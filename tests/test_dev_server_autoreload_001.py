"""Tests — DEV-SERVER-AUTORELOAD-001.

Verrouille le contrat du superviseur `cli.project.dev_reloader` :

  - détecte les modifications des fichiers pertinents (app.py, config.py,
    env/dev, mvc/**, core/**) ;
  - ignore les dossiers volumineux ou générés
    (.venv, __pycache__, storage, logs, site, node_modules, .git, ...) ;
  - terminate + wait + respawn le subprocess applicatif à chaque
    changement détecté ;
  - `forge run` (dev) active l'autoreload par défaut ;
  - `forge run --no-reload` retombe sur le mécanisme legacy
    (`scripts/dev-server.sh` ou `python app.py`) ;
  - `forge run` (prod) ne lance jamais l'autoreload.

Aucun vrai subprocess HTTP n'est lancé : les tests injectent un faux
spawn_fn et vérifient les appels.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from cli.project import dev_reloader, run as run_module
from cli.project.dev_reloader import (
    DevReloader,
    DIRECTORIES_TO_WATCH,
    IGNORED_DIR_NAMES,
    ROOT_FILES_TO_WATCH,
    diff_snapshots,
    is_ignored_path,
    iter_watched_files,
    snapshot,
)


_REPO_ROOT = Path(__file__).resolve().parents[1]


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_project(tmp_path: Path) -> Path:
    """Squelette de projet Forge utilisable par le superviseur :

        app.py, config.py, env/dev, mvc/, core/.
    """
    (tmp_path / "app.py").write_text("# stub\n", encoding="utf-8")
    (tmp_path / "config.py").write_text("# stub\n", encoding="utf-8")
    (tmp_path / "env").mkdir()
    (tmp_path / "env" / "dev").write_text("APP_ENV=dev\n", encoding="utf-8")

    mvc = tmp_path / "mvc"
    (mvc / "controllers").mkdir(parents=True)
    (mvc / "controllers" / "home_controller.py").write_text("# stub\n", encoding="utf-8")
    (mvc / "views").mkdir()
    (mvc / "views" / "home.html").write_text("<html></html>", encoding="utf-8")
    (mvc / "entities").mkdir()
    (mvc / "entities" / "contact.json").write_text("{}", encoding="utf-8")
    (mvc / "migrations").mkdir()
    (mvc / "migrations" / "001_init.sql").write_text("-- noop", encoding="utf-8")
    (mvc / "routes.py").write_text("# stub\n", encoding="utf-8")

    core_app = tmp_path / "core" / "app"
    core_app.mkdir(parents=True)
    (core_app / "application.py").write_text("# stub\n", encoding="utf-8")

    # Dossiers ignorés (peuplés pour vérifier que le watcher les saute).
    for ignored in (".venv", "__pycache__", "storage", "logs", "node_modules", ".git"):
        (tmp_path / ignored).mkdir()
        (tmp_path / ignored / "noise.py").write_text("# noise\n", encoding="utf-8")

    return tmp_path


class FakeProcess:
    """Subprocess simulé : suit terminate/wait/kill/poll sans système."""

    def __init__(self, pid: int = 1234) -> None:
        self.pid = pid
        self.alive = True
        self.returncode: int | None = None
        self.terminate_calls = 0
        self.wait_calls = 0
        self.kill_calls = 0
        self.wait_raises: BaseException | None = None

    def poll(self) -> int | None:
        return None if self.alive else self.returncode

    def terminate(self) -> None:
        self.terminate_calls += 1
        if self.wait_raises is None:
            self.alive = False
            self.returncode = 0

    def kill(self) -> None:
        self.kill_calls += 1
        self.alive = False
        self.returncode = -9

    def wait(self, timeout: float | None = None) -> int | None:
        self.wait_calls += 1
        if self.wait_raises is not None:
            exc = self.wait_raises
            self.wait_raises = None  # un seul tir, puis terminate normal
            raise exc
        return self.returncode


def _touch(path: Path, *, bump: float = 2.0) -> None:
    """Modifie le mtime de `path` pour forcer une détection de changement."""
    path.touch()
    new_mtime = time.time() + bump
    os.utime(path, (new_mtime, new_mtime))


# ── 1. Détection des changements ─────────────────────────────────────────────


class TestDetection:
    """Le snapshot détecte les modifications des fichiers pertinents."""

    @pytest.mark.parametrize("relative", [
        "mvc/controllers/home_controller.py",
        "mvc/routes.py",
        "mvc/views/home.html",
        "mvc/entities/contact.json",
        "mvc/migrations/001_init.sql",
        "app.py",
        "config.py",
        "env/dev",
        "core/app/application.py",
    ])
    def test_detecte_modification(self, tmp_path, relative):
        root = _make_project(tmp_path)
        before = snapshot(root)
        _touch(root / relative)
        after = snapshot(root)
        changes = diff_snapshots(before, after)
        assert str(root / relative) in changes, (
            f"Modification de {relative} non détectée. Changes={changes}"
        )

    def test_detecte_ajout_de_fichier(self, tmp_path):
        root = _make_project(tmp_path)
        before = snapshot(root)
        new = root / "mvc" / "controllers" / "new_controller.py"
        new.write_text("# new\n", encoding="utf-8")
        after = snapshot(root)
        changes = diff_snapshots(before, after)
        assert str(new) in changes

    def test_detecte_suppression_de_fichier(self, tmp_path):
        root = _make_project(tmp_path)
        target = root / "mvc" / "controllers" / "home_controller.py"
        before = snapshot(root)
        target.unlink()
        after = snapshot(root)
        changes = diff_snapshots(before, after)
        assert str(target) in changes

    def test_aucun_changement_si_aucun_touch(self, tmp_path):
        root = _make_project(tmp_path)
        before = snapshot(root)
        after = snapshot(root)
        assert diff_snapshots(before, after) == []


# ── 2. Dossiers ignorés ──────────────────────────────────────────────────────


class TestIgnoredDirectories:
    """Les dossiers ignorés ne génèrent jamais de reload."""

    @pytest.mark.parametrize("ignored", [
        ".venv", "__pycache__", "storage", "logs",
        "node_modules", ".git", ".pytest_cache",
        ".ruff_cache", ".mypy_cache", "site", "build", "dist",
    ])
    def test_dossier_ignore_dans_constantes(self, ignored):
        assert ignored in IGNORED_DIR_NAMES

    @pytest.mark.parametrize("ignored", [
        ".venv", "__pycache__", "storage", "logs",
        "node_modules", ".git",
    ])
    def test_modification_dans_dossier_ignore_non_detectee(self, tmp_path, ignored):
        root = _make_project(tmp_path)
        target = root / ignored / "noise.py"
        before = snapshot(root)
        _touch(target)
        after = snapshot(root)
        assert diff_snapshots(before, after) == [], (
            f"Le watcher ne doit PAS réagir à {ignored}/noise.py. "
            f"Changes={diff_snapshots(before, after)}"
        )

    def test_is_ignored_path_reconnait_chaque_marqueur(self, tmp_path):
        root = _make_project(tmp_path)
        for ignored in IGNORED_DIR_NAMES:
            sample = root / ignored / "foo.py"
            assert is_ignored_path(sample, root), (
                f"{ignored} doit être ignoré par is_ignored_path."
            )

    def test_is_ignored_path_refuse_un_fichier_hors_arbre(self, tmp_path):
        root = _make_project(tmp_path)
        outside = Path("/etc/passwd")
        assert is_ignored_path(outside, root)


# ── 3. Périmètre des fichiers surveillés ─────────────────────────────────────


class TestWatchedScope:
    """iter_watched_files inclut les bons fichiers et exclut les autres."""

    def test_inclut_les_fichiers_racine(self, tmp_path):
        root = _make_project(tmp_path)
        paths = {str(p) for p in iter_watched_files(root)}
        for name in ROOT_FILES_TO_WATCH:
            target = str(root / name)
            assert target in paths, f"{name} doit être surveillé."

    def test_inclut_mvc_py_html_json_sql(self, tmp_path):
        root = _make_project(tmp_path)
        paths = {str(p) for p in iter_watched_files(root)}
        assert str(root / "mvc" / "routes.py") in paths
        assert str(root / "mvc" / "views" / "home.html") in paths
        assert str(root / "mvc" / "entities" / "contact.json") in paths
        assert str(root / "mvc" / "migrations" / "001_init.sql") in paths

    def test_exclut_fichiers_inconnus_dans_mvc(self, tmp_path):
        root = _make_project(tmp_path)
        binaries = root / "mvc" / "data.bin"
        binaries.write_text("noise", encoding="utf-8")
        paths = {str(p) for p in iter_watched_files(root)}
        assert str(binaries) not in paths, (
            "Une extension non surveillée (.bin) ne doit pas figurer."
        )

    def test_inclut_core_py(self, tmp_path):
        root = _make_project(tmp_path)
        paths = {str(p) for p in iter_watched_files(root)}
        assert str(root / "core" / "app" / "application.py") in paths

    def test_directories_to_watch_couvre_mvc_et_core(self):
        watched = {rel for rel, _ in DIRECTORIES_TO_WATCH}
        assert "mvc" in watched
        assert "core" in watched

    def test_root_files_to_watch_couvre_app_config_env(self):
        assert "app.py" in ROOT_FILES_TO_WATCH
        assert "config.py" in ROOT_FILES_TO_WATCH
        assert "env/dev" in ROOT_FILES_TO_WATCH


# ── 4. Superviseur : terminate / wait / respawn ──────────────────────────────


class TestSupervisorLifecycle:
    """DevReloader appelle terminate/wait puis respawn à chaque changement."""

    def _make_reloader(self, root: Path) -> tuple[DevReloader, list[FakeProcess], list[str]]:
        spawned: list[FakeProcess] = []
        logs: list[str] = []

        def spawn() -> FakeProcess:
            proc = FakeProcess(pid=1000 + len(spawned))
            spawned.append(proc)
            return proc

        def log(message: str) -> None:
            logs.append(message)

        reloader = DevReloader(
            root,
            poll_interval=0.0,
            spawn_fn=spawn,
            log_fn=log,
        )
        return reloader, spawned, logs

    def test_start_spawne_un_subprocess(self, tmp_path):
        root = _make_project(tmp_path)
        reloader, spawned, _ = self._make_reloader(root)
        reloader.start()
        assert len(spawned) == 1
        assert reloader.process is spawned[0]

    def test_stop_termine_et_attend(self, tmp_path):
        root = _make_project(tmp_path)
        reloader, spawned, _ = self._make_reloader(root)
        reloader.start()
        reloader.stop()
        proc = spawned[0]
        assert proc.terminate_calls == 1
        assert proc.wait_calls == 1
        assert proc.kill_calls == 0
        assert not proc.alive

    def test_stop_idempotent(self, tmp_path):
        root = _make_project(tmp_path)
        reloader, spawned, _ = self._make_reloader(root)
        reloader.start()
        reloader.stop()
        reloader.stop()  # ne doit pas relancer terminate sur un mort
        assert spawned[0].terminate_calls == 1

    def test_stop_force_kill_si_wait_timeout(self, tmp_path):
        root = _make_project(tmp_path)
        reloader, spawned, _ = self._make_reloader(root)
        reloader.start()
        proc = spawned[0]
        proc.wait_raises = subprocess.TimeoutExpired(cmd="x", timeout=1)
        # terminate() ne tue plus le faux process si wait_raises est posé
        proc.alive = True  # forcer le scénario "ne se termine pas"
        # On simule : terminate() est appelé, wait() lève → fallback kill().
        # Notre FakeProcess.terminate() arme « alive=False » ; pour le test,
        # on doit annuler ce side-effect APRÈS terminate() pour reproduire
        # un processus qui ignore SIGTERM.
        original_terminate = proc.terminate

        def stubborn_terminate() -> None:
            proc.terminate_calls += 1  # incrémenté manuellement ici
            # PAS d'alive=False : le process ignore SIGTERM.

        proc.terminate = stubborn_terminate  # type: ignore[method-assign]
        reloader.stop(timeout=0.01)
        del original_terminate
        assert proc.kill_calls == 1, "kill() doit être appelé en secours."

    def test_restart_termine_puis_respawne(self, tmp_path):
        root = _make_project(tmp_path)
        reloader, spawned, _ = self._make_reloader(root)
        reloader.start()
        reloader.restart("mvc/routes.py")
        assert len(spawned) == 2
        assert spawned[0].terminate_calls == 1
        assert spawned[0].wait_calls == 1
        assert reloader.process is spawned[1]

    def test_restart_log_changement_et_relance(self, tmp_path):
        root = _make_project(tmp_path)
        reloader, _, logs = self._make_reloader(root)
        reloader.start()
        reloader.restart("mvc/routes.py")
        joined = "\n".join(logs)
        assert "Changement détecté" in joined
        assert "Redémarrage" in joined
        assert "Serveur relancé" in joined


# ── 5. Boucle run() : intégration ────────────────────────────────────────────


def _ki_after(n):
    """`sleep` factice qui lève KeyboardInterrupt au n-ième appel.

    Sert à borner la boucle `run()` dans les tests : depuis
    DEV-SERVER-CRASH-RESILIENCE-001, `run()` ne s'arrête plus à la mort du
    subprocess (il relance) — seul Ctrl+C (KeyboardInterrupt) la termine.
    """
    state = {"calls": 0}

    def _sleep(_delay):
        state["calls"] += 1
        if state["calls"] >= n:
            raise KeyboardInterrupt

    return _sleep


class TestRunLoop:
    """`DevReloader.run()` relance le serveur et se termine proprement sur Ctrl+C."""

    def test_run_respawne_si_subprocess_meurt(self, tmp_path):
        # DEV-SERVER-CRASH-RESILIENCE-001 — un crash ne stoppe plus forge run :
        # le superviseur relance, et ne propage pas le code de crash.
        root = _make_project(tmp_path)
        spawned: list[FakeProcess] = []

        def spawn() -> FakeProcess:
            proc = FakeProcess()
            spawned.append(proc)
            proc.alive = False  # meurt aussitôt (crash)
            proc.returncode = 42
            return proc

        reloader = DevReloader(
            root,
            poll_interval=0.0,
            spawn_fn=spawn,
            log_fn=lambda _msg: None,
            sleep_fn=_ki_after(2),
            respawn_backoff=0.0,
        )
        code = reloader.run()
        assert code == 0, "run() ne s'arrête que sur Ctrl+C, pas sur un crash."
        assert len(spawned) >= 2, "Le serveur mort doit être relancé."

    def test_run_redemarre_sur_changement_puis_arret(self, tmp_path):
        root = _make_project(tmp_path)
        spawned: list[FakeProcess] = []
        snap_iter = iter([{"a": 1.0}, {"a": 2.0}])  # initial, puis change

        def spawn() -> FakeProcess:
            proc = FakeProcess()
            proc.alive = True  # vit (pas de crash)
            spawned.append(proc)
            return proc

        def fake_snapshot(_root: Path) -> dict[str, float]:
            try:
                return next(snap_iter)
            except StopIteration:
                return {"a": 2.0}

        reloader = DevReloader(
            root,
            poll_interval=0.0,
            spawn_fn=spawn,
            log_fn=lambda _msg: None,
            snapshot_fn=fake_snapshot,
            sleep_fn=_ki_after(2),
        )
        code = reloader.run()
        assert code == 0
        assert len(spawned) == 2, "Un changement détecté → respawn attendu."
        assert spawned[0].terminate_calls == 1
        assert spawned[0].wait_calls == 1

    def test_run_logue_demarrage_et_surveillance(self, tmp_path):
        root = _make_project(tmp_path)
        logs: list[str] = []

        def spawn() -> FakeProcess:
            proc = FakeProcess()
            proc.alive = True
            return proc

        reloader = DevReloader(
            root,
            poll_interval=0.0,
            spawn_fn=spawn,
            log_fn=logs.append,
            sleep_fn=_ki_after(1),
        )
        reloader.run()
        joined = "\n".join(logs)
        assert "Serveur Forge démarré" in joined
        assert "Surveillance active" in joined

    def test_run_cesse_le_respawn_apres_crashes_repetes(self, tmp_path):
        # Garde anti-boucle : après max_fast_crashes crashes rapides, on
        # cesse de respawner et on attend une modification de fichier.
        root = _make_project(tmp_path)
        spawned: list[FakeProcess] = []
        logs: list[str] = []

        def spawn() -> FakeProcess:
            proc = FakeProcess()
            proc.alive = False  # crash immédiat à chaque tentative
            proc.returncode = 1
            spawned.append(proc)
            return proc

        reloader = DevReloader(
            root,
            poll_interval=0.0,
            spawn_fn=spawn,
            log_fn=logs.append,
            sleep_fn=_ki_after(10),
            respawn_backoff=0.0,
            max_fast_crashes=3,
        )
        reloader.run()
        # 1 démarrage initial + 3 relances ; le 4e crash déclenche le garde.
        assert len(spawned) == 1 + 3
        assert any("Échecs répétés" in m for m in logs)

    def test_run_relance_apres_garde_sur_modification(self, tmp_path):
        # Après être passé en attente (crashes répétés), une modification de
        # fichier relance proprement le serveur.
        root = _make_project(tmp_path)
        spawned: list[FakeProcess] = []
        logs: list[str] = []
        calls = {"n": 0}

        def spawn() -> FakeProcess:
            proc = FakeProcess()
            proc.alive = False
            proc.returncode = 1
            spawned.append(proc)
            return proc

        def fake_snapshot(_root: Path) -> dict[str, float]:
            calls["n"] += 1
            # Inchangé pendant les crashes, puis changement au 6e appel.
            return {"a": 1.0} if calls["n"] <= 5 else {"a": 2.0}

        reloader = DevReloader(
            root,
            poll_interval=0.0,
            spawn_fn=spawn,
            log_fn=logs.append,
            snapshot_fn=fake_snapshot,
            sleep_fn=_ki_after(6),
            respawn_backoff=0.0,
            max_fast_crashes=2,
        )
        reloader.run()
        assert any("Échecs répétés" in m for m in logs)
        assert any("Changement détecté" in m for m in logs), (
            "Une modification après le garde doit relancer le serveur."
        )


# ── 6. Intégration `forge run` ───────────────────────────────────────────────


class TestForgeRunIntegration:
    """`forge run` choisit la bonne branche selon --no-reload et APP_ENV."""

    def _bootstrap(self, tmp_path: Path, monkeypatch) -> Path:
        root = _make_project(tmp_path)
        monkeypatch.chdir(root)
        monkeypatch.delenv("APP_ENV", raising=False)
        return root

    def test_dev_active_le_reloader_par_defaut(self, tmp_path, monkeypatch):
        self._bootstrap(tmp_path, monkeypatch)
        called: dict[str, bool] = {"reloader": False, "legacy": False}

        monkeypatch.setattr(run_module, "_run_dev_with_reloader",
                            lambda _root: (called.__setitem__("reloader", True) or 0))
        monkeypatch.setattr(run_module, "_run_dev_legacy",
                            lambda _root: (called.__setitem__("legacy", True) or 0))
        run_module.cmd_run([])
        assert called["reloader"] is True
        assert called["legacy"] is False

    def test_no_reload_utilise_le_chemin_legacy(self, tmp_path, monkeypatch):
        self._bootstrap(tmp_path, monkeypatch)
        called: dict[str, bool] = {"reloader": False, "legacy": False}

        monkeypatch.setattr(run_module, "_run_dev_with_reloader",
                            lambda _root: (called.__setitem__("reloader", True) or 0))
        monkeypatch.setattr(run_module, "_run_dev_legacy",
                            lambda _root: (called.__setitem__("legacy", True) or 0))
        run_module.cmd_run(["--no-reload"])
        assert called["legacy"] is True
        assert called["reloader"] is False

    def test_parse_reload_defaut(self):
        assert run_module._parse_reload([]) is True

    def test_parse_reload_no_reload(self):
        assert run_module._parse_reload(["--no-reload"]) is False

    def test_parse_reload_no_reload_avec_autres_args(self):
        assert run_module._parse_reload(["--env", "dev", "--no-reload"]) is False

    def test_prod_n_active_jamais_l_autoreload(self, tmp_path, monkeypatch, capsys):
        root = _make_project(tmp_path)
        monkeypatch.chdir(root)
        monkeypatch.delenv("APP_ENV", raising=False)
        called: dict[str, bool] = {"reloader": False, "legacy": False}

        monkeypatch.setattr(run_module, "_run_dev_with_reloader",
                            lambda _root: (called.__setitem__("reloader", True) or 0))
        monkeypatch.setattr(run_module, "_run_dev_legacy",
                            lambda _root: (called.__setitem__("legacy", True) or 0))
        with pytest.raises(SystemExit) as exc_info:
            run_module.cmd_run(["--env", "prod"])
        assert exc_info.value.code != 0
        err = capsys.readouterr().err
        assert "WSGI" in err
        # Aucune des deux branches dev ne doit avoir été appelée :
        assert called["reloader"] is False
        assert called["legacy"] is False
        # Et bien sûr, jamais `python app.py` recommandé en prod.
        assert "python app.py" not in err.lower()

    def test_legacy_avec_dev_server_sh(self, tmp_path, monkeypatch):
        root = _make_project(tmp_path)
        scripts_dir = root / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "dev-server.sh").write_text(
            "#!/usr/bin/env bash\n", encoding="utf-8"
        )
        monkeypatch.chdir(root)
        monkeypatch.setattr(os, "name", "posix")

        captured: dict[str, list[str]] = {}

        def fake_run(cmd, cwd=None):  # noqa: ANN001
            captured["cmd"] = list(cmd)

            class _R:
                returncode = 0

            return _R()

        monkeypatch.setattr(subprocess, "run", fake_run)
        run_module._run_dev_legacy(root)
        assert any("dev-server.sh" in part for part in captured["cmd"])

    def test_legacy_fallback_python_app_py(self, tmp_path, monkeypatch):
        root = _make_project(tmp_path)
        monkeypatch.chdir(root)

        captured: dict[str, list[str]] = {}

        def fake_run(cmd, cwd=None):  # noqa: ANN001
            captured["cmd"] = list(cmd)

            class _R:
                returncode = 0

            return _R()

        monkeypatch.setattr(subprocess, "run", fake_run)
        run_module._run_dev_legacy(root)
        assert sys.executable in captured["cmd"]
        assert any(part.endswith("app.py") for part in captured["cmd"])


# ── 7. Module / aide ─────────────────────────────────────────────────────────


class TestModulePresence:
    def test_module_existe(self):
        assert (_REPO_ROOT / "cli" / "project" / "dev_reloader.py").exists()

    def test_log_prefix_est_dev_reload(self):
        assert dev_reloader.LOG_PREFIX == "[DEV-RELOAD]"


class TestHelpMentionsNoReload:
    """`forge run --help` mentionne --no-reload et l'autoreload."""

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(_REPO_ROOT / "forge.py"), *args],
            capture_output=True,
            text=True,
            timeout=15,
        )

    def test_help_mentionne_no_reload(self):
        result = self._run("run", "--help")
        assert result.returncode == 0
        assert "--no-reload" in result.stdout

    def test_help_mentionne_autoreload(self):
        result = self._run("run", "--help")
        out = result.stdout.lower()
        assert "autoreload" in out or "redémarre" in out or "reload" in out
