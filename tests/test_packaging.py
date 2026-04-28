"""Vérifie que le packaging pyproject.toml couvre tous les packages requis."""

from __future__ import annotations

import fnmatch
import os
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_pyproject() -> dict:
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def _simulate_find_packages(patterns: list[str]) -> set[str]:
    """Imite find_packages(include=[...]) sans dépendance setuptools."""
    found = set()
    skip = {".venv", "node_modules", "__pycache__", ".git", "site", "deploy"}
    for dirpath, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in skip]
        if "__init__.py" not in files:
            continue
        rel = os.path.relpath(dirpath, ROOT).replace(os.sep, ".")
        if any(fnmatch.fnmatch(rel, p) for p in patterns):
            found.add(rel)
    return found


# ── Structure pyproject.toml ──────────────────────────────────────────────────

def test_pyproject_utilise_find_packages():
    data = _load_pyproject()
    setuptools = data["tool"]["setuptools"]
    assert "find" in setuptools.get("packages", {}), (
        "pyproject.toml doit utiliser [tool.setuptools.packages.find] "
        "et non une liste explicite — risque d'oublier les nouveaux packages."
    )


def test_pyproject_inclut_core_et_sous_packages():
    data = _load_pyproject()
    patterns = data["tool"]["setuptools"]["packages"]["find"]["include"]
    assert any(fnmatch.fnmatch("core", p) for p in patterns)
    assert any(fnmatch.fnmatch("core.uploads", p) for p in patterns)


def test_pyproject_exclut_tests_et_mvc_applicatif():
    data = _load_pyproject()
    patterns = data["tool"]["setuptools"]["packages"]["find"]["include"]
    for excluded in ("tests", "mvc", "cmd"):
        assert not any(fnmatch.fnmatch(excluded, p) for p in patterns), (
            f"Le package '{excluded}' ne doit pas être inclus dans le packaging."
        )


# ── Packages découverts ───────────────────────────────────────────────────────

def test_find_packages_couvre_core_uploads():
    data = _load_pyproject()
    patterns = data["tool"]["setuptools"]["packages"]["find"]["include"]
    found = _simulate_find_packages(patterns)
    assert "core.uploads" in found, (
        "core.uploads introuvable avec les patterns find_packages actuels — "
        "vérifier que core/uploads/__init__.py existe."
    )


def test_find_packages_couvre_tous_les_sous_packages_core():
    data = _load_pyproject()
    patterns = data["tool"]["setuptools"]["packages"]["find"]["include"]
    found = _simulate_find_packages(patterns)

    expected = {
        "core", "core.database", "core.forms", "core.http",
        "core.mvc", "core.mvc.controller", "core.mvc.model", "core.mvc.view",
        "core.security", "core.templating", "core.validation", "core.uploads",
    }
    missing = expected - found
    assert not missing, f"Packages manquants dans le packaging : {missing}"


def test_find_packages_couvre_forge_cli_et_integrations():
    data = _load_pyproject()
    patterns = data["tool"]["setuptools"]["packages"]["find"]["include"]
    found = _simulate_find_packages(patterns)

    for pkg in ("forge_cli", "forge_cli.entities", "integrations", "integrations.jinja2"):
        assert pkg in found, f"{pkg} absent du packaging."


def test_package_data_inclut_tous_les_fichiers_starters():
    data = _load_pyproject()
    package_data = data["tool"]["setuptools"]["package-data"]

    assert package_data["forge_cli"] == ["starters/data/**/*"]


def test_package_data_couvre_les_python_des_starters():
    data = _load_pyproject()
    patterns = data["tool"]["setuptools"]["package-data"]["forge_cli"]
    starter_file = "starters/data/carnet-contacts/files/mvc/controllers/contact_controller.py"

    assert any(fnmatch.fnmatch(starter_file, pattern) for pattern in patterns)


# ── Fichiers starters sur disque ──────────────────────────────────────────────

def test_starter1_fichiers_sur_disque():
    """Starter 1 (contact-simple) : JSON uniquement, pas de files/."""
    root = ROOT / "forge_cli" / "starters" / "data" / "contact-simple"
    for rel in ("starter.json", "contact.json"):
        assert (root / rel).exists(), f"Manquant : contact-simple/{rel}"


def test_starter2_fichiers_sur_disque():
    """Starter 2 (utilisateurs-auth) : contrôleurs, modèles, vues, scripts."""
    root = ROOT / "forge_cli" / "starters" / "data" / "utilisateurs-auth"
    for rel in (
        "starter.json",
        "routes.py.snippet",
        "files/mvc/controllers/auth_controller.py",
        "files/mvc/controllers/dashboard_controller.py",
        "files/mvc/models/auth_model.py",
        "files/mvc/views/auth/login.html",
        "files/mvc/views/dashboard/index.html",
        "files/scripts/create_auth_user.py",
    ):
        assert (root / rel).exists(), f"Manquant : utilisateurs-auth/{rel}"


