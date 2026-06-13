"""Garde-fou FILES-IMAGES-REPOINT-001 (ADR-019).

Inversion de dépendance : ``forge-mvc-images`` n'importe plus ``core.uploads``
(parti vers ``forge-mvc-files``) mais dépend de ``forge-mvc-files`` :

- aucun module ``forge_mvc_images`` n'importe ``core.uploads`` (pipeline déplacé) ;
- ``forge_mvc_images`` importe ``forge_mvc_files`` (pipeline) et ``core.forms``
  (validation, restée dans le core) ;
- ``packages/forge-mvc-images/pyproject.toml`` **déclare** la dépendance
  ``forge-mvc-files`` (sinon import sans dépendance déclarée — bug de packaging).
"""
from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
IMAGES_PKG = PROJECT_ROOT / "packages" / "forge-mvc-images"
IMAGES_SRC = IMAGES_PKG / "forge_mvc_images"
IMAGES_PYPROJECT = IMAGES_PKG / "pyproject.toml"


class TestNoCoreUploadsImport:
    def test_no_module_imports_core_uploads(self):
        offenders = []
        for py in IMAGES_SRC.rglob("*.py"):
            for lineno, line in enumerate(
                py.read_text(encoding="utf-8", errors="replace").splitlines(), 1
            ):
                stripped = line.lstrip()
                if stripped.startswith("#"):
                    continue
                if "core.uploads" in stripped and (
                    stripped.startswith("import ") or stripped.startswith("from ")
                ):
                    offenders.append(f"{py.relative_to(PROJECT_ROOT)}:{lineno}")
        assert not offenders, (
            "forge_mvc_images ne doit plus importer core.uploads "
            f"(pipeline déplacé vers forge-mvc-files) : {offenders}"
        )


class TestDependsOnForgeFiles:
    def test_imports_forge_mvc_files(self):
        text = (IMAGES_SRC / "processing.py").read_text(encoding="utf-8")
        assert "forge_mvc_files" in text

    def test_pyproject_declares_forge_mvc_files(self):
        data = tomllib.loads(IMAGES_PYPROJECT.read_text(encoding="utf-8"))
        deps = data["project"]["dependencies"]
        assert any("forge-mvc-files" in d for d in deps), (
            "forge-mvc-images doit DÉCLARER la dépendance forge-mvc-files dans "
            "son pyproject (sinon `pip install forge-mvc-images` ne tire pas "
            "le pipeline d'upload)."
        )


class TestValidationStillFromCore:
    def test_validation_imported_from_core_forms(self):
        # La validation pure reste dans le core (core.forms), pas dans l'opt-in.
        text = (IMAGES_SRC / "processing.py").read_text(encoding="utf-8")
        assert "core.forms.upload_validation" in text
        assert "core.forms.upload_exceptions" in text


class TestFunctional:
    def test_save_image_upload_still_works(self, tmp_path, monkeypatch):
        import core.forge as forge
        from types import SimpleNamespace
        from io import BytesIO
        from PIL import Image
        from forge_mvc_images import save_image_upload

        # ADR-032 : upload_root, extensions et types MIME lus depuis
        # l'environnement ; seul upload_max_size reste détenu par le noyau.
        monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path / "uploads"))
        monkeypatch.setenv("UPLOAD_ALLOWED_EXTENSIONS", "png")
        monkeypatch.setenv("UPLOAD_ALLOWED_MIME_TYPES", "image/png")
        forge.configure(upload_max_size=1_000_000)
        buf = BytesIO()
        Image.new("RGB", (40, 20), (10, 20, 30)).save(buf, format="PNG")
        f = SimpleNamespace(filename="x.png", content=buf.getvalue(), content_type="image/png")

        saved = save_image_upload(f, category="images", variants=True)
        assert saved.path.startswith("images/")
        assert saved.variants["medium"]
