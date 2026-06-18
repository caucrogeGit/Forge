# pyright: strict
"""Commande ``forge iot:init`` — IOT-INIT-COMMAND-001.

Copie la (les) migration(s) SQL Forge IoT embarquée(s) dans le package
``forge_mvc_iot/migrations/`` vers le dossier ``mvc/migrations/`` du
projet utilisateur. **Aucune exécution SQL**, **aucune connexion
MariaDB** : on prépare seulement les fichiers, puis on suggère
``forge migration:apply``.

La commande est volontairement scoped :

- idempotente (rejouable sans erreur si la migration est déjà copiée
  à l'identique) ;
- jamais d'écrasement silencieux : un fichier déjà présent avec un
  contenu différent provoque un ``WARN`` et n'est pas écrasé ;
- pas de choix interactif, pas de rollback.

Lecture des ressources via ``importlib.resources.files("forge_mvc_iot")``
— fonctionne identiquement en install éditable et en install PyPI
(cf. ``IOT-PACKAGE-DATA-MIGRATIONS-001``).
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
    "iter_iot_migration_resources",
    "init_iot_migrations",
    "main",
]

STATUS_OK = "[OK]"
STATUS_INFO = "[INFO]"
STATUS_WARN = "[WARN]"
STATUS_ERROR = "[ERREUR]"


def iter_iot_migration_resources() -> Iterator[tuple[str, bytes]]:
    """Itère ``(filename, content_bytes)`` pour chaque ``.sql`` embarqué.

    Utilise ``importlib.resources`` — la liste reflète exactement ce qui
    est shippé dans la distribution PyPI via
    ``[tool.setuptools.package-data]``.
    """
    anchor = resources.files("forge_mvc_iot") / "migrations"
    for entry in sorted(anchor.iterdir(), key=lambda e: e.name):
        if entry.name.endswith(".sql"):
            yield entry.name, entry.read_bytes()


def init_iot_migrations(project_root: Path) -> int:
    """Copie les migrations IoT vers ``<project_root>/mvc/migrations/``.

    Returns
    -------
    0
        Succès (y compris idempotent : tous les fichiers déjà présents
        sont identiques).
    1
        Le dossier ``mvc/`` est absent (pas un projet Forge).
    """
    mvc_dir = project_root / "mvc"
    if not mvc_dir.is_dir():
        print(
            f"{STATUS_ERROR} Ce dossier ne ressemble pas à un projet Forge."
        )
        print(
            "Conseil : lance cette commande à la racine du projet "
            "(dossier mvc/ attendu)."
        )
        return 1

    target_dir = mvc_dir / "migrations"
    if not target_dir.exists():
        target_dir.mkdir(parents=True)
        print(f"{STATUS_INFO} Dossier mvc/migrations/ créé.")

    copied: list[str] = []
    skipped_identical: list[str] = []
    skipped_different: list[str] = []

    for name, content in iter_iot_migration_resources():
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
        print(f"{STATUS_OK} Migration IoT copiée : mvc/migrations/{name}")
    for name in skipped_identical:
        print(
            f"{STATUS_OK} Migration IoT déjà présente (identique) : "
            f"mvc/migrations/{name}"
        )
    for name in skipped_different:
        print(
            f"{STATUS_WARN} mvc/migrations/{name} existe et diffère "
            "— aucune modification."
        )

    # Suggestion d'enchaînement, dès qu'il y a au moins une migration
    # côté projet (copiée ou déjà identique).
    if copied or skipped_identical:
        print()
        print(f"{STATUS_INFO} Lance maintenant : forge migration:apply")

    return 0


def main(args: list[str] | None = None) -> int:
    """Point d'entrée appelé par ``forge.py`` pour ``forge iot:init``.

    Les arguments sont actuellement ignorés (pas d'option à ce ticket).
    """
    return init_iot_migrations(Path.cwd())
