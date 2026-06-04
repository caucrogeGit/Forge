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
- ``core.uploads`` ne réintroduit pas d'import dur de ``core.uploads.image``.

Depuis CORE-SAVEUPLOAD-GENERIC-CLEANUP, ``save_upload`` est **purement
générique** (plus aucune branche image) ; le chemin image-aware appartient à
``forge_mvc_images.save_image_upload``. Le delegate lazy
(``_require_image_processing``) ne sert plus qu'à ``delete_media_file
(variants=True)`` (suppression des fichiers de variantes).
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

    def test_core_uploads_module_removed(self):
        # CORE-DROP-UPLOADS-001 (ADR-019) : core.uploads a entièrement disparu
        # (l'API image ne peut donc plus en venir, a fortiori).
        import importlib

        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("core.uploads")


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


class TestSaveUploadIsGeneric:
    """CORE-SAVEUPLOAD-GENERIC-CLEANUP : save_upload n'a plus rien d'image-aware."""

    def test_save_upload_signature_has_no_variants(self):
        import inspect as _inspect

        # CORE-DROP-UPLOADS-001 : save_upload vit dans forge_mvc_files.
        from forge_mvc_files.manager import save_upload

        params = _inspect.signature(save_upload).parameters
        assert "variants" not in params, (
            "save_upload ne doit plus exposer de paramètre `variants` "
            "(chemin image-aware déplacé dans forge_mvc_images.save_image_upload)."
        )

    def test_save_upload_source_has_no_image_branch(self):
        from forge_mvc_files import manager

        src = inspect.getsource(manager.save_upload)
        assert 'category == "images"' not in src, (
            "save_upload ne doit plus contenir de branche spécifique aux images."
        )

    def test_manager_still_has_delegate_helper_for_delete(self):
        # Le delegate lazy subsiste pour delete_media_file(variants=True).
        from forge_mvc_files import manager

        assert hasattr(manager, "_require_image_processing")

    def test_delegate_resolves_processing_functions(self):
        from forge_mvc_files.manager import _require_image_processing

        for name in (
            "verify_image_content",
            "generate_image_variants",
            "image_variant_relative_paths",
            "save_image_upload",
        ):
            resolved = _require_image_processing(name)
            assert callable(resolved), f"{name} doit être résoluble via le delegate."

    def test_manager_source_has_no_core_image_import(self):
        from forge_mvc_files import manager

        source = inspect.getsource(manager)
        assert "core.uploads.image" not in source, (
            "manager ne doit plus importer core.uploads.image (module déplacé)."
        )
