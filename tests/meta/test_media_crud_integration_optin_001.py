"""Garde-fou MEDIA-CRUD-INTEGRATION-OPTIN-001.

Vérifie que les générateurs CRUD et pages publiques n'émettent plus d'imports
applicatifs média depuis core.uploads, et ciblent l'opt-in pour les helpers
applicatifs.

Depuis CLI-CRUD-IMAGES-RENAME-001 (ADR-018), cet opt-in est `forge_mvc_images`
(propriétaire de tout l'image) ; `forge_mvc_media` n'est plus qu'un shim
transitoire. Les générateurs émettent donc `from forge_mvc_images import ...`.

Ne bloque pas les imports core.uploads pour les primitives génériques
(save_upload, delete_media_file, serve_media_file…).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent

CONTROLLER_BUILDER = PROJECT_ROOT / "forge_cli" / "entities" / "crud" / "controller_builder.py"
PUBLIC_LIST = PROJECT_ROOT / "forge_cli" / "public_list.py"
CORE_REPO_SHIM = PROJECT_ROOT / "core" / "uploads" / "media_repository.py"
CORE_GALLERY_SHIM = PROJECT_ROOT / "core" / "uploads" / "media_gallery.py"
ROOT_PYPROJECT = PROJECT_ROOT / "pyproject.toml"
ROADMAP = PROJECT_ROOT / "docs" / "roadmap" / "forge-roadmap.md"

# Helpers applicatifs qui doivent désormais être importés depuis forge_mvc_images
_APPLICATIVE_HELPERS = [
    "attach_media_to_entity",
    "list_media_for_entity",
    "get_cover_media",
    "delete_media",
    "update_media_alt_text",
    "update_media_position",
]


class TestGeneratorsCrudNoApplicativeImportFromCore:
    """Les générateurs CRUD ne génèrent plus d'imports applicatifs depuis core.uploads."""

    def test_controller_builder_no_core_uploads_attach_media_to_entity(self):
        text = CONTROLLER_BUILDER.read_text(encoding="utf-8")
        for helper in _APPLICATIVE_HELPERS:
            assert f"core.uploads import {helper}" not in text, (
                f"controller_builder.py génère encore 'from core.uploads import {helper}'. "
                "Les helpers applicatifs doivent venir de forge_mvc_images."
            )

    def test_controller_builder_no_single_line_core_uploads_with_attach(self):
        text = CONTROLLER_BUILDER.read_text(encoding="utf-8")
        # La chaîne littérale de l'ancienne ligne d'import groupé ne doit plus exister
        assert "attach_media_to_entity, delete_media, get_cover_media, list_media_for_entity, save_upload" not in text, (
            "controller_builder.py contient encore l'ancienne ligne d'import groupé depuis core.uploads."
        )

    def test_public_list_no_core_uploads_get_cover_media(self):
        text = PUBLIC_LIST.read_text(encoding="utf-8")
        assert "core.uploads import get_cover_media" not in text, (
            "public_list.py génère encore 'from core.uploads import get_cover_media'. "
            "Les helpers applicatifs doivent venir de forge_mvc_images."
        )

    def test_public_list_no_core_uploads_list_media_for_entity(self):
        text = PUBLIC_LIST.read_text(encoding="utf-8")
        assert "core.uploads import list_media_for_entity" not in text, (
            "public_list.py génère encore 'from core.uploads import list_media_for_entity'. "
            "Les helpers applicatifs doivent venir de forge_mvc_images."
        )


