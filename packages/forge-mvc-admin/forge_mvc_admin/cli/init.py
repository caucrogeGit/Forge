# pyright: strict
"""Commande ``forge admin:init`` — ADMIN-INIT-COMMAND-001.

Prépare la structure ``mvc/admin/`` d'un projet Forge pour le back-office. À ce
stade du châssis, la commande crée :

- ``mvc/admin/__init__.py`` ;
- ``mvc/admin/resources.py`` : fichier où l'application déclare ses ressources
  administrables (``AdminResource`` enregistrées dans le registre).

Volontairement scoped (mirror ``video:init`` / ``iot:init``) :

- idempotente : un fichier déjà présent à l'identique n'est pas réécrit ;
- jamais d'écrasement silencieux : un fichier présent au contenu différent
  provoque un ``WARN`` et n'est pas touché (charte §9) ;
- pas de choix interactif ; pas de génération de vues ni de templates, qui
  viendront avec les tickets de dashboard et de rendu.
"""
from __future__ import annotations

from pathlib import Path

__all__ = [
    "STATUS_OK",
    "STATUS_INFO",
    "STATUS_WARN",
    "STATUS_ERROR",
    "ADMIN_INIT_PY",
    "ADMIN_RESOURCES_PY",
    "init_admin",
    "main",
]

STATUS_OK = "[OK]"
STATUS_INFO = "[INFO]"
STATUS_WARN = "[WARN]"
STATUS_ERROR = "[ERREUR]"

ADMIN_INIT_PY = '''\
"""Back-office Forge Admin du projet.

Les ressources administrables sont déclarées dans ``resources.py``.
"""
'''

ADMIN_RESOURCES_PY = '''\
"""Ressources administrables du projet (Forge Admin).

Déclarez ici les entités à administrer en enregistrant des ``AdminResource``
dans le registre. Adaptez l'exemple à vos entités, puis décommentez-le.

    from forge_mvc_admin import AdminResource, registry

    registry.register(AdminResource(
        entity="Article",
        slug="articles",
        label="Article",
        plural_label="Articles",
        list_fields=("title", "published_at"),
        form_fields=("title", "body"),
    ))
"""
'''


def _write_if_new(target: Path, content: str) -> str:
    """Écrit `content` si le fichier est absent. N'écrase jamais.

    Retourne ``"created"``, ``"identical"`` ou ``"different"``.
    """
    if target.exists():
        if target.read_text(encoding="utf-8") == content:
            return "identical"
        return "different"
    target.write_text(content, encoding="utf-8")
    return "created"


def init_admin(project_root: Path) -> int:
    """Crée la structure ``mvc/admin/`` sous ``project_root``.

    Returns
    -------
    0
        Succès, y compris en relecture idempotente.
    1
        Le dossier ``mvc/`` est absent (ce n'est pas un projet Forge).
    """
    mvc_dir = project_root / "mvc"
    if not mvc_dir.is_dir():
        print(f"{STATUS_ERROR} Ce dossier ne ressemble pas à un projet Forge.")
        print(
            "Conseil : lance cette commande à la racine du projet "
            "(dossier mvc/ attendu)."
        )
        return 1

    admin_dir = mvc_dir / "admin"
    if not admin_dir.exists():
        admin_dir.mkdir(parents=True)
        print(f"{STATUS_INFO} Dossier mvc/admin/ créé.")

    files: list[tuple[str, Path, str]] = [
        ("mvc/admin/__init__.py", admin_dir / "__init__.py", ADMIN_INIT_PY),
        ("mvc/admin/resources.py", admin_dir / "resources.py", ADMIN_RESOURCES_PY),
    ]
    for label, target, content in files:
        status = _write_if_new(target, content)
        if status == "created":
            print(f"{STATUS_OK} Créé : {label}")
        elif status == "identical":
            print(f"{STATUS_OK} Déjà présent (identique) : {label}")
        else:
            print(f"{STATUS_WARN} {label} existe et diffère — aucune modification.")

    print()
    print(f"{STATUS_INFO} Déclarez vos ressources dans mvc/admin/resources.py.")
    return 0


def main(args: list[str] | None = None) -> int:
    """Point d'entrée appelé par ``forge.py`` pour ``forge admin:init``."""
    return init_admin(Path.cwd())
