"""Détection de scaffold existant et nettoyage --force pour les starters."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from forge_cli.starters.file_ops import entity_specs, to_snake
from forge_cli.starters.route_ops import marker_present, remove_marker


def check_existing(meta: dict, root: Path) -> list[str]:
    """Retourne la liste des chemins du starter déjà présents dans le projet."""
    found = []
    for rel in meta.get("check_paths", []):
        p = root / rel
        if p.exists() and not _is_adoptable(meta, p, root):
            found.append(rel)
    marker = meta.get("routes_marker", "")
    if marker and marker_present(root / "mvc" / "routes.py", marker):
        found.append("mvc/routes.py (marqueurs déjà présents)")
    return found


def _is_adoptable(meta: dict, path: Path, root: Path) -> bool:
    """
    Renvoie True si le fichier est un artefact du squelette Forge neuf
    qui peut être adopté sans conflit (pas besoin de --force).
    """
    rel = path.relative_to(root).as_posix()

    # relations.json vide du squelette → adoptable par carnet-contacts
    if meta.get("id") == "carnet-contacts" and rel == "mvc/entities/relations.json":
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            return False
        return data == {"format_version": 1, "relations": []}

    # Fichiers auth du squelette → adoptables par utilisateurs-auth
    if meta.get("id") != "utilisateurs-auth" or not path.is_file():
        return False
    content = path.read_text(encoding="utf-8")
    if rel == "mvc/controllers/auth_controller.py":
        return 'BaseController.redirect("/")' in content and "DashboardController" not in content
    if rel == "mvc/models/auth_model.py":
        return "GET_ROLES_UTILISATEUR" in content and "utilisateur_role" in content
    if rel == "mvc/views/auth/login.html":
        return 'action="/login"' in content and 'name="csrf_token"' in content
    return False


def force_clean_crud(meta: dict, root: Path) -> None:
    """Supprime uniquement les fichiers générés par un starter CRUD simple."""
    snake = to_snake(meta["entity"])
    _rmdir(root / "mvc" / "entities" / snake)
    _rmdir(root / "mvc" / "views" / snake)
    for rel in (
        f"mvc/controllers/{snake}_controller.py",
        f"mvc/models/{snake}_model.py",
        f"mvc/forms/{snake}_form.py",
    ):
        _rm(root / rel)
    marker = meta.get("routes_marker", "")
    if marker:
        remove_marker(root / "mvc" / "routes.py", marker)


def force_clean_application(meta: dict, root: Path) -> None:
    """Supprime uniquement les fichiers déclarés dans check_paths du starter."""
    # Fichiers régénérables dans chaque dossier d'entité (les manuels sont préservés)
    regenerable: dict[Path, set[Path]] = {}
    for spec in entity_specs(meta):
        s = to_snake(spec["entity"])
        d = Path("mvc") / "entities" / s
        regenerable[d] = {d / f"{s}.json", d / f"{s}.sql", d / f"{s}_base.py"}

    for rel in meta.get("check_paths", []):
        p = root / rel
        rel_path = Path(rel)
        if rel_path in regenerable:
            for gen in regenerable[rel_path]:
                _rm(root / gen)
        elif p.is_dir():
            shutil.rmtree(p)
        elif p.exists():
            p.unlink()

    marker = meta.get("routes_marker", "")
    if marker:
        remove_marker(root / "mvc" / "routes.py", marker)


def _rm(path: Path) -> None:
    if path.exists():
        path.unlink()


def _rmdir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
