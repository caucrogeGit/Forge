# pyright: strict
"""Commande ``forge jobs:init`` — JOBS-INIT-COMMAND-001.

Copie la migration SQL embarquée (`forge_mvc_jobs/migrations/`) vers le dossier
`mvc/migrations/` du projet, sans exécution SQL ni connexion MariaDB. On prépare
le fichier, puis on suggère `forge migration:apply`.

Idempotente, jamais d'écrasement silencieux : un fichier déjà présent au contenu
différent provoque un `WARN` et n'est pas écrasé.
"""
from __future__ import annotations

from collections.abc import Iterator
from importlib import resources
from pathlib import Path

__all__ = [
    "STATUS_OK",
    "STATUS_INFO",
    "STATUS_WARN",
    "STATUS_ERROR",
    "iter_jobs_migration_resources",
    "init_jobs_migrations",
    "main",
]

STATUS_OK = "[OK]"
STATUS_INFO = "[INFO]"
STATUS_WARN = "[WARN]"
STATUS_ERROR = "[ERREUR]"


def iter_jobs_migration_resources() -> Iterator[tuple[str, bytes]]:
    """Itère ``(filename, content_bytes)`` pour chaque ``.sql`` embarqué."""
    anchor = resources.files("forge_mvc_jobs") / "migrations"
    for entry in sorted(anchor.iterdir(), key=lambda e: e.name):
        if entry.name.endswith(".sql"):
            yield entry.name, entry.read_bytes()


def init_jobs_migrations(project_root: Path) -> int:
    """Copie les migrations Jobs vers ``<project_root>/mvc/migrations/``.

    Renvoie 0 (succès, idempotent inclus) ou 1 si ``mvc/`` est absent.
    """
    mvc_dir = project_root / "mvc"
    if not mvc_dir.is_dir():
        print(f"{STATUS_ERROR} Ce dossier ne ressemble pas à un projet Forge.")
        print("Conseil : lance cette commande à la racine du projet (dossier mvc/ attendu).")
        return 1

    target_dir = mvc_dir / "migrations"
    if not target_dir.exists():
        target_dir.mkdir(parents=True)
        print(f"{STATUS_INFO} Dossier mvc/migrations/ créé.")

    copied: list[str] = []
    skipped_identical: list[str] = []
    skipped_different: list[str] = []

    for name, content in iter_jobs_migration_resources():
        target = target_dir / name
        if target.exists():
            if target.read_bytes() == content:
                skipped_identical.append(name)
            else:
                skipped_different.append(name)
            continue
        target.write_bytes(content)
        copied.append(name)

    for name in copied:
        print(f"{STATUS_OK} Migration Jobs copiée : mvc/migrations/{name}")
    for name in skipped_identical:
        print(f"{STATUS_OK} Migration Jobs déjà présente (identique) : mvc/migrations/{name}")
    for name in skipped_different:
        print(f"{STATUS_WARN} mvc/migrations/{name} existe et diffère, aucune modification.")

    if copied or skipped_identical:
        print()
        print(f"{STATUS_INFO} Lance maintenant : forge migration:apply")

    return 0


def main(args: list[str] | None = None) -> int:
    """Point d'entrée appelé par ``forge.py`` pour ``forge jobs:init``."""
    return init_jobs_migrations(Path.cwd())
