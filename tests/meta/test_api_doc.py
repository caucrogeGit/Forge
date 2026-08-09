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

    def test_json_error(self):
        """ADR-088 : la page enseigne `json_error`, fabrique unique des erreurs."""
        assert "json_error" in _doc()

    def test_la_forme_plate_est_montree(self):
        """La forme du contrat doit apparaître, pas seulement le nom de la fabrique."""
        assert '{"error": "not_found"}' in _doc()


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
    def test_primitive_bearer(self):
        """ADR-088 : la page enseigne `is_bearer_authorized`, seule primitive.

        Elle enseignait `@require_api_token`, décorateur d'une seconde
        implémentation Bearer du cœur, retirée par l'ADR-088 : elle distinguait
        trois causes de refus, donc renseignait l'attaquant sur l'étape franchie.
        """
        assert "is_bearer_authorized" in _doc()
        assert "require_api_token" not in _doc()

    def test_authorization_bearer(self):
        assert "Authorization" in _doc() and "Bearer" in _doc()

    def test_api_token_env(self):
        assert "API_TOKEN" in _doc()


# ---------------------------------------------------------------------------
# Convention JSON structurée mentionnée
# ---------------------------------------------------------------------------


class TestConventionJson:
    """ADR-088 : la page enseigne la forme plate, plus l'enveloppe.

    Ces trois contrôles exigeaient auparavant `"success": true` et
    `"success": false` dans la page. L'enveloppe ayant été retirée, ils
    vérifient désormais la forme retenue, et **l'absence** de l'ancienne dans
    les exemples, sans quoi la page enseignerait deux contrats à la fois.
    """

    def test_structure_succes(self):
        doc = _doc()
        assert "rend **la ressource**" in doc or "rend la ressource" in doc

    def test_structure_erreur(self):
        assert '{"error": "not_found"}' in _doc()

    def test_l_enveloppe_n_est_plus_enseignee(self):
        doc = _doc()
        assert '"success": true' not in doc
        assert '"success": false' not in doc

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