def test_starter3_fichiers_sur_disque():
    """Starter 3 (carnet-contacts) : contrôleurs, formulaires, modèles, vues, seed."""
    root = ROOT / "forge_cli" / "starters" / "data" / "carnet-contacts"
    for rel in (
        "starter.json",
        "relations.json",
        "routes.py.snippet",
        "files/mvc/controllers/contact_controller.py",
        "files/mvc/controllers/ville_controller.py",
        "files/mvc/forms/contact_form.py",
        "files/mvc/models/contact_model.py",
        "files/mvc/models/ville_model.py",
        "files/mvc/views/contact/index.html",
        "files/mvc/views/contact/form.html",
        "files/mvc/views/contact/show.html",
        "files/mvc/views/ville/index.html",
        "files/scripts/seed_villes.py",
    ):
        assert (root / rel).exists(), f"Manquant : carnet-contacts/{rel}"


def test_starter4_fichiers_sur_disque():
    """Starter 4 (suivi-comportement-eleves) : contrôleurs, modèles, vues, seeds."""
    root = ROOT / "forge_cli" / "starters" / "data" / "suivi-comportement-eleves"
    for rel in (
        "starter.json",
        "relations.json",
        "routes.py.snippet",
        "files/mvc/controllers/auth_controller.py",
        "files/mvc/controllers/cours_controller.py",
        "files/mvc/controllers/eleve_controller.py",
        "files/mvc/controllers/observation_cours_controller.py",
        "files/mvc/controllers/suivi_controller.py",
        "files/mvc/models/auth_model.py",
        "files/mvc/models/cours_model.py",
        "files/mvc/models/eleve_model.py",
        "files/mvc/models/observation_cours_model.py",
        "files/mvc/views/auth/login.html",
        "files/mvc/views/cours/index.html",
        "files/mvc/views/eleve/index.html",
        "files/mvc/views/suivi/dashboard.html",
        "files/scripts/seed_suivi.py",
        "files/scripts/create_auth_user.py",
    ):
        assert (root / rel).exists(), f"Manquant : suivi-comportement-eleves/{rel}"


def test_package_data_couvre_tous_types_fichiers_starters():
    """Le glob starters/data/**/* couvre .py, .json, .html et .snippet de tous les starters."""
    data = _load_pyproject()
    patterns = data["tool"]["setuptools"]["package-data"]["forge_cli"]

    representative = [
        # Starter 1
        "starters/data/contact-simple/starter.json",
        "starters/data/contact-simple/contact.json",
        # Starter 2
        "starters/data/utilisateurs-auth/starter.json",
        "starters/data/utilisateurs-auth/routes.py.snippet",
        "starters/data/utilisateurs-auth/files/mvc/controllers/auth_controller.py",
        "starters/data/utilisateurs-auth/files/mvc/views/auth/login.html",
        # Starter 3
        "starters/data/carnet-contacts/starter.json",
        "starters/data/carnet-contacts/relations.json",
        "starters/data/carnet-contacts/routes.py.snippet",
        "starters/data/carnet-contacts/files/mvc/controllers/contact_controller.py",
        "starters/data/carnet-contacts/files/mvc/views/contact/index.html",
        "starters/data/carnet-contacts/files/scripts/seed_villes.py",
        # Starter 4
        "starters/data/suivi-comportement-eleves/starter.json",
        "starters/data/suivi-comportement-eleves/relations.json",
        "starters/data/suivi-comportement-eleves/routes.py.snippet",
        "starters/data/suivi-comportement-eleves/files/mvc/controllers/cours_controller.py",
        "starters/data/suivi-comportement-eleves/files/mvc/views/suivi/dashboard.html",
        "starters/data/suivi-comportement-eleves/files/scripts/seed_suivi.py",
    ]

    for path in representative:
        assert any(fnmatch.fnmatch(path, p) for p in patterns), (
            f"Non couvert par package-data : {path}"
        )


# ── Importabilité directe ─────────────────────────────────────────────────────

def test_core_uploads_importable():
    """Protection régression : core.uploads doit toujours s'importer."""
    from core.uploads.manager import save_upload  # noqa: F401
    from core.uploads.exceptions import UploadStorageError  # noqa: F401
    from core.uploads.validators import validate_upload_metadata  # noqa: F401
    from core.uploads.storage import ensure_upload_dirs  # noqa: F401
