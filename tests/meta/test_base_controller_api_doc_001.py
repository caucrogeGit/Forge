"""Garde-fou BASE-CONTROLLER-API-DOC-001.

Vérifie que docs/reference/api.md documente officiellement l'API publique
de BaseController avec les bonnes signatures, classifications et alternatives.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parents[2]
# Contrat déplacé : la surface BaseController est documentée sur sa page dédiée
# (DOCS-API-CATALOG-003), api.md n'étant plus qu'un catalogue de liens.
API_DOC = PROJECT_ROOT / "core" / "mvc" / "docs" / "base_controller.md"


@pytest.fixture(scope="module")
def doc() -> str:
    assert API_DOC.exists(), f"docs/reference/api.md introuvable : {API_DOC}"
    return API_DOC.read_text(encoding="utf-8")


class TestDocExists:

    def test_fichier_existe(self):
        assert API_DOC.exists()

    def test_fichier_non_vide(self, doc):
        assert len(doc) > 5000

    def test_ticket_reference(self, doc):
        assert "BASE-CONTROLLER-API-DOC-001" in doc

    def test_section_base_controller(self, doc):
        assert "BaseController" in doc
        assert "coremvccontroller" in doc


class TestMethodesCanoniques:

    def test_render_present(self, doc):
        assert "render" in doc

    def test_redirect_present(self, doc):
        assert "redirect" in doc

    def test_redirect_with_flash_present(self, doc):
        assert "redirect_with_flash" in doc

    def test_redirect_to_route_present(self, doc):
        assert "redirect_to_route" in doc

    def test_not_found_present(self, doc):
        assert "not_found" in doc

    def test_bad_request_present(self, doc):
        assert "bad_request" in doc

    def test_forbidden_present(self, doc):
        assert "forbidden" in doc

    def test_validation_error_present(self, doc):
        assert "validation_error" in doc

    def test_server_error_present(self, doc):
        assert "server_error" in doc

    def test_include_present(self, doc):
        assert "include" in doc

    def test_json_present(self, doc):
        assert "json" in doc

    def test_body_present(self, doc):
        assert "body" in doc

    def test_json_body_present(self, doc):
        assert "json_body" in doc

    def test_render_form_present(self, doc):
        assert "render_form" in doc

    def test_form_context_present(self, doc):
        assert "form_context" in doc


class TestSignaturesExactes:

    def test_render_signature(self, doc):
        assert "raw=False" in doc

    def test_redirect_signature(self, doc):
        assert 'level="success"' in doc

    def test_redirect_with_flash_signature(self, doc):
        assert "redirect_with_flash(request, location, message" in doc

    def test_validation_error_signature(self, doc):
        assert 'template="errors/422.html"' in doc

    def test_render_form_signature(self, doc):
        assert 'erreurs=""' in doc

    def test_form_context_signature(self, doc):
        assert "form_context(request, data, erreurs" in doc


class TestClassificationMethodes:

    def test_section_canoniques(self, doc):
        lower = doc.lower()
        assert "canonique" in lower

    def test_section_legacy(self, doc):
        assert "LEGACY" in doc or "legacy" in doc.lower()

    def test_section_surveiller(self, doc):
        lower = doc.lower()
        assert "surveiller" in lower or "À_SURVEILLER" in doc

    def test_18_methodes_annoncees(self, doc):
        assert "18" in doc


class TestCurrentUserLegacy:

    def test_current_user_present(self, doc):
        assert "current_user" in doc

    def test_current_user_marque_legacy(self, doc):
        assert "LEGACY" in doc

    def test_deprecation_mentionnee(self, doc):
        assert "DeprecationWarning" in doc or "déprécié" in doc.lower() or "depreci" in doc.lower()

    def test_alternative_canonique_presente(self, doc):
        assert "get_authenticated_user_id" in doc


class TestAuditReference:

    def test_audit_surface_reference(self, doc):
        assert "base-controller-surface-audit-001" in doc

    def test_set_flash_surveiller(self, doc):
        lower = doc.lower()
        assert "set_flash" in lower

    def test_csrf_token_surveiller(self, doc):
        assert "csrf_token" in doc

    def test_core_security_session_mentionne(self, doc):
        assert "core.security.session" in doc
