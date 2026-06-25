# pyright: strict
"""Superviseur de développement Forge avec autoreload par redémarrage de processus.

Tickets :
    DEV-SERVER-AUTORELOAD-001       — autoreload sur changement de fichier.
    DEV-SERVER-CRASH-RESILIENCE-001 — `forge run` survit aux crashes de l'app.

Architecture :
    forge run (APP_ENV=dev)
        → DevReloader.run()
            → spawn `python app.py` (subprocess)
            → boucle de polling stat() sur les fichiers surveillés
            → si changement détecté :
                → terminate(subprocess) + wait
                → respawn
            → si le subprocess meurt (crash, erreur fatale) :
                → relance automatique ; après plusieurs crashes rapides,
                  attend une modification de fichier (pas de boucle de crash).
                  `forge run` ne s'arrête que sur Ctrl+C — une erreur ne tue
                  jamais le serveur de dév.

Volontairement simple :
    - polling stat() (pas d'inotify, pas de watchfiles, pas de watchdog) ;
    - redémarrage de processus (jamais importlib.reload) ;
    - stdlib uniquement : subprocess, time, pathlib, os, sys, signal.

Le superviseur vit dans cli/ — il ne touche ni le routeur HTTP,
ni core/http, ni le chemin WSGI.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable, Iterable


LOG_PREFIX = "[DEV-RELOAD]"


# Fichiers individuels surveillés à la racine du projet (chemins relatifs).
ROOT_FILES_TO_WATCH: tuple[str, ...] = (
    "app.py",
    "config.py",
    "env/dev",
)


# Répertoires surveillés récursivement + extensions retenues (avec point).
DIRECTORIES_TO_WATCH: tuple[tuple[str, frozenset[str]], ...] = (
    ("mvc", frozenset({".py", ".html", ".json", ".sql"})),
    ("core", frozenset({".py"})),
)


# Composants de chemin systématiquement ignorés (premier match gagne).
IGNORED_DIR_NAMES: frozenset[str] = frozenset({
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "storage",
    "logs",
    "site",
    "node_modules",
    ".git",
    "build",
    "dist",
})


def is_ignored_path(path: Path, root: Path) -> bool:
    """True si `path` traverse un répertoire ignoré (relatif à `root`).

    Hors-arbre (`path` non sous `root`) est considéré comme ignoré : le
    superviseur ne s'intéresse qu'au projet courant.
    """
    try:
        rel = path.resolve().relative_to(root.resolve())
    except ValueError:
        return True
    return any(part in IGNORED_DIR_NAMES for part in rel.parts)


def iter_watched_files(root: Path) -> Iterable[Path]:
    """Itère sur les fichiers surveillés à un instant t.

    Combine :
      - les fichiers racines listés dans ROOT_FILES_TO_WATCH ;
      - tous les fichiers de DIRECTORIES_TO_WATCH dont l'extension
        figure dans le set associé, en excluant IGNORED_DIR_NAMES.
    """
    for name in ROOT_FILES_TO_WATCH:
        path = root / name
        if path.is_file():
            yield path

    for rel_dir, exts in DIRECTORIES_TO_WATCH:
        base = root / rel_dir
        if not base.is_dir():
            continue
        for entry in base.rglob("*"):
            if is_ignored_path(entry, root):
                continue
            if not entry.is_file():
                continue
            if entry.suffix in exts:
                yield entry


def snapshot(root: Path) -> dict[str, float]:
    """État courant des mtimes des fichiers surveillés ({chemin str: mtime})."""
    snap: dict[str, float] = {}
    for path in iter_watched_files(root):
        try:
            snap[str(path)] = path.stat().st_mtime
        except OSError:
            # Fichier supprimé entre rglob et stat — on l'ignore.
            continue
    return snap


def diff_snapshots(before: dict[str, float], after: dict[str, float]) -> list[str]:
    """Liste triée des chemins modifiés, ajoutés ou supprimés."""
    changed: set[str] = set()
    for path, mtime in after.items():
        if before.get(path) != mtime:
            changed.add(path)
    for path in before:
        if path not in after:
            changed.add(path)
    return sorted(changed)


# ── Superviseur ──────────────────────────────────────────────────────────────


class DevReloader:
    """Boucle : spawn → watch → terminate → respawn.

    Les hooks `spawn_fn` et `log_fn` sont injectables pour les tests :
    aucun vrai subprocess HTTP n'est nécessaire pour vérifier le contrat.
    """

    def __init__(
        self,
        root: Path,
        *,
        poll_interval: float = 0.5,
        cmd: list[str] | None = None,
        env: dict[str, str] | None = None,
        log_fn: Callable[[str], None] | None = None,
        spawn_fn: Callable[[], "subprocess.Popen[bytes]"] | None = None,
        snapshot_fn: Callable[[Path], dict[str, float]] | None = None,
        sleep_fn: Callable[[float], None] | None = None,
        healthy_uptime: float = 3.0,
        max_fast_crashes: int = 3,
        respawn_backoff: float = 1.0,
    ) -> None:
        self.root = root
        self.poll_interval = poll_interval
        self.cmd = cmd or [sys.executable, str(root / "app.py")]
        self.env = dict(env) if env is not None else os.environ.copy()
        self.log: Callable[[str], None] = log_fn or self._default_log
        self._spawn: Callable[[], "subprocess.Popen[bytes]"] = (
            spawn_fn or self._default_spawn
        )
        self._snapshot: Callable[[Path], dict[str, float]] = snapshot_fn or snapshot
        self._sleep: Callable[[float], None] = sleep_fn or time.sleep
        # Résilience aux crashes (DEV-SERVER-CRASH-RESILIENCE-001) :
        #   - healthy_uptime   : durée (s) au-delà de laquelle un processus est
        #     « sain » ; en deçà, sa mort compte comme crash rapide ;
        #   - max_fast_crashes : nb de crashes rapides consécutifs tolérés avant
        #     d'arrêter le respawn auto et d'attendre une modification ;
        #   - respawn_backoff  : pause (s) avant un respawn après crash rapide.
        self.healthy_uptime = healthy_uptime
        self.max_fast_crashes = max_fast_crashes
        self.respawn_backoff = respawn_backoff
        self._spawn_time: float = 0.0
        self.process: "subprocess.Popen[bytes] | None" = None

    @staticmethod
    def _default_log(message: str) -> None:
        print(f"{LOG_PREFIX} {message}", flush=True)

    def _default_spawn(self) -> "subprocess.Popen[bytes]":
        return subprocess.Popen(self.cmd, cwd=str(self.root), env=self.env)

    # ── Cycle de vie du subprocess ──────────────────────────────────────────

    def start(self) -> None:
        """Spawn le subprocess applicatif."""
        self.process = self._spawn()
        self._spawn_time = time.monotonic()

    def stop(self, timeout: float = 5.0) -> None:
        """Arrête le subprocess actif : SIGTERM (terminate), puis kill en
        secours si le processus n'a pas fini dans `timeout`.

        Idempotent : si le processus est déjà mort, ne fait rien.
        """
        proc = self.process
        if proc is None or proc.poll() is not None:
            return
        proc.terminate()
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            try:
                proc.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                pass

    def restart(self, reason: str) -> None:
        """Redémarre proprement le subprocess applicatif."""
        self.log(f"Changement détecté : {reason}")
        self.log("Redémarrage du serveur...")
        self.stop()
        self.start()
        self.log("Serveur relancé.")

    # ── Boucle principale ───────────────────────────────────────────────────

    def run(self) -> int:
        """Boucle de surveillance — garde `forge run` vivant.

        Le superviseur ne s'arrête QUE sur KeyboardInterrupt (Ctrl+C) : une
        erreur applicative ne doit jamais arrêter le serveur de dév
        (DEV-SERVER-CRASH-RESILIENCE-001).

        Comportement :
            - changement de fichier → redémarrage propre (réarme le compteur
              de crashes) ;
            - mort inattendue du subprocess → relance automatique ;
            - crashes rapides répétés (> max_fast_crashes) → on cesse le
              respawn en boucle et on attend une modification de fichier pour
              relancer (l'erreur reste lisible dans le terminal) ;
            - KeyboardInterrupt → arrêt propre, retour 0.
        """
        self.log("Serveur Forge démarré.")
        self.log(f"Surveillance active : {self._watched_summary()}")

        self.start()
        snap = self._snapshot(self.root)
        fast_crashes = 0
        awaiting_change = False

        try:
            while True:
                self._sleep(self.poll_interval)

                # 1) Un changement de fichier relance toujours (et réarme).
                new_snap = self._snapshot(self.root)
                changes = diff_snapshots(snap, new_snap)
                if changes:
                    snap = new_snap
                    fast_crashes = 0
                    awaiting_change = False
                    self.restart(self._format_reason(changes))
                    continue

                # 2) En attente d'une correction : on idle sans respawner.
                if awaiting_change:
                    continue

                # 3) Le subprocess a-t-il disparu ? On le relance.
                if self.process is None or self.process.poll() is not None:
                    code = self.process.returncode if self.process else 0
                    uptime = time.monotonic() - self._spawn_time
                    self.log(f"Le serveur s'est arrêté (code {code}).")

                    fast_crashes = (
                        fast_crashes + 1 if uptime < self.healthy_uptime else 0
                    )
                    if fast_crashes > self.max_fast_crashes:
                        awaiting_change = True
                        self.log(
                            "Échecs répétés au démarrage — le serveur reste "
                            "arrêté. Corrigez l'erreur ci-dessus puis "
                            "enregistrez un fichier pour relancer."
                        )
                        continue

                    if fast_crashes and self.respawn_backoff:
                        self._sleep(self.respawn_backoff)
                    self.log("Redémarrage automatique du serveur...")
                    self.start()
                    self.log("Serveur relancé.")
        except KeyboardInterrupt:
            self.log("Interruption (Ctrl+C). Arrêt du serveur...")
        finally:
            self.stop()
        return 0

    # ── Aides ───────────────────────────────────────────────────────────────

    def _watched_summary(self) -> str:
        roots = ", ".join(ROOT_FILES_TO_WATCH)
        dirs = ", ".join(f"{rel}/" for rel, _ in DIRECTORIES_TO_WATCH)
        return f"{roots}, {dirs}"

    def _format_reason(self, changes: list[str]) -> str:
        if not changes:
            return ""
        first = changes[0]
        try:
            first_label = str(Path(first).resolve().relative_to(self.root.resolve()))
        except ValueError:
            first_label = first
        if len(changes) == 1:
            return first_label
        return f"{first_label} (+{len(changes) - 1} autres)"
