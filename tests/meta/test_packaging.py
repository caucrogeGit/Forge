"""Vérifie que le packaging pyproject.toml couvre tous les packages requis."""

from __future__ import annotations

import fnmatch
import os
import tomllib
from pathlib import Path
import pytest

pytestmark = pytest.mark.meta

ROOT = Path(__file__).resolve().parents[2]


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
    starter_file = "starters/data/users-core-auth/files/mvc/controllers/auth_controller.py"

    assert any(fnmatch.fnmatch(starter_file, pattern) for pattern in patterns)


# ── Fichiers starters sur disque ──────────────────────────────────────────────

def test_starter1_fichiers_sur_disque():
    """Starter 1 (contact-simple) : JSON uniquement, pas de files/."""
    root = ROOT / "forge_cli" / "starters" / "data" / "contact-simple"
    for rel in ("starter.json", "contact.json"):
        assert (root / rel).exists(), f"Manquant : contact-simple/{rel}"


def test_starter2_fichiers_sur_disque():
    """Starter 2 (users-core-auth) : contrôleurs, modèles, vues, scripts."""
    root = ROOT / "forge_cli" / "starters" / "data" / "users-core-auth"
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
        assert (root / rel).exists(), f"Manquant : users-core-auth/{rel}"


def test_package_data_couvre_tous_types_fichiers_starters():
    """Le glob starters/data/**/* couvre .py, .json, .html et .snippet de tous les starters."""
    data = _load_pyproject()
    patterns = data["tool"]["setuptools"]["package-data"]["forge_cli"]

    representative = [
        # Starter 1
        "starters/data/contact-simple/starter.json",
        "starters/data/contact-simple/contact.json",
        # Starter 2
        "starters/data/users-core-auth/starter.json",
        "starters/data/users-core-auth/routes.py.snippet",
        "starters/data/users-core-auth/files/mvc/controllers/auth_controller.py",
        "starters/data/users-core-auth/files/mvc/views/auth/login.html",
        "starters/data/users-core-auth/files/scripts/create_auth_user.py",
    ]

    for path in representative:
        assert any(fnmatch.fnmatch(path, p) for p in patterns), (
            f"Non couvert par package-data : {path}"
        )


# ── Dépendances déclarées ─────────────────────────────────────────────────────

def test_pillow_dans_pyproject():
    data = _load_pyproject()
    deps = data["project"]["dependencies"]
    pillow_deps = [d for d in deps if d.lower().startswith("pillow")]
    assert pillow_deps, "Pillow absent des dependencies dans pyproject.toml"
    assert any(">=" in d for d in pillow_deps), (
        "Pillow doit avoir une contrainte de version minimale dans pyproject.toml"
    )


def test_pillow_dans_requirements_txt():
    reqs = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    lines = [l.strip() for l in reqs.splitlines() if l.strip() and not l.startswith("#")]
    pillow_lines = [l for l in lines if l.lower().startswith("pillow")]
    assert pillow_lines, "Pillow absent de requirements.txt"


def test_pillow_contrainte_coherente():
    """pyproject.toml et requirements.txt doivent déclarer la même contrainte Pillow."""
    data = _load_pyproject()
    deps = data["project"]["dependencies"]
    pyproject_pillow = next(d for d in deps if d.lower().startswith("pillow"))

    reqs = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    req_pillow = next(
        l.strip() for l in reqs.splitlines()
        if l.strip().lower().startswith("pillow")
    )

    assert pyproject_pillow == req_pillow, (
        f"Contrainte Pillow incohérente :\n"
        f"  pyproject.toml : {pyproject_pillow}\n"
        f"  requirements.txt : {req_pillow}"
    )


def test_argon2_cffi_dans_pyproject():
    data = _load_pyproject()
    deps = data["project"]["dependencies"]
    argon2_deps = [d for d in deps if d.lower().startswith("argon2-cffi")]
    assert argon2_deps, "argon2-cffi absent des dependencies dans pyproject.toml"
    assert argon2_deps == ["argon2-cffi>=25.1,<26"]


def test_argon2_cffi_dans_requirements_txt():
    reqs = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    lines = [l.strip() for l in reqs.splitlines() if l.strip() and not l.startswith("#")]
    argon2_lines = [l for l in lines if l.lower().startswith("argon2-cffi")]
    assert argon2_lines == ["argon2-cffi>=25.1,<26"]


def test_argon2_cffi_contrainte_coherente():
    data = _load_pyproject()
    deps = data["project"]["dependencies"]
    pyproject_argon2 = next(d for d in deps if d.lower().startswith("argon2-cffi"))

    reqs = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    req_argon2 = next(
        l.strip() for l in reqs.splitlines()
        if l.strip().lower().startswith("argon2-cffi")
    )

    assert pyproject_argon2 == req_argon2, (
        f"Contrainte argon2-cffi incohérente :\n"
        f"  pyproject.toml : {pyproject_argon2}\n"
        f"  requirements.txt : {req_argon2}"
    )


# ── Importabilité directe ─────────────────────────────────────────────────────

def test_pil_importable():
    """Pillow (PIL) doit être importable — dépendance runtime obligatoire."""
    from PIL import Image  # noqa: F401


def test_argon2_importable():
    """argon2-cffi doit être importable — dépendance runtime obligatoire."""
    from argon2 import PasswordHasher  # noqa: F401


def test_core_uploads_importable():
    """Protection régression : core.uploads doit toujours s'importer."""
    from core.uploads.manager import save_upload  # noqa: F401
    from core.uploads.exceptions import UploadStorageError  # noqa: F401
    from core.uploads.validators import validate_upload_metadata  # noqa: F401
    from core.uploads.storage import ensure_upload_dirs  # noqa: F401
