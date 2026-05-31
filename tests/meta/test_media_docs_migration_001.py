"""Garde-fou MEDIA-DOCS-MIGRATION-001.

Vérifie que la documentation média reflète la frontière core / opt-in :
- forge_mvc_media est mentionné dans les docs médias ;
- core.uploads n'est plus présenté comme source des helpers applicatifs ;
- la frontière core / opt-in est documentée ;
- forge-mvc-media est présenté comme source-only, non publié sur PyPI ;
- les shims de compatibilité sont documentés comme temporaires ;
- les primitives core restent documentées ;
- la roadmap marque MEDIA-DOCS-MIGRATION-001 livré.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent

MEDIA_DOC = PROJECT_ROOT / "docs" / "features" / "media.md"
FRONT_DOC = PROJECT_ROOT / "docs" / "features" / "front.md"
API_DOC = PROJECT_ROOT / "docs" / "reference" / "api.md"
ROADMAP = PROJECT_ROOT / "docs" / "roadmap" / "forge-roadmap.md"
README = PROJECT_ROOT / "packages" / "forge-mvc-media" / "README.md"

# Helpers applicatifs qui ne doivent plus être documentés comme venant de core.uploads
_APPLICATIVE_HELPERS = [
    "attach_media_to_entity",
    "list_media_for_entity",
    "get_cover_media",
    "get_media_gallery",
    "delete_media",
    "update_media_alt_text",
    "update_media_position",
    "media_url",
]


class TestMediaDocMentionsOptIn:
    """La documentation média mentionne forge_mvc_media."""

    def test_media_md_mentions_forge_mvc_media(self):
        text = MEDIA_DOC.read_text(encoding="utf-8")
        assert "forge_mvc_media" in text, (
            "docs/features/media.md doit mentionner forge_mvc_media."
        )

    def test_media_md_mentions_frontier(self):
        text = MEDIA_DOC.read_text(encoding="utf-8")
        assert "core.uploads" in text and "forge_mvc_media" in text, (
            "docs/features/media.md doit distinguer core.uploads et forge_mvc_media."
        )

    def test_api_md_mentions_forge_mvc_media(self):
        text = API_DOC.read_text(encoding="utf-8")
        assert "forge_mvc_media" in text, (
            "docs/reference/api.md doit mentionner forge_mvc_media."
        )

    def test_front_md_uses_forge_mvc_media_for_helpers(self):
        text = FRONT_DOC.read_text(encoding="utf-8")
        assert "forge_mvc_media" in text, (
            "docs/features/front.md doit mentionner forge_mvc_media pour les helpers publics."
        )

    def test_front_md_no_longer_says_core_uploads_for_helpers(self):
        text = FRONT_DOC.read_text(encoding="utf-8")
        assert "issus de `core.uploads`" not in text, (
            "docs/features/front.md ne doit plus présenter les helpers comme issus de core.uploads."
        )


class TestApiDocSeparatesGenericFromApplicative:
    """L'API reference distingue les primitives core et les helpers applicatifs."""

    def test_api_md_has_forge_mvc_media_section(self):
        text = API_DOC.read_text(encoding="utf-8")
        assert "forge_mvc_media" in text and "opt-in" in text.lower(), (
            "docs/reference/api.md doit avoir une section forge_mvc_media opt-in."
        )

    def test_api_md_core_uploads_section_does_not_list_applicative_helpers(self):
        text = API_DOC.read_text(encoding="utf-8")
        # La table Gestionnaire core.uploads ne doit plus lister les helpers applicatifs
        # Vérification : attach_media_to_entity ne doit pas apparaître dans
        # le contexte "core.uploads" comme API principale (table Gestionnaire)
        core_section_start = text.find('<summary><code>core.uploads</code>')
        core_section_end = text.find('</details>', core_section_start)
        assert core_section_start != -1
        core_section = text[core_section_start:core_section_end]
        assert "attach_media_to_entity" not in core_section, (
            "La section core.uploads dans api.md ne doit plus lister attach_media_to_entity "
            "comme API principale de core.uploads."
        )

    def test_api_md_crud_section_uses_forge_mvc_media(self):
        text = API_DOC.read_text(encoding="utf-8")
        assert "forge_mvc_media" in text[text.find("Génération CRUD media"):], (
            "La section CRUD media dans api.md doit mentionner forge_mvc_media."
        )

    def test_api_md_modules_lists_forge_mvc_media(self):
        text = API_DOC.read_text(encoding="utf-8")
        assert "forge-mvc-media" in text[text.find("Opt-ins officiels"):], (
            "La section Opt-ins officiels doit inclure forge-mvc-media."
        )


