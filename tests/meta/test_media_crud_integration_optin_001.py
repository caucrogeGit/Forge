"""Garde-fou MEDIA-CRUD-INTEGRATION-OPTIN-001.

Vérifie que les générateurs CRUD et pages publiques n'émettent plus d'imports
applicatifs média depuis core.uploads, et ciblent désormais forge_mvc_media
pour les helpers applicatifs.

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
README = PROJECT_ROOT / "packages" / "forge-mvc-media" / "README.md"

# Helpers applicatifs qui doivent désormais être importés depuis forge_mvc_media
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
                "Les helpers applicatifs doivent venir de forge_mvc_media."
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
            "Les helpers applicatifs doivent venir de forge_mvc_media."
        )

    def test_public_list_no_core_uploads_list_media_for_entity(self):
        text = PUBLIC_LIST.read_text(encoding="utf-8")
        assert "core.uploads import list_media_for_entity" not in text, (
            "public_list.py génère encore 'from core.uploads import list_media_for_entity'. "
            "Les helpers applicatifs doivent venir de forge_mvc_media."
        )


class TestGeneratorsMentionForgeMediaOptIn:
    """Les générateurs ciblent forge_mvc_media pour les helpers applicatifs."""

    def test_controller_builder_mentions_forge_mvc_media(self):
        text = CONTROLLER_BUILDER.read_text(encoding="utf-8")
        assert "forge_mvc_media" in text, (
            "controller_builder.py ne mentionne pas forge_mvc_media. "
            "Les helpers applicatifs CRUD doivent être importés depuis forge_mvc_media."
        )

    def test_controller_builder_imports_attach_from_forge_mvc_media(self):
        text = CONTROLLER_BUILDER.read_text(encoding="utf-8")
        assert "forge_mvc_media import attach_media_to_entity" in text, (
            "controller_builder.py n'importe pas attach_media_to_entity depuis forge_mvc_media."
        )

    def test_public_list_mentions_forge_mvc_media(self):
        text = PUBLIC_LIST.read_text(encoding="utf-8")
        assert "forge_mvc_media" in text, (
            "public_list.py ne mentionne pas forge_mvc_media. "
            "Les helpers applicatifs publics doivent être importés depuis forge_mvc_media."
        )

    def test_public_list_imports_get_cover_from_forge_mvc_media(self):
        text = PUBLIC_LIST.read_text(encoding="utf-8")
        assert "forge_mvc_media import get_cover_media" in text, (
            "public_list.py n'importe pas get_cover_media depuis forge_mvc_media."
        )

    def test_controller_builder_still_uses_core_uploads_for_save_upload(self):
        text = CONTROLLER_BUILDER.read_text(encoding="utf-8")
        assert "core.uploads import save_upload" in text, (
            "controller_builder.py doit encore importer save_upload depuis core.uploads "
            "(primitive générique, pas un helper applicatif)."
        )


class TestShimsStillExist:
    """Les shims de compatibilité dans core/uploads ne sont pas supprimés."""

    def test_core_media_repository_shim_exists(self):
        assert CORE_REPO_SHIM.exists(), (
            "core/uploads/media_repository.py a été supprimé. "
            "Les shims de compatibilité doivent rester jusqu'à la fin de la dépréciation."
        )

    def test_core_media_gallery_shim_exists(self):
        assert CORE_GALLERY_SHIM.exists(), (
            "core/uploads/media_gallery.py a été supprimé. "
            "Les shims de compatibilité doivent rester jusqu'à la fin de la dépréciation."
        )

    def test_core_media_repository_shim_re_exports_forge_mvc_media(self):
        text = CORE_REPO_SHIM.read_text(encoding="utf-8")
        assert "forge_mvc_media" in text, (
            "core/uploads/media_repository.py n'est plus un shim forge_mvc_media."
        )

    def test_core_media_gallery_shim_re_exports_forge_mvc_media(self):
        text = CORE_GALLERY_SHIM.read_text(encoding="utf-8")
        assert "forge_mvc_media" in text, (
            "core/uploads/media_gallery.py n'est plus un shim forge_mvc_media."
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

    def test_readme_mentions_crud_integration_ticket(self):
        text = README.read_text(encoding="utf-8")
        assert "MEDIA-CRUD-INTEGRATION-OPTIN-001" in text, (
            "Le README de forge-mvc-media doit mentionner MEDIA-CRUD-INTEGRATION-OPTIN-001."
        )

    def test_readme_marks_crud_integration_as_livre(self):
        text = README.read_text(encoding="utf-8")
        # La dernière occurrence est celle de la table des tickets (source canonique)
        idx = text.rfind("MEDIA-CRUD-INTEGRATION-OPTIN-001")
        assert idx != -1
        bloc = text[idx:idx + 120]
        assert "livré" in bloc, (
            "MEDIA-CRUD-INTEGRATION-OPTIN-001 doit être marqué 'livré' dans le README "
            "(vérifier la table 'Tickets de référence')."
        )

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
