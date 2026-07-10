# pyright: strict
"""Commande ``forge sessions:init`` — provisionne le schéma (retour terrain 016 F34).

Copie le DDL embarqué (`forge_mvc_sessions_db/sql/`) vers le dossier
`mvc/models/sql/` du projet, sans aucune exécution SQL ni connexion base. On
prépare le fichier, puis on suggère `forge db:apply`.

Idempotente, jamais d'écrasement silencieux : un fichier déjà présent au
contenu différent provoque un `WARN` et n'est pas écrasé. Lecture des
ressources via `importlib.resources`, identique en éditable et en PyPI.
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
    "iter_sessions_sql_resources",
    "init_sessions_schema",
    "main",
]

STATUS_OK = "[OK]"
STATUS_INFO = "[INFO]"
STATUS_WARN = "[WARN]"
STATUS_ERROR = "[ERREUR]"


def iter_sessions_sql_resources() -> Iterator[tuple[str, bytes]]:
    """Itère ``(filename, content_bytes)`` pour chaque ``.sql`` embarqué."""
    anchor = resources.files("forge_mvc_sessions_db") / "sql"
    for entry in sorted(anchor.iterdir(), key=lambda e: e.name):
        if entry.name.endswith(".sql"):
            yield entry.name, entry.read_bytes()


def init_sessions_schema(project_root: Path) -> int:
    """Copie le DDL Sessions vers ``<project_root>/mvc/models/sql/``.

    Renvoie 0 (succès, idempotent inclus) ou 1 si ``mvc/`` est absent.
    """
    mvc_dir = project_root / "mvc"
    if not mvc_dir.is_dir():
        print(f"{STATUS_ERROR} Ce dossier ne ressemble pas à un projet Forge.")
        print("Conseil : lance cette commande à la racine du projet (dossier mvc/ attendu).")
        return 1

    target_dir = mvc_dir / "models" / "sql"
    if not target_dir.exists():
        target_dir.mkdir(parents=True)
        print(f"{STATUS_INFO} Dossier mvc/models/sql/ créé.")

    copied: list[str] = []
    skipped_identical: list[str] = []
    skipped_different: list[str] = []

    for name, content in iter_sessions_sql_resources():
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
        print(f"{STATUS_OK} DDL Sessions copié : mvc/models/sql/{name}")
    for name in skipped_identical:
        print(f"{STATUS_OK} DDL Sessions déjà présent (identique) : mvc/models/sql/{name}")
    for name in skipped_different:
        print(f"{STATUS_WARN} mvc/models/sql/{name} existe et diffère, aucune modification.")

    if copied or skipped_identical:
        print()
        print(f"{STATUS_INFO} Lance maintenant : forge db:apply")

    return 0


def main(args: list[str] | None = None) -> int:
    """Point d'entrée appelé par ``forge.py`` pour ``forge sessions:init``."""
    return init_sessions_schema(Path.cwd())
