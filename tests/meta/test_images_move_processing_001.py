"""Garde-fou IMAGES-MOVE-PROCESSING-001 (ADR-018).

Vérifie le déplacement du traitement d'image du core vers l'opt-in
``forge-mvc-images`` :

- ``core/uploads/image.py`` a disparu du core (déplacé) ;
- plus aucun fichier ``core/`` n'importe Pillow (le pipeline image quitte le
  runtime du core — principe 8) ;
- ``core.uploads`` ne réexporte plus l'API image (``save_image``,
  ``generate_image_variants``, ``verify_image_content``, constantes
  ``ALLOWED_IMAGE_*``, ``IMAGE_VARIANT_SIZES``, ``MediaRecord``) ;
- ``forge_mvc_images`` expose désormais toute cette API ;
- ``core.uploads.save_upload`` reste générique : il **délègue** le chemin
  image-aware à l'opt-in en import *lazy* (``_require_image_processing``), sans
  réintroduire d'import dur de ``core.uploads.image``.

Le delegate transitoire garde la suite verte : ``save_upload(category="images",
variants=True)`` continue de fonctionner (tests fonctionnels dans
``tests/test_uploads.py``). Le passage de ``save_upload`` à 100 % générique
relèvera d'un ticket de nettoyage ultérieur (après le rename des générateurs).
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
CORE_DIR = PROJECT_ROOT / "core"
CORE_UPLOADS = CORE_DIR / "uploads"

PROCESSING_API = (
    "ALLOWED_IMAGE_EXTENSIONS",
    "ALLOWED_IMAGE_MIME_TYPES",
    "IMAGE_VARIANT_SIZES",
    "MediaRecord",
    "generate_image_variants",
    "image_variant_paths",
    "image_variant_relative_paths",
    "save_image",
    "verify_image_content",
)


class TestImageRemovedFromCore:
    """Le traitement d'image a quitté le core."""

    def test_core_image_module_absent(self):
        assert not (CORE_UPLOADS / "image.py").exists(), (
            "core/uploads/image.py doit avoir été déplacé vers "
            "forge_mvc_images (IMAGES-MOVE-PROCESSING-001)."
        )

    def test_no_pillow_import_in_core(self):
        offenders: list[str] = []
        for py in CORE_DIR.rglob("*.py"):
            for lineno, line in enumerate(
                py.read_text(encoding="utf-8", errors="replace").splitlines(), 1
            ):
                stripped = line.lstrip()
                if stripped.startswith(("from PIL", "import PIL")):
                    offenders.append(f"{py.relative_to(PROJECT_ROOT)}:{lineno}")
        assert not offenders, (
            "Aucun fichier sous core/ ne doit importer Pillow ; le pipeline "
            f"image vit dans forge-mvc-images. Fautifs : {offenders}"
        )

    def test_core_uploads_no_longer_exports_image_api(self):
        import core.uploads as uploads

        leaked = [name for name in PROCESSING_API if name in uploads.__all__]
        assert not leaked, (
            "core.uploads ne doit plus réexporter l'API image "
            f"(retirée par IMAGES-MOVE-PROCESSING-001) : {leaked}"
        )

    @pytest.mark.parametrize("name", PROCESSING_API)
    def test_core_uploads_image_attr_absent(self, name: str):
        import core.uploads as uploads

        assert not hasattr(uploads, name), (
            f"core.uploads ne doit plus exposer '{name}' (déplacé dans "
            "forge_mvc_images)."
        )


class TestProcessingApiInOptin:
    """forge_mvc_images possède désormais tout le traitement d'image."""

    def test_processing_submodule_exists(self):
        import forge_mvc_images.processing  # noqa: F401

    @pytest.mark.parametrize("name", PROCESSING_API)
    def test_optin_exposes_api(self, name: str):
        import forge_mvc_images

        assert hasattr(forge_mvc_images, name), (
            f"forge_mvc_images doit exposer '{name}' (déplacé du core)."
        )

    def test_optin_all_lists_api(self):
        import forge_mvc_images

        missing = [name for name in PROCESSING_API if name not in forge_mvc_images.__all__]
        assert not missing, (
            f"forge_mvc_images.__all__ doit lister l'API image : manquants {missing}"
        )


class TestSaveUploadDelegates:
    """save_upload garde la branche image mais la délègue à l'opt-in."""

    def test_manager_has_lazy_delegate_helper(self):
        from core.uploads import manager

        assert hasattr(manager, "_require_image_processing"), (
            "core.uploads.manager doit fournir _require_image_processing "
            "(lock + delegate vers forge_mvc_images)."
        )

    def test_delegate_resolves_processing_functions(self):
        from core.uploads.manager import _require_image_processing

        for name in (
            "verify_image_content",
            "generate_image_variants",
            "image_variant_relative_paths",
        ):
            resolved = _require_image_processing(name)
            assert callable(resolved), f"{name} doit être résoluble via le delegate."

    def test_manager_source_has_no_core_image_import(self):
        from core.uploads import manager

        source = inspect.getsource(manager)
        assert "core.uploads.image" not in source, (
            "manager ne doit plus importer core.uploads.image (module déplacé)."
        )
