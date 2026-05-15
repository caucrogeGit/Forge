"""Tests unitaires — API-JSON-001 : réponse JSON simple dans Forge."""

import json
import pytest

from core.http.helpers import json_response
from core.http import json_response as json_response_from_package


# ---------------------------------------------------------------------------
# Import et accessibilité
# ---------------------------------------------------------------------------


class TestImport:
    def test_import_depuis_helpers(self):
        assert callable(json_response)

    def test_import_depuis_core_http(self):
        assert callable(json_response_from_package)

    def test_meme_objet(self):
        assert json_response is json_response_from_package


# ---------------------------------------------------------------------------
# Types de données sérialisables
# ---------------------------------------------------------------------------


class TestTypesDonnees:
    def test_dict(self):
        resp = json_response({"status": "ok"})
        assert json.loads(resp.body) == {"status": "ok"}

    def test_list(self):
        resp = json_response([1, 2, 3])
        assert json.loads(resp.body) == [1, 2, 3]

    def test_none(self):
        resp = json_response(None)
        assert json.loads(resp.body) is None

    def test_entier(self):
        resp = json_response(42)
        assert json.loads(resp.body) == 42

    def test_flottant(self):
        resp = json_response(3.14)
        assert json.loads(resp.body) == pytest.approx(3.14)

    def test_bool_true(self):
        resp = json_response(True)
        assert json.loads(resp.body) is True

    def test_bool_false(self):
        resp = json_response(False)
        assert json.loads(resp.body) is False

    def test_chaine(self):
        resp = json_response("bonjour")
        assert json.loads(resp.body) == "bonjour"

    def test_dict_imbriqué(self):
        data = {"user": {"id": 1, "nom": "Alice"}, "actif": True}
        resp = json_response(data)
        assert json.loads(resp.body) == data

    def test_liste_de_dicts(self):
        data = [{"id": 1}, {"id": 2}]
        resp = json_response(data)
        assert json.loads(resp.body) == data

    def test_dict_vide(self):
        resp = json_response({})
        assert json.loads(resp.body) == {}

    def test_liste_vide(self):
        resp = json_response([])
        assert json.loads(resp.body) == []


# ---------------------------------------------------------------------------
# Statut HTTP
# ---------------------------------------------------------------------------


class TestStatutHTTP:
    def test_statut_par_defaut_200(self):
        resp = json_response({"ok": True})
        assert resp.status == 200

    def test_statut_201(self):
        resp = json_response({"created": True}, status=201)
        assert resp.status == 201

    def test_statut_400(self):
        resp = json_response({"erreur": "invalide"}, status=400)
        assert resp.status == 400

    def test_statut_404(self):
        resp = json_response({"erreur": "introuvable"}, status=404)
        assert resp.status == 404

    def test_statut_500(self):
        resp = json_response({"erreur": "serveur"}, status=500)
        assert resp.status == 500


# ---------------------------------------------------------------------------
# Content-Type
# ---------------------------------------------------------------------------


class TestContentType:
    def test_content_type_application_json(self):
        resp = json_response({})
        assert "application/json" in resp.content_type

    def test_content_type_charset_utf8(self):
        resp = json_response({})
        assert "charset=utf-8" in resp.content_type.lower()

    def test_content_type_exact(self):
        resp = json_response({})
        assert resp.content_type == "application/json; charset=utf-8"


# ---------------------------------------------------------------------------
# Corps de réponse
# ---------------------------------------------------------------------------


class TestCorps:
    def test_body_est_bytes(self):
        resp = json_response({"x": 1})
        assert isinstance(resp.body, bytes)

    def test_body_json_valide(self):
        resp = json_response({"x": 1})
        parsed = json.loads(resp.body)
        assert parsed == {"x": 1}

    def test_body_non_vide(self):
        resp = json_response({})
        assert len(resp.body) > 0


# ---------------------------------------------------------------------------
# Encodage UTF-8
# ---------------------------------------------------------------------------


class TestEncodage:
    def test_caracteres_accentues(self):
        resp = json_response({"msg": "héros"})
        assert "héros" in resp.body.decode("utf-8")

    def test_utf8_correct(self):
        data = {"prénom": "Éléonore", "ville": "Montréal"}
        resp = json_response(data)
        assert json.loads(resp.body.decode("utf-8")) == data

    def test_ensure_ascii_false(self):
        resp = json_response({"msg": "café"})
        assert b"caf\\u00e9" not in resp.body
        assert "café".encode("utf-8") in resp.body

    def test_emoji_non_ascii(self):
        resp = json_response({"icon": "✓"})
        assert json.loads(resp.body.decode("utf-8")) == {"icon": "✓"}

    def test_decodage_utf8_sans_erreur(self):
        resp = json_response({"a": "été", "b": "naïf"})
        resp.body.decode("utf-8")


# ---------------------------------------------------------------------------
# Gestion des erreurs de sérialisation
# ---------------------------------------------------------------------------


class TestErreurSerialisation:
    def test_objet_non_serialisable_leve_valueerror(self):
        with pytest.raises((ValueError, TypeError)):
            json_response({"x": object()})

    def test_set_non_serialisable(self):
        with pytest.raises((ValueError, TypeError)):
            json_response({1, 2, 3})

    def test_bytes_non_serialisables(self):
        with pytest.raises((ValueError, TypeError)):
            json_response({"data": b"binary"})

    def test_valueerror_message_clair(self):
        with pytest.raises(ValueError, match="sérialisable"):
            json_response({"x": object()})


# ---------------------------------------------------------------------------
# Cohérence avec BaseController.json()
# ---------------------------------------------------------------------------


class TestCohérenceBaseController:
    def test_meme_content_type_que_base_controller(self):
        from core.mvc.controller.base_controller import BaseController
        resp_helper = json_response({"a": 1})
        resp_ctrl = BaseController.json({"a": 1})
        assert resp_helper.content_type == resp_ctrl.content_type

    def test_meme_corps_que_base_controller(self):
        from core.mvc.controller.base_controller import BaseController
        data = {"id": 1, "nom": "Alice"}
        resp_helper = json_response(data)
        resp_ctrl = BaseController.json(data)
        assert json.loads(resp_helper.body) == json.loads(resp_ctrl.body)

    def test_meme_statut_que_base_controller(self):
        from core.mvc.controller.base_controller import BaseController
        resp_helper = json_response({"x": 1}, status=201)
        resp_ctrl = BaseController.json({"x": 1}, status=201)
        assert resp_helper.status == resp_ctrl.status