class TestSourceOnlyAndPyPIStatus:
    """forge-mvc-media est publié sur PyPI depuis `1.0.0-beta.9` au statut Alpha.

    L'historique de la phase source-only reste consigné dans le README via le
    tableau des tickets (`MEDIA-EXTRACT-PACKAGE-SCAFFOLD-001`, etc.) — c'est
    légitime et préservé. Le présent garde-fou vérifie en revanche que la
    documentation utilisateur active reflète l'état réel : publication PyPI.
    """

    def test_media_md_mentions_pypi_publication(self):
        text = MEDIA_DOC.read_text(encoding="utf-8")
        assert "publié sur PyPI" in text or "publié PyPI" in text, (
            "docs/features/media.md doit indiquer que forge-mvc-media est publié sur PyPI "
            "depuis `1.0.0-beta.9` (DOCS-OPTINS-PYPI-BETA9-SWEEP-001)."
        )

    def test_readme_mentions_pypi_publication(self):
        text = README.read_text(encoding="utf-8")
        assert "publié sur PyPI" in text or "Publié sur PyPI" in text, (
            "README forge-mvc-media doit indiquer la publication PyPI depuis `1.0.0-beta.9`."
        )

    def test_readme_does_not_advertise_pip_install_pypi(self):
        text = README.read_text(encoding="utf-8")
        # Ne doit pas promouvoir "pip install forge-mvc-media" sans avertissement
        assert "pip install forge-mvc-media" not in text, (
            "README ne doit pas présenter 'pip install forge-mvc-media' comme commande disponible."
        )


class TestShimsDocumented:
    """Les shims de compatibilité sont documentés comme temporaires."""

    def test_media_md_mentions_shims_as_temporary(self):
        text = MEDIA_DOC.read_text(encoding="utf-8")
        assert "shims" in text or "compatibilité" in text, (
            "docs/features/media.md doit mentionner les shims de compatibilité."
        )

    def test_api_md_mentions_shims_as_deprecation(self):
        text = API_DOC.read_text(encoding="utf-8")
        assert "DeprecationWarning" in text or "shims" in text or "compatibilité" in text.lower(), (
            "docs/reference/api.md doit mentionner les shims de compatibilité dans la section forge_mvc_media."
        )


class TestCorePrimitivesStillDocumented:
    """Les primitives génériques core restent documentées."""

    def test_media_md_mentions_save_upload(self):
        text = MEDIA_DOC.read_text(encoding="utf-8")
        assert "save_upload" in text, (
            "docs/features/media.md doit toujours documenter save_upload (primitive core)."
        )

    def test_api_md_core_uploads_has_save_upload(self):
        text = API_DOC.read_text(encoding="utf-8")
        core_section_start = text.find('<summary><code>core.uploads</code>')
        core_section_end = text.find('</details>', core_section_start)
        core_section = text[core_section_start:core_section_end]
        assert "save_upload" in core_section, (
            "La section core.uploads dans api.md doit toujours documenter save_upload."
        )


class TestRoadmap:

    def test_roadmap_mentions_docs_migration_ticket(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "MEDIA-DOCS-MIGRATION-001" in text, (
            "La roadmap doit mentionner MEDIA-DOCS-MIGRATION-001."
        )

    def test_roadmap_marks_docs_migration_as_livre(self):
        text = ROADMAP.read_text(encoding="utf-8")
        idx = text.find("MEDIA-DOCS-MIGRATION-001")
        assert idx != -1
        bloc = text[idx:idx + 140]
        assert "livré" in bloc, (
            "MEDIA-DOCS-MIGRATION-001 doit être marqué 'livré' dans la roadmap."
        )

    def test_roadmap_phase_11_all_tickets_livre(self):
        text = ROADMAP.read_text(encoding="utf-8")
        tickets = [
            "MEDIA-CORE-BOUNDARY-AUDIT-001",
            "MEDIA-EXTRACT-PACKAGE-SCAFFOLD-001",
            "MEDIA-REPOSITORY-MOVE-001",
            "MEDIA-CRUD-INTEGRATION-OPTIN-001",
            "MEDIA-DOCS-MIGRATION-001",
        ]
        for ticket in tickets:
            idx = text.find(ticket)
            assert idx != -1, f"Ticket {ticket} absent de la roadmap."
            bloc = text[idx:idx + 140]
            assert "livré" in bloc, (
                f"Ticket {ticket} doit être marqué 'livré' dans la roadmap."
            )
