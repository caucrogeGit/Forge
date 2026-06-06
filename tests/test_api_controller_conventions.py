"""Tests — API-CONTROLLER-001 : conventions de contrôleurs JSON dans Forge."""

import json

from core.http import api_success, api_error
from core.http.helpers import api_success as api_success_helpers, api_error as api_error_helpers


# ---------------------------------------------------------------------------
# Imports et accessibilité
# ---------------------------------------------------------------------------


class TestImport:
    def test_api_success_depuis_core_http(self):
        assert callable(api_success)

    def test_api_error_depuis_core_http(self):
        assert callable(api_error)

    def test_meme_objet_api_success(self):
        assert api_success is api_success_helpers

    def test_meme_objet_api_error(self):
        assert api_error is api_error_helpers


# ---------------------------------------------------------------------------
# api_success — structure de la réponse
# ---------------------------------------------------------------------------


class TestApiSuccess:
    def test_champ_success_true(self):
        resp = api_success({"id": 1})
        body = json.loads(resp.body)
        assert body["success"] is True

    def test_champ_data_present(self):
        resp = api_success({"id": 1})
        body = json.loads(resp.body)
        assert "data" in body

    def test_champ_data_valeur(self):
        data = {"id": 1, "nom": "Alice"}
        resp = api_success(data)
        body = json.loads(resp.body)
        assert body["data"] == data

    def test_data_none_par_defaut(self):
        resp = api_success()
        body = json.loads(resp.body)
        assert body["data"] is None

    def test_data_none_explicite(self):
        resp = api_success(None)
        body = json.loads(resp.body)
        assert body["data"] is None

    def test_data_liste(self):
        resp = api_success([{"id": 1}, {"id": 2}])
        body = json.loads(resp.body)
        assert body["data"] == [{"id": 1}, {"id": 2}]

    def test_data_liste_vide(self):
        resp = api_success([])
        body = json.loads(resp.body)
        assert body["data"] == []

    def test_pas_de_champ_error(self):
        resp = api_success({"x": 1})
        body = json.loads(resp.body)
        assert "error" not in body

    def test_pas_de_meta_par_defaut(self):
        resp = api_success({"x": 1})
        body = json.loads(resp.body)
        assert "meta" not in body


# ---------------------------------------------------------------------------
# api_success — meta
# ---------------------------------------------------------------------------


class TestApiSuccessMeta:
    def test_meta_present_si_fourni(self):
        resp = api_success([], meta={"count": 0})
        body = json.loads(resp.body)
        assert "meta" in body

    def test_meta_valeur(self):
        resp = api_success([{"id": 1}], meta={"count": 1})
        body = json.loads(resp.body)
        assert body["meta"] == {"count": 1}

    def test_meta_none_absent(self):
        resp = api_success({}, meta=None)
        body = json.loads(resp.body)
        assert "meta" not in body

    def test_structure_complete_avec_meta(self):
        resp = api_success([1, 2], meta={"count": 2})
        body = json.loads(resp.body)
        assert body["success"] is True
        assert body["data"] == [1, 2]
        assert body["meta"] == {"count": 2}


# ---------------------------------------------------------------------------
# api_success — statuts HTTP
# ---------------------------------------------------------------------------


class TestApiSuccessStatut:
    def test_statut_200_par_defaut(self):
        assert api_success({}).status == 200

    def test_statut_201(self):
        assert api_success({"created": True}, status=201).status == 201

    def test_statut_personnalisable(self):
        assert api_success({}, status=204).status == 204


# ---------------------------------------------------------------------------
# api_error — structure de la réponse
# ---------------------------------------------------------------------------


class TestApiError:
    def test_champ_success_false(self):
        resp = api_error("Introuvable", status=404)
        body = json.loads(resp.body)
        assert body["success"] is False

    def test_champ_error_present(self):
        resp = api_error("Introuvable")
        body = json.loads(resp.body)
        assert "error" in body

    def test_champ_error_message(self):
        resp = api_error("Données invalides")
        body = json.loads(resp.body)
        assert body["error"]["message"] == "Données invalides"

    def test_champ_error_code_par_defaut(self):
        resp = api_error("Erreur")
        body = json.loads(resp.body)
        assert body["error"]["code"] == "error"

    def test_champ_error_code_personnalise(self):
        resp = api_error("Introuvable", code="not_found")
        body = json.loads(resp.body)
        assert body["error"]["code"] == "not_found"

    def test_pas_de_champ_data(self):
        resp = api_error("Erreur")
        body = json.loads(resp.body)
        assert "data" not in body

    def test_pas_de_details_par_defaut(self):
        resp = api_error("Erreur")
        body = json.loads(resp.body)
        assert "details" not in body["error"]


# ---------------------------------------------------------------------------
# api_error — details
# ---------------------------------------------------------------------------


class TestApiErrorDetails:
    def test_details_present_si_fourni(self):
        resp = api_error("Invalide", details={"email": "Obligatoire"})
        body = json.loads(resp.body)
        assert "details" in body["error"]

    def test_details_valeur(self):
        details = {"email": "Obligatoire", "nom": "Trop court"}
        resp = api_error("Invalide", details=details)
        body = json.loads(resp.body)
        assert body["error"]["details"] == details

    def test_details_none_absent(self):
        resp = api_error("Erreur", details=None)
        body = json.loads(resp.body)
        assert "details" not in body["error"]

    def test_structure_complete_avec_details(self):
        resp = api_error("Invalide", status=422, code="validation_error",
                         details={"email": "Obligatoire"})
        body = json.loads(resp.body)
        assert body["success"] is False
        assert body["error"]["code"] == "validation_error"
        assert body["error"]["message"] == "Invalide"
        assert body["error"]["details"] == {"email": "Obligatoire"}


