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


# ── Importabilité directe ─────────────────────────────────────────────────────

def test_core_uploads_importable():
    """Protection régression : core.uploads doit toujours s'importer."""
    from core.uploads.manager import save_upload  # noqa: F401
    from core.uploads.exceptions import UploadStorageError  # noqa: F401
    from core.uploads.validators import validate_upload_metadata  # noqa: F401
    from core.uploads.storage import ensure_upload_dirs  # noqa: F401
