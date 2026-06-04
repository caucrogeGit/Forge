"""Garde-fou CORE-DROP-UPLOADS-001 (ADR-019) — clôture du chantier forge-mvc-files.

État final : l'upload générique a entièrement quitté le core.

- ``core/uploads/`` n'existe plus ; ``import core.uploads`` échoue ;
- aucun fichier du dépôt (hors docs/history) n'importe ``core.uploads`` ;
- ``forge-mvc-files`` détient le pipeline (``save_upload``, storage, rate-limit,
  ``serve_media_file``) ;
- la **validation pure** + exceptions restent dans le core (``core.forms``).
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent


def test_core_uploads_dir_absent():
    assert not (PROJECT_ROOT / "core" / "uploads").exists(), (
        "core/uploads/ doit avoir été supprimé (upload extrait vers forge-mvc-files)."
    )


def test_core_uploads_not_importable():
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("core.uploads")


def test_no_python_file_imports_core_uploads():
    # Aucun import `core.uploads` ne doit subsister dans le code (hors docstrings
    # et fichiers de test d'absence qui le mentionnent comme chaîne).
    offenders: list[str] = []
    for base in ("core", "forge_cli", "mvc", "integrations", "packages"):
        root = PROJECT_ROOT / base
        if not root.exists():
            continue
        for py in root.rglob("*.py"):
            if "__pycache__" in str(py):
                continue
            for lineno, line in enumerate(
                py.read_text(encoding="utf-8", errors="replace").splitlines(), 1
            ):
                stripped = line.lstrip()
                if stripped.startswith(("import core.uploads", "from core.uploads")):
                    offenders.append(f"{py.relative_to(PROJECT_ROOT)}:{lineno}")
    # app.py racine
    app_py = PROJECT_ROOT / "app.py"
    if app_py.exists():
        for lineno, line in enumerate(app_py.read_text(encoding="utf-8").splitlines(), 1):
            stripped = line.lstrip()
            if stripped.startswith(("import core.uploads", "from core.uploads")):
                offenders.append(f"app.py:{lineno}")
    assert not offenders, f"Imports core.uploads résiduels : {offenders}"


def test_forge_mvc_files_owns_pipeline():
    import forge_mvc_files

    for name in ("save_upload", "serve_media_file", "save_bytes",
                 "normalize_media_path", "is_upload_rate_limited"):
        assert hasattr(forge_mvc_files, name)


def test_validation_stays_in_core():
    from core.forms.upload_validation import validate_upload_metadata  # noqa: F401
    from core.forms.upload_exceptions import UploadError  # noqa: F401
