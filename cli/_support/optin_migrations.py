# pyright: strict
"""Provisioning partagé des opt-ins BDD (CORE-OPTIN-INIT-HELPER-001, ADR-071).

Les opt-ins adossés à la base (audit, settings, jobs, notifications, sessions-db,
images, video, iot) exposent tous une commande ``<optin>:init`` qui copie leurs
migrations SQL embarquées (``<package>/migrations/*.sql``) vers ``mvc/migrations/``
du projet, sans exécuter aucun SQL (charte §7 : Forge génère, l'opérateur
applique). La logique était dupliquée à l'identique dans chaque paquet ; elle est
centralisée ici. Chaque ``cli/init.py`` d'opt-in n'est plus qu'un mince adaptateur
qui fournit son nom de paquet et son libellé.

Idempotent, jamais d'écrasement silencieux : un fichier déjà présent au contenu
identique est signalé OK, un fichier différent provoque un WARN sans modification.
"""
from __future__ import annotations

from collections.abc import Iterator
from importlib import resources
from pathlib import Path

STATUS_OK = "[OK]"
STATUS_INFO = "[INFO]"
STATUS_WARN = "[WARN]"
STATUS_ERROR = "[ERREUR]"


def iter_migration_resources(package: str) -> Iterator[tuple[str, bytes]]:
    """Itère ``(filename, content_bytes)`` pour chaque ``.sql`` de ``<package>/migrations``."""
    anchor = resources.files(package) / "migrations"
    for entry in sorted(anchor.iterdir(), key=lambda e: e.name):
        if entry.name.endswith(".sql"):
            yield entry.name, entry.read_bytes()


def init_optin_migrations(package: str, label: str, project_root: Path) -> int:
    """Copie les migrations SQL de ``package`` vers ``<project_root>/mvc/migrations/``.

    ``label`` nomme l'opt-in dans les messages (« Audit », « Sessions »...).
    Renvoie 0 (succès, idempotent inclus) ou 1 si ``mvc/`` est absent (le dossier
    courant n'est pas un projet Forge).
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

    for name, content in iter_migration_resources(package):
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
        print(f"{STATUS_OK} Migration {label} copiée : mvc/migrations/{name}")
    for name in skipped_identical:
        print(f"{STATUS_OK} Migration {label} déjà présente (identique) : mvc/migrations/{name}")
    for name in skipped_different:
        print(f"{STATUS_WARN} mvc/migrations/{name} existe et diffère, aucune modification.")

    if copied or skipped_identical:
        print()
        print(f"{STATUS_INFO} Lance maintenant : forge migration:apply")

    return 0