# ---------------------------------------------------------------------------
# api_error — statuts HTTP
# ---------------------------------------------------------------------------


class TestApiErrorStatut:
    def test_statut_400_par_defaut(self):
        assert api_error("Erreur").status == 400

    def test_statut_404(self):
        assert api_error("Introuvable", status=404).status == 404

    def test_statut_401(self):
        assert api_error("Non authentifié", status=401).status == 401

    def test_statut_403(self):
        assert api_error("Interdit", status=403).status == 403

    def test_statut_500(self):
        assert api_error("Erreur serveur", status=500).status == 500

    def test_statut_422(self):
        assert api_error("Invalide", status=422).status == 422


# ---------------------------------------------------------------------------
# Content-Type pour les deux helpers
# ---------------------------------------------------------------------------


class TestContentType:
    def test_api_success_content_type(self):
        resp = api_success({"x": 1})
        assert resp.content_type == "application/json; charset=utf-8"

    def test_api_error_content_type(self):
        resp = api_error("Erreur")
        assert resp.content_type == "application/json; charset=utf-8"


# ---------------------------------------------------------------------------
# Corps JSON valide
# ---------------------------------------------------------------------------


class TestCorpsJSON:
    def test_api_success_body_est_bytes(self):
        assert isinstance(api_success({}).body, bytes)

    def test_api_error_body_est_bytes(self):
        assert isinstance(api_error("x").body, bytes)

    def test_api_success_json_valide(self):
        json.loads(api_success({"a": 1}).body)

    def test_api_error_json_valide(self):
        json.loads(api_error("msg").body)

    def test_utf8_success(self):
        resp = api_success({"msg": "héros"})
        assert "héros" in resp.body.decode("utf-8")

    def test_utf8_error(self):
        resp = api_error("Données invalides — champ manquant")
        assert "manquant" in resp.body.decode("utf-8")


# ---------------------------------------------------------------------------
# Convention contrôleur — pattern complet
# ---------------------------------------------------------------------------


class TestConventionControleur:
    def test_pattern_lecture_200(self):
        """Lecture réussie : success=True, data=..., status=200."""
        resp = api_success({"id": 1, "nom": "Contact"})
        assert resp.status == 200
        body = json.loads(resp.body)
        assert body["success"] is True
        assert body["data"]["id"] == 1

    def test_pattern_creation_201(self):
        """Création réussie : success=True, data=..., status=201."""
        resp = api_success({"id": 42}, status=201)
        assert resp.status == 201
        body = json.loads(resp.body)
        assert body["success"] is True

    def test_pattern_liste_avec_meta(self):
        """Liste paginée : success=True, data=[...], meta={count}."""
        items = [{"id": 1}, {"id": 2}]
        resp = api_success(items, meta={"count": 2})
        body = json.loads(resp.body)
        assert body["success"] is True
        assert len(body["data"]) == 2
        assert body["meta"]["count"] == 2

    def test_pattern_not_found_404(self):
        """Ressource introuvable : success=False, error.code=not_found."""
        resp = api_error("Ressource introuvable", status=404, code="not_found")
        assert resp.status == 404
        body = json.loads(resp.body)
        assert body["success"] is False
        assert body["error"]["code"] == "not_found"

    def test_pattern_validation_422(self):
        """Validation : success=False, error.code=validation_error, details."""
        resp = api_error("Données invalides", status=422,
                         code="validation_error",
                         details={"email": "Champ obligatoire"})
        assert resp.status == 422
        body = json.loads(resp.body)
        assert body["error"]["details"]["email"] == "Champ obligatoire"

    def test_pattern_forbidden_403(self):
        """Accès interdit : success=False, error.code=forbidden."""
        resp = api_error("Accès interdit", status=403, code="forbidden")
        assert resp.status == 403
        body = json.loads(resp.body)
        assert body["success"] is False

    def test_pattern_unauthorized_401(self):
        """Non authentifié : success=False, error.code=unauthorized."""
        resp = api_error("Non authentifié", status=401, code="unauthorized")
        assert resp.status == 401
        body = json.loads(resp.body)
        assert body["success"] is False


# ---------------------------------------------------------------------------
# Intégration avec Application.dispatch()
# ---------------------------------------------------------------------------


class TestIntegrationDispatch:
    def test_dispatch_retourne_json_depuis_handler(self):
        from core.app.application import Application
        from core.http.router import Router
        from tests.fake_request import FakeRequest

        router = Router()
        router.add("GET", "/api/status", lambda r: api_success({"ok": True}), public=True)
        app = Application(router, middlewares=[])
        req = FakeRequest("GET", "/api/status")
        resp = app.dispatch(req)
        assert resp.status == 200
        assert "application/json" in resp.content_type
        body = json.loads(resp.body)
        assert body["success"] is True

    def test_dispatch_retourne_erreur_json(self):
        from core.app.application import Application
        from core.http.router import Router
        from tests.fake_request import FakeRequest

        router = Router()
        router.add("GET", "/api/missing",
                   lambda r: api_error("Introuvable", status=404, code="not_found"),
                   public=True)
        app = Application(router, middlewares=[])
        req = FakeRequest("GET", "/api/missing")
        resp = app.dispatch(req)
        assert resp.status == 404
        body = json.loads(resp.body)
        assert body["success"] is False
        assert body["error"]["code"] == "not_found"
