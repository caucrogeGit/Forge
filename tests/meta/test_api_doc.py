"""Tests — API-DOC-001 : documentation API JSON légère."""

import pathlib
import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]

DOC_PATH = pathlib.Path("docs/reference/api-json.md")
MKDOCS_PATH = pathlib.Path("mkdocs.yml")


def _doc():
    return DOC_PATH.read_text(encoding="utf-8")


def _mkdocs():
    return MKDOCS_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Existence
# ---------------------------------------------------------------------------


class TestExistence:
    def test_fichier_existe(self):
        assert DOC_PATH.exists(), "docs/reference/api-json.md doit exister"

    def test_fichier_non_vide(self):
        assert len(_doc()) > 500


# ---------------------------------------------------------------------------
# Présence dans mkdocs.yml
# ---------------------------------------------------------------------------


class TestMkdocs:
    def test_api_json_dans_mkdocs(self):
        assert "api-json.md" in _mkdocs()


# ---------------------------------------------------------------------------
# Helpers JSON mentionnés
# ---------------------------------------------------------------------------


class TestHelpersMentionnes:
    def test_json_response(self):
        assert "json_response" in _doc()

    def test_api_success(self):
        assert "api_success" in _doc()

    def test_api_error(self):
        assert "api_error" in _doc()


# ---------------------------------------------------------------------------
# Convention routes API mentionnée
# ---------------------------------------------------------------------------


class TestConventionRoutes:
    def test_api_routes_py(self):
        assert "mvc/api_routes.py" in _doc() or "api_routes.py" in _doc()

    def test_register_api_routes(self):
        assert "register_api_routes" in _doc()


# ---------------------------------------------------------------------------
# Auth API mentionnée
# ---------------------------------------------------------------------------


class TestAuthApi:
    def test_require_api_token(self):
        assert "require_api_token" in _doc()

    def test_authorization_bearer(self):
        assert "Authorization" in _doc() and "Bearer" in _doc()

    def test_api_token_env(self):
        assert "API_TOKEN" in _doc()


# ---------------------------------------------------------------------------
# Convention JSON structurée mentionnée
# ---------------------------------------------------------------------------


class TestConventionJson:
    def test_success_data(self):
        assert '"success"' in _doc() or "success" in _doc()

    def test_structure_succes(self):
        doc = _doc()
        assert '"success": true' in doc or "success: true" in doc or "success" in doc

    def test_structure_erreur(self):
        doc = _doc()
        assert '"success": false' in doc or "success: false" in doc

    def test_content_type_json(self):
        assert "application/json" in _doc()


# ---------------------------------------------------------------------------
# Section limites présente
# ---------------------------------------------------------------------------


class TestSectionLimites:
    def test_section_limites(self):
        doc = _doc()
        assert "Limites" in doc or "limites" in doc

    def test_jwt_mentionne(self):
        assert "JWT" in _doc() or "jwt" in _doc()

    def test_pagination_mentionnee(self):
        assert "pagination" in _doc().lower()


# ---------------------------------------------------------------------------
# Roadmap — API-DOC-001 livré
# ---------------------------------------------------------------------------


class TestRoadmap:
    def test_api_doc_001_livre(self):
        roadmap = pathlib.Path("docs/roadmap/forge-roadmap.md").read_text(encoding="utf-8")
        assert "API-DOC-001" in roadmap
        idx = roadmap.index("API-DOC-001")
        bloc = roadmap[idx: idx + 60]
        assert "livré" in bloc or "terminé" in bloc or "close" in roadmap[idx: idx + 200]