class TestGeneratorsMentionForgeImagesOptIn:
    """Les générateurs ciblent forge_mvc_images pour les helpers applicatifs.

    CLI-CRUD-IMAGES-RENAME-001 (ADR-018) : les helpers applicatifs proviennent
    désormais de forge_mvc_images (et non plus de forge_mvc_media, devenu shim).
    """

    def test_controller_builder_mentions_forge_mvc_images(self):
        text = CONTROLLER_BUILDER.read_text(encoding="utf-8")
        assert "forge_mvc_images" in text, (
            "controller_builder.py ne mentionne pas forge_mvc_images. "
            "Les helpers applicatifs CRUD doivent être importés depuis forge_mvc_images."
        )

    def test_controller_builder_imports_attach_from_forge_mvc_images(self):
        text = CONTROLLER_BUILDER.read_text(encoding="utf-8")
        # CORE-SAVEUPLOAD-GENERIC-CLEANUP : l'import forge_mvc_images est désormais
        # construit dynamiquement (`"from forge_mvc_images import " + ", ".join(...)`).
        assert "from forge_mvc_images import " in text, (
            "controller_builder.py doit générer un import depuis forge_mvc_images."
        )
        assert '"attach_media_to_entity"' in text, (
            "controller_builder.py doit inclure attach_media_to_entity dans les helpers importés."
        )

    def test_controller_builder_generates_save_image_upload_for_images(self):
        # Les champs image passent par forge_mvc_images.save_image_upload
        # (et non le save_upload générique du core).
        text = CONTROLLER_BUILDER.read_text(encoding="utf-8")
        assert "save_image_upload" in text, (
            "controller_builder.py doit générer des appels save_image_upload "
            "pour les champs image (CORE-SAVEUPLOAD-GENERIC-CLEANUP)."
        )

    def test_controller_builder_no_longer_targets_forge_mvc_media(self):
        text = CONTROLLER_BUILDER.read_text(encoding="utf-8")
        assert "forge_mvc_media" not in text, (
            "controller_builder.py ne doit plus cibler forge_mvc_media "
            "(shim transitoire) ; importer depuis forge_mvc_images."
        )

    def test_public_list_mentions_forge_mvc_images(self):
        text = PUBLIC_LIST.read_text(encoding="utf-8")
        assert "forge_mvc_images" in text, (
            "public_list.py ne mentionne pas forge_mvc_images. "
            "Les helpers applicatifs publics doivent être importés depuis forge_mvc_images."
        )

    def test_public_list_imports_get_cover_from_forge_mvc_images(self):
        text = PUBLIC_LIST.read_text(encoding="utf-8")
        assert "forge_mvc_images import get_cover_media" in text, (
            "public_list.py n'importe pas get_cover_media depuis forge_mvc_images."
        )

    def test_public_list_no_longer_targets_forge_mvc_media(self):
        text = PUBLIC_LIST.read_text(encoding="utf-8")
        assert "forge_mvc_media" not in text, (
            "public_list.py ne doit plus cibler forge_mvc_media (shim transitoire)."
        )

    def test_controller_builder_uses_forge_mvc_files_for_save_upload(self):
        # FILES-CLI-RENAME-001 (ADR-019) : l'upload générique (fichiers) vient
        # désormais de forge-mvc-files, plus du core.
        text = CONTROLLER_BUILDER.read_text(encoding="utf-8")
        assert "forge_mvc_files import save_upload" in text, (
            "controller_builder.py doit générer 'from forge_mvc_files import "
            "save_upload' pour les champs fichier (upload extrait du core)."
        )
        assert "core.uploads import save_upload" not in text, (
            "controller_builder.py ne doit plus importer save_upload depuis core.uploads."
        )


class TestShimsRemoved:
    """Les shims de compatibilité dans core/uploads ont été supprimés (MEDIA-SHIMS-REMOVE-001)."""

    def test_core_media_repository_shim_absent(self):
        assert not CORE_REPO_SHIM.exists(), (
            "core/uploads/media_repository.py est présent mais doit être absent. "
            "Le shim a été supprimé dans MEDIA-SHIMS-REMOVE-001."
        )

    def test_core_media_gallery_shim_absent(self):
        assert not CORE_GALLERY_SHIM.exists(), (
            "core/uploads/media_gallery.py est présent mais doit être absent. "
            "Le shim a été supprimé dans MEDIA-SHIMS-REMOVE-001."
        )


class TestNoDependencyOnOptIn:
    """Le core ne dépend pas de forge-mvc-media comme dépendance obligatoire."""

    def test_root_pyproject_does_not_depend_on_forge_mvc_media(self):
        lines = ROOT_PYPROJECT.read_text(encoding="utf-8").splitlines()
        active_lines = [l for l in lines if not l.strip().startswith("#")]
        active_text = "\n".join(active_lines)
        assert "forge-mvc-media" not in active_text, (
            "Le pyproject.toml racine dépend de forge-mvc-media (ligne active, hors commentaires). "
            "Ce module doit rester opt-in, non publié, non requis par le core."
        )


class TestReadmeAndRoadmap:
    # REMOVE-MEDIA-PKG : le README de forge-mvc-media a été supprimé avec le
    # paquet ; les tests qui le lisaient sont retirés. La roadmap reste la
    # source canonique de l'historique des tickets.

    def test_roadmap_mentions_crud_integration_ticket(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "MEDIA-CRUD-INTEGRATION-OPTIN-001" in text, (
            "La roadmap doit mentionner MEDIA-CRUD-INTEGRATION-OPTIN-001."
        )

    def test_roadmap_marks_crud_integration_as_livre(self):
        text = ROADMAP.read_text(encoding="utf-8")
        idx = text.find("MEDIA-CRUD-INTEGRATION-OPTIN-001")
        assert idx != -1
        bloc = text[idx:idx + 140]
        assert "livré" in bloc, (
            "MEDIA-CRUD-INTEGRATION-OPTIN-001 doit être marqué 'livré' dans la roadmap."
        )
