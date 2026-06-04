"""Garde-fou IMAGES-MOVE-APPLICATIVE-001 (ADR-018).

Vérifie le rapatriement de la couche médias applicative (repository SQL +
galerie/couverture) depuis ``forge-mvc-media`` vers ``forge-mvc-images`` :

- ``forge_mvc_images`` contient désormais ``media_repository`` (logique SQL) et
  ``media_gallery`` (galerie/couverture) et expose toute l'API applicative ;
- ``forge-mvc-media`` a été entièrement supprimé au ticket
  ``REMOVE-MEDIA-PKG-001`` : plus de paquet, plus de shim, plus d'import
  ``forge_mvc_media`` possible (voir ``TestMediaPackageRemoved``).

Les tests média fonctionnels et les générateurs CRUD importent désormais
``forge_mvc_images``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
IMG_PKG = PROJECT_ROOT / "packages" / "forge-mvc-images" / "forge_mvc_images"
MEDIA_PKG = PROJECT_ROOT / "packages" / "forge-mvc-media" / "forge_mvc_media"

APPLICATIVE_API = (
    "attach_media_to_entity",
    "create_media_record",
    "delete_media",
    "delete_media_record",
    "get_cover_media",
    "get_media_gallery",
    "get_media_record",
    "list_media_for_entity",
    "media_url",
    "update_media_alt_text",
    "update_media_position",
)


class TestApplicativeCodeInImages:
    """Le code applicatif réel vit dans forge_mvc_images."""

    def test_repository_module_present(self):
        assert (IMG_PKG / "media_repository.py").exists()

    def test_gallery_module_present(self):
        assert (IMG_PKG / "media_gallery.py").exists()

    def test_repository_has_sql(self):
        text = (IMG_PKG / "media_repository.py").read_text(encoding="utf-8")
        assert "INSERT INTO media" in text

    def test_gallery_has_logic(self):
        text = (IMG_PKG / "media_gallery.py").read_text(encoding="utf-8")
        assert "def get_media_gallery" in text

    @pytest.mark.parametrize("name", APPLICATIVE_API)
    def test_optin_exposes_applicative_api(self, name: str):
        import forge_mvc_images

        assert hasattr(forge_mvc_images, name), (
            f"forge_mvc_images doit exposer '{name}' (couche applicative)."
        )

    def test_all_lists_applicative_api(self):
        import forge_mvc_images

        missing = [n for n in APPLICATIVE_API if n not in forge_mvc_images.__all__]
        assert not missing, f"forge_mvc_images.__all__ doit lister : {missing}"


class TestMediaPackageRemoved:
    """REMOVE-MEDIA-PKG : forge-mvc-media supprimé (remplacé par forge-mvc-images)."""

    def test_media_package_dir_absent(self):
        assert not MEDIA_PKG.exists(), (
            "packages/forge-mvc-media doit avoir été supprimé "
            "(remplacé par forge-mvc-images)."
        )

    def test_forge_mvc_media_not_importable(self):
        import importlib

        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("forge_mvc_media")


class TestCoreReexportsFromImages:
    """L'API applicative s'importe depuis forge_mvc_images (plus via le core)."""

    def test_core_uploads_removed_no_reexport(self):
        # CORE-DROP-UPLOADS-001 (ADR-019) : core/uploads a été supprimé ; il n'y
        # a plus de réexport applicatif dans le core. Les apps importent
        # directement depuis forge_mvc_images.
        assert not (PROJECT_ROOT / "core" / "uploads").exists()

    def test_applicative_api_lives_in_images(self):
        import forge_mvc_images

        for name in ("attach_media_to_entity", "get_media_gallery", "delete_media"):
            assert hasattr(forge_mvc_images, name)
