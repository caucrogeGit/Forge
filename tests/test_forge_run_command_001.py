"""Tests — FORGE-RUN-COMMAND-001.

Verrouille le contrat de la commande `forge run` :

  - point d'entrée unique pour lancer Forge ;
  - APP_ENV=dev  → délègue au mécanisme de démarrage existant ;
  - APP_ENV=prod → refuse le serveur intégré et imprime la stratégie
                   WSGI recommandée (jamais `python app.py`).

Hors périmètre (tickets suivants) :
  - autoreload ;
  - lancement automatique de Gunicorn.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

import forge
from cli.project import run as run_module


_REPO_ROOT = Path(__file__).resolve().parents[1]


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_project(tmp_path: Path) -> Path:
    """Crée un faux projet Forge minimal : app.py + mvc/."""
    (tmp_path / "app.py").write_text("# stub\n", encoding="utf-8")
    (tmp_path / "mvc").mkdir()
    return tmp_path


# ── Module : cli/project/run.py ────────────────────────────────────────────────


class TestRunModuleExists:
    """Le module cli/project/run.py existe et expose `main`."""

    def test_module_present(self):
        path = _REPO_ROOT / "cli" / "run.py"
        assert path.exists(), "cli/project/run.py doit exister (FORGE-RUN-COMMAND-001)"

    def test_main_callable(self):
        assert callable(run_module.main)


# ── Dispatcher forge.py ──────────────────────────────────────────────────────


class TestDispatchRun:
    """`forge run` est dispatché vers cli/project/run.py."""

    def test_dispatch_run_appelle_run_main(self, monkeypatch):
        captured: dict[str, list[str]] = {}

        def fake_run_main(args: list[str]) -> None:
            captured["args"] = list(args)

        monkeypatch.setattr(sys, "argv", ["forge", "run"])
        monkeypatch.setattr(forge, "run_main", fake_run_main)
        forge.main()
        assert captured["args"] == []

    def test_dispatch_run_transmet_env_dev(self, monkeypatch):
        captured: dict[str, list[str]] = {}

        def fake_run_main(args: list[str]) -> None:
            captured["args"] = list(args)

        monkeypatch.setattr(sys, "argv", ["forge", "run", "--env", "dev"])
        monkeypatch.setattr(forge, "run_main", fake_run_main)
        forge.main()
        assert captured["args"] == ["--env", "dev"]

    def test_dispatch_run_transmet_env_prod(self, monkeypatch):
        captured: dict[str, list[str]] = {}

        def fake_run_main(args: list[str]) -> None:
            captured["args"] = list(args)

        monkeypatch.setattr(sys, "argv", ["forge", "run", "--env", "prod"])
        monkeypatch.setattr(forge, "run_main", fake_run_main)
        forge.main()
        assert captured["args"] == ["--env", "prod"]


# ── Parsing de l'environnement ───────────────────────────────────────────────


class TestParseEnv:
    """Priorité : --env > APP_ENV > défaut 'dev'."""

    def test_defaut_dev_si_rien(self, monkeypatch):
        monkeypatch.delenv("APP_ENV", raising=False)
        assert run_module._parse_env([]) == "dev"

    def test_lit_app_env(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "prod")
        assert run_module._parse_env([]) == "prod"

    def test_flag_env_dev_prime(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "prod")
        assert run_module._parse_env(["--env", "dev"]) == "dev"

    def test_flag_env_prod_prime(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "dev")
        assert run_module._parse_env(["--env", "prod"]) == "prod"

    def test_env_inconnu_refus(self, monkeypatch):
        monkeypatch.delenv("APP_ENV", raising=False)
        with pytest.raises(SystemExit):
            run_module._parse_env(["--env", "staging"])

    def test_env_sans_valeur_refus(self, monkeypatch):
        monkeypatch.delenv("APP_ENV", raising=False)
        with pytest.raises(SystemExit):
            run_module._parse_env(["--env"])


# ── Garde projet Forge ───────────────────────────────────────────────────────


class TestProjectGuard:
    """`forge run` doit être lancé depuis un projet Forge."""

    def test_refuse_si_pas_de_app_py(self, tmp_path, monkeypatch, capsys):
        (tmp_path / "mvc").mkdir()
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("APP_ENV", raising=False)
        with pytest.raises(SystemExit):
            run_module.cmd_run([])
        err = capsys.readouterr().err
        assert "app.py" in err

    def test_refuse_si_pas_de_mvc(self, tmp_path, monkeypatch, capsys):
        (tmp_path / "app.py").write_text("# stub\n", encoding="utf-8")
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("APP_ENV", raising=False)
        with pytest.raises(SystemExit):
            run_module.cmd_run([])
        err = capsys.readouterr().err
        assert "mvc" in err


# ── Comportement prod : refus du serveur intégré ─────────────────────────────


class TestProdRefusal:
    """APP_ENV=prod → refus + message WSGI clair, jamais `python app.py`."""

    def test_message_mentionne_wsgi_gunicorn(self):
        msg = run_module._format_prod_refusal()
        assert "WSGI" in msg
        assert "gunicorn" in msg.lower()

    def test_message_ne_recommande_pas_python_app_py(self):
        msg = run_module._format_prod_refusal()
        assert "python app.py" not in msg.lower()

    def test_message_mentionne_reverse_proxy(self):
        msg = run_module._format_prod_refusal()
        assert "reverse proxy" in msg.lower() or "nginx" in msg.lower() or "caddy" in msg.lower()

    def test_message_cite_create_configured_wsgi_app(self):
        msg = run_module._format_prod_refusal()
        assert "create_configured_wsgi_app" in msg

    def test_prod_exit_non_zero(self, tmp_path, monkeypatch, capsys):
        _make_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("APP_ENV", "prod")
        with pytest.raises(SystemExit) as exc_info:
            run_module.cmd_run([])
        assert exc_info.value.code != 0
        err = capsys.readouterr().err
        assert "WSGI" in err
        assert "python app.py" not in err.lower()

    def test_prod_via_flag_refuse(self, tmp_path, monkeypatch, capsys):
        _make_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("APP_ENV", raising=False)
        with pytest.raises(SystemExit) as exc_info:
            run_module.cmd_run(["--env", "prod"])
        assert exc_info.value.code != 0
        err = capsys.readouterr().err
        assert "WSGI" in err


# ── Comportement dev legacy (--no-reload) ────────────────────────────────────
#
# Le chemin par défaut en dev passe désormais par le superviseur d'autoreload
# (`cli.project.dev_reloader`, ticket DEV-SERVER-AUTORELOAD-001). Ces tests
# couvrent la branche `--no-reload` qui conserve l'ancien comportement :
# délégation à `scripts/dev-server.sh` (POSIX) ou fallback `python app.py`.


class TestDevDelegationLegacy:
    """`forge run --no-reload` retombe sur dev-server.sh ou python app.py."""

    def test_dev_lance_dev_server_sh_si_present(self, tmp_path, monkeypatch):
        _make_project(tmp_path)
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "dev-server.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("APP_ENV", "dev")
        monkeypatch.setattr(os, "name", "posix")

        captured: dict[str, list[str]] = {}

        def fake_run(cmd, cwd=None):  # noqa: ANN001
            captured["cmd"] = list(cmd)
            captured["cwd"] = cwd

            class _R:
                returncode = 0

            return _R()

        monkeypatch.setattr(subprocess, "run", fake_run)
        run_module.cmd_run(["--no-reload"])
        # Le script dev-server.sh figure dans la commande exécutée.
        assert any("dev-server.sh" in part for part in captured["cmd"]), captured

    def test_dev_fallback_python_app_py_si_pas_de_script(self, tmp_path, monkeypatch):
        _make_project(tmp_path)
        # Pas de scripts/dev-server.sh.
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("APP_ENV", "dev")

        captured: dict[str, list[str]] = {}

        def fake_run(cmd, cwd=None):  # noqa: ANN001
            captured["cmd"] = list(cmd)

            class _R:
                returncode = 0

            return _R()

        monkeypatch.setattr(subprocess, "run", fake_run)
        run_module.cmd_run(["--no-reload"])
        assert sys.executable in captured["cmd"]
        assert any(part.endswith("app.py") for part in captured["cmd"]), captured

    def test_dev_propage_code_retour_non_zero(self, tmp_path, monkeypatch):
        _make_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("APP_ENV", "dev")

        def fake_run(cmd, cwd=None):  # noqa: ANN001
            class _R:
                returncode = 7

            return _R()

        monkeypatch.setattr(subprocess, "run", fake_run)
        with pytest.raises(SystemExit) as exc_info:
            run_module.cmd_run(["--no-reload"])
        assert exc_info.value.code == 7


# ── Aide centrale --help ─────────────────────────────────────────────────────


class TestRunHelp:
    """`forge run --help` retourne 0 et imprime l'aide sans exécuter."""

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(_REPO_ROOT / "forge.py"), *args],
            capture_output=True,
            text=True,
            timeout=15,
        )

    def test_run_help_exit_zero(self):
        result = self._run("run", "--help")
        assert result.returncode == 0, result.stderr

    def test_run_h_exit_zero(self):
        result = self._run("run", "-h")
        assert result.returncode == 0, result.stderr

    def test_run_help_decrit_dev_et_prod(self):
        result = self._run("run", "--help")
        out = result.stdout
        assert "dev" in out
        assert "prod" in out
        assert "WSGI" in out

    def test_run_help_apparait_dans_help_general(self):
        result = self._run("help")
        assert "run" in result.stdout


# ── Présence dans help.py ────────────────────────────────────────────────────


class TestHelpTextMentionsRun:
    def test_build_help_contient_run(self):
        from cli._support.help import build_help

        text = build_help("1.0.0")
        assert " run " in text or "\nrun\n" in text or "run " in text
