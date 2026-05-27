"""Tests — API-INSPECTABLE-OBJECTS-CONVENTION-001.

Verrouille la convention d'inspection appliquée à `Request` et `Response` :

  - accesseurs nommés (`request.param`, `request.form`, `request.json`,
    `request.file`, `request.header`, `request.route_param`) ;
  - vue d'inspection `.data` stable, masquage systématique des valeurs
    sensibles (Authorization, Cookie, password, csrf, token, …) ;
  - constructeurs nommés (`Response.text`, `Response.html`,
    `Response.json`) ;
  - `Response.debug` rend `obj.data` en dev et refuse en prod ;
  - `Response.cookies` ne fuite jamais la valeur des cookies posés.

Aucun vrai handler HTTP n'est instancié — un mini-handler `SimpleNamespace`
suffit pour construire un `Request`.
"""

from __future__ import annotations

import io
import json
from types import SimpleNamespace

import pytest

from core import forge as forge_module
from core.http.request import (
    MASKED_VALUE,
    Request,
    SENSITIVE_FIELD_FRAGMENTS,
    SENSITIVE_HEADER_NAMES,
    UploadedFile,
)
from core.http.response import Response


# ── Mini handler ─────────────────────────────────────────────────────────────


class _FakeHeaders:
    """Imite `http.client.HTTPMessage` (get insensible à la casse + keys()).

    Le default est `None`, comme `HTTPMessage.get(name)` : ne pas passer à
    `""` ici, sinon `Request.header(name)` retournerait `""` au lieu de
    `None`, ce qui casserait la sémantique « champ absent ».
    """

    def __init__(self, data: dict[str, str]):
        self._data = dict(data)
        self._lower = {k.lower(): k for k in self._data}

    def get(self, name, default=None):
        if name in self._data:
            return self._data[name]
        original_key = self._lower.get(name.lower())
        if original_key is None:
            return default
        return self._data[original_key]

    def keys(self):
        return list(self._data.keys())

    def items(self):
        return list(self._data.items())


def _handler(method="GET", path="/", headers=None, body=b"") -> SimpleNamespace:
    return SimpleNamespace(
        command=method,
        path=path,
        headers=_FakeHeaders(headers or {}),
        rfile=io.BytesIO(body),
        client_address=("127.0.0.1", 12345),
    )


# ── 1. Accesseurs `Request` ──────────────────────────────────────────────────


class TestRequestAccessors:
    def test_param_lit_la_query_string(self):
        req = Request(_handler(path="/search?q=forge&page=2"))
        assert req.param("q") == "forge"
        assert req.param("page") == "2"

    def test_param_retourne_default_si_absent(self):
        req = Request(_handler(path="/search"))
        assert req.param("missing") is None
        assert req.param("missing", default="1") == "1"

    def test_param_renvoie_la_premiere_valeur(self):
        req = Request(_handler(path="/?tag=a&tag=b"))
        assert req.param("tag") == "a"

    def test_header_lit_un_header(self):
        req = Request(_handler(headers={"User-Agent": "curl/8.0"}))
        assert req.header("User-Agent") == "curl/8.0"

    def test_header_insensible_a_la_casse(self):
        req = Request(_handler(headers={"X-Custom": "value"}))
        assert req.header("x-custom") == "value"

    def test_header_retourne_default_si_absent(self):
        req = Request(_handler())
        assert req.header("X-Missing") is None
        assert req.header("X-Missing", default="fallback") == "fallback"

    def test_form_lit_le_body_formulaire(self):
        body = b"email=a%40b.c&page=2"
        req = Request(_handler(
            method="POST",
            body=body,
            headers={"Content-Length": str(len(body)),
                     "Content-Type": "application/x-www-form-urlencoded"},
        ))
        assert req.form("email") == "a@b.c"
        assert req.form("page") == "2"

    def test_form_retourne_default_si_absent(self):
        req = Request(_handler())
        assert req.form("missing") is None
        assert req.form("missing", default="x") == "x"

    def test_json_lit_le_json_body(self):
        body = b'{"name": "Forge", "version": "1.0"}'
        req = Request(_handler(
            method="POST",
            body=body,
            headers={"Content-Length": str(len(body)),
                     "Content-Type": "application/json"},
        ))
        assert req.json("name") == "Forge"
        assert req.json("version") == "1.0"

    def test_json_retourne_default_si_absent(self):
        body = b'{"a": 1}'
        req = Request(_handler(
            method="POST",
            body=body,
            headers={"Content-Length": str(len(body)),
                     "Content-Type": "application/json"},
        ))
        assert req.json("missing") is None
        assert req.json("missing", default=42) == 42

    def test_json_sur_body_non_dict_retourne_default(self):
        # Body JSON racine = liste — pas un dict, le get(key) n'a pas de sens.
        body = b'[1, 2, 3]'
        req = Request(_handler(
            method="POST",
            body=body,
            headers={"Content-Length": str(len(body)),
                     "Content-Type": "application/json"},
        ))
        assert req.json("anything", default="ok") == "ok"

    def test_file_lit_un_upload(self):
        req = Request(_handler())  # body vide
        upload = UploadedFile(
            field_name="avatar",
            filename="x.png",
            content=b"\x89PNG...",
            content_type="image/png",
        )
        req.files["avatar"] = upload
        assert req.file("avatar") is upload

    def test_file_retourne_default_si_absent(self):
        req = Request(_handler())
        assert req.file("missing") is None

    def test_route_param_lit_les_parametres_de_route(self):
        req = Request(_handler())
        req.route_params = {"id": "42"}
        assert req.route_param("id") == "42"

    def test_route_param_retourne_default_si_absent(self):
        req = Request(_handler())
        assert req.route_param("missing") is None
        assert req.route_param("missing", default="x") == "x"


# ── 2. `Request.data` — structure et stabilité ───────────────────────────────


class TestRequestDataShape:
    def test_data_est_un_dict(self):
        req = Request(_handler(path="/contacts?id=1"))
        assert isinstance(req.data, dict)

    def test_data_contient_les_cles_canoniques(self):
        req = Request(_handler(path="/contacts?id=1"))
        keys = set(req.data.keys())
        expected = {
            "method", "original_method", "path", "ip",
            "params", "route_params", "headers",
            "body", "json_body", "files",
        }
        assert expected.issubset(keys), f"Manquantes : {expected - keys}"

    def test_data_method_path_ip(self):
        req = Request(_handler(method="GET", path="/health"))
        d = req.data
        assert d["method"] == "GET"
        assert d["path"] == "/health"
        assert d["ip"] == "127.0.0.1"

    def test_data_route_params_inclus(self):
        req = Request(_handler(path="/contacts/42"))
        req.route_params = {"id": "42"}
        assert req.data["route_params"] == {"id": "42"}

    def test_data_params_inclus(self):
        req = Request(_handler(path="/?q=forge"))
        assert req.data["params"] == {"q": ["forge"]}

    def test_data_n_est_pas_le_dunder_dict(self):
        req = Request(_handler())
        # Garde-fou §1 de la convention : .data n'est PAS un dump brut.
        assert req.data is not req.__dict__
        # Une clé "headers" différente : la version masquée vs HTTPMessage.
        assert not isinstance(req.data["headers"], _FakeHeaders)


# ── 3. `Request.data` — masquage des champs sensibles ────────────────────────


class TestRequestDataMasksSensitiveFields:

    @pytest.mark.parametrize("header", [
        "Authorization", "AUTHORIZATION", "authorization",
        "Cookie", "Set-Cookie",
        "X-API-Key", "x-auth-token", "X-CSRF-Token",
        "Proxy-Authorization",
    ])
    def test_masque_les_headers_sensibles(self, header):
        req = Request(_handler(headers={header: "very-secret-value"}))
        masked = req.data["headers"]
        assert masked[header] == MASKED_VALUE, (
            f"Header sensible {header!r} non masqué : {masked[header]!r}"
        )

    def test_header_inconnu_reste_visible(self):
        req = Request(_handler(headers={"User-Agent": "curl/8.0"}))
        assert req.data["headers"]["User-Agent"] == "curl/8.0"

    @pytest.mark.parametrize("field", [
        "password",
        "password_confirmation",
        "current_password",
        "user_passwd",
        "secret",
        "client_secret",
        "csrf",
        "csrf_token",
        "_csrf",
        "api_token",
        "bearer_token",
        "api_key",
        "apikey",
    ])
    def test_masque_les_champs_formulaire_sensibles(self, field):
        body = f"{field}=hunter2&email=a%40b.c".encode("utf-8")
        req = Request(_handler(
            method="POST",
            body=body,
            headers={"Content-Length": str(len(body)),
                     "Content-Type": "application/x-www-form-urlencoded"},
        ))
        masked_body = req.data["body"]
        assert masked_body[field] == MASKED_VALUE, (
            f"Champ {field!r} non masqué : {masked_body[field]!r}"
        )
        # Le champ non sensible reste lisible :
        assert masked_body["email"] == ["a@b.c"]

    def test_masque_les_champs_json_sensibles(self):
        body = json.dumps({
            "name": "Forge",
            "password": "hunter2",
            "csrf_token": "abc123",
            "api_key": "k-1",
        }).encode("utf-8")
        req = Request(_handler(
            method="POST",
            body=body,
            headers={"Content-Length": str(len(body)),
                     "Content-Type": "application/json"},
        ))
        masked = req.data["json_body"]
        assert masked["name"] == "Forge"
        assert masked["password"] == MASKED_VALUE
        assert masked["csrf_token"] == MASKED_VALUE
        assert masked["api_key"] == MASKED_VALUE

    def test_la_requete_reelle_reste_intacte(self):
        """Masquage = vue, pas mutation : le body brut reste accessible."""
        body = b"password=hunter2&email=a%40b.c"
        req = Request(_handler(
            method="POST",
            body=body,
            headers={"Content-Length": str(len(body)),
                     "Content-Type": "application/x-www-form-urlencoded"},
        ))
        assert req.body.get("password") == ["hunter2"]
        assert req.form("password") == "hunter2"
        # Mais .data le masque :
        assert req.data["body"]["password"] == MASKED_VALUE


# ── 4. `Request.data` — fichiers ─────────────────────────────────────────────


class TestRequestDataFiles:
    def test_files_inclus_uniquement_les_metadonnees(self):
        req = Request(_handler())
        secret_bytes = b"\x00\x01\x02SECRET-PNG-DATA"
        req.files["avatar"] = UploadedFile(
            field_name="avatar",
            filename="x.png",
            content=secret_bytes,
            content_type="image/png",
        )
        meta = req.data["files"]
        assert meta["avatar"]["filename"] == "x.png"
        assert meta["avatar"]["size"] == len(secret_bytes)
        assert meta["avatar"]["content_type"] == "image/png"
        # Le contenu binaire ne doit JAMAIS apparaître dans .data.
        flat = json.dumps(meta, default=str)
        assert "SECRET-PNG-DATA" not in flat


# ── 5. Constantes publiques exposées ─────────────────────────────────────────


class TestSensitiveConstants:
    def test_sensitive_headers_couvre_authorization_cookie(self):
        assert "authorization" in SENSITIVE_HEADER_NAMES
        assert "cookie" in SENSITIVE_HEADER_NAMES
        assert "set-cookie" in SENSITIVE_HEADER_NAMES

    def test_sensitive_fragments_couvre_password_csrf_token(self):
        assert "password" in SENSITIVE_FIELD_FRAGMENTS
        assert "csrf" in SENSITIVE_FIELD_FRAGMENTS
        assert "token" in SENSITIVE_FIELD_FRAGMENTS
        assert "secret" in SENSITIVE_FIELD_FRAGMENTS


# ── 6. `Response.text` / `.html` / `.json` ───────────────────────────────────


class TestResponseConstructors:
    def test_text_produit_text_plain(self):
        r = Response.text("Bonjour Forge")
        assert r.content_type == "text/plain; charset=utf-8"
        assert r.status == 200
        assert r.body == b"Bonjour Forge"

    def test_text_accepte_status_et_headers(self):
        r = Response.text("nope", status=404, headers={"X-Note": "v"})
        assert r.status == 404
        assert r.headers == {"X-Note": "v"}

    def test_html_produit_text_html(self):
        r = Response.html("<h1>Bonjour Forge</h1>")
        assert r.content_type == "text/html; charset=utf-8"
        assert r.body == b"<h1>Bonjour Forge</h1>"

    def test_json_produit_application_json(self):
        r = Response.json({"message": "Bonjour Forge"})
        assert r.content_type == "application/json; charset=utf-8"
        assert json.loads(r.body.decode("utf-8")) == {"message": "Bonjour Forge"}

    def test_json_serialise_unicode_brut(self):
        r = Response.json({"message": "éàç"})
        # ensure_ascii=False : pas d'échappement unicode.
        assert "éàç".encode("utf-8") in r.body

    def test_json_refuse_donnees_non_serialisables(self):
        with pytest.raises(ValueError):
            Response.json({"set": {1, 2, 3}})

    def test_json_accepte_status_personnalise(self):
        r = Response.json({"created": True}, status=201)
        assert r.status == 201


# ── 7. `Response.debug` ──────────────────────────────────────────────────────


class TestResponseDebug:
    @pytest.fixture(autouse=True)
    def _save_env(self):
        # Sauvegarde et restaure la clé `app_env` du registre forge.
        original = forge_module._cfg.get("app_env", "dev")
        try:
            yield
        finally:
            forge_module._cfg["app_env"] = original

    def _set_env(self, env: str) -> None:
        forge_module._cfg["app_env"] = env

    def test_dev_dump_obj_data_en_html(self):
        """En dev, `Response.debug(obj)` retourne désormais du HTML
        pédagogique (DX-DEBUG-DUMP-HTML-001) — le content-type est
        `text/html; charset=utf-8` et le body contient le path et la
        méthode lisibles."""
        self._set_env("dev")
        req = Request(_handler(path="/health"))
        r = Response.debug(req)
        assert r.content_type == "text/html; charset=utf-8"
        text = r.body.decode("utf-8")
        assert "Debug Forge" in text
        assert "method" in text
        assert "/health" in text

    def test_dev_dump_dict_brut(self):
        """Le rendu HTML conserve les clés et valeurs du dict brut."""
        self._set_env("dev")
        r = Response.debug({"a": 1, "b": "ok"})
        text = r.body.decode("utf-8")
        assert ">a<" in text
        assert ">1<" in text
        assert ">b<" in text
        assert ">ok<" in text

    def test_dev_fallback_repr_pour_objet_sans_data(self):
        self._set_env("dev")

        class Plain:
            def __repr__(self) -> str:
                return "<Plain x=1>"

        r = Response.debug(Plain())
        # Le repr est échappé HTML dans le rendu.
        assert b"&lt;Plain x=1&gt;" in r.body

    def test_dev_masque_les_headers_dans_le_dump(self):
        self._set_env("dev")
        req = Request(_handler(headers={"Authorization": "Bearer SECRET"}))
        text = Response.debug(req).body.decode("utf-8")
        assert "SECRET" not in text
        assert MASKED_VALUE in text

    def test_prod_refuse_et_n_inclut_pas_le_payload(self):
        self._set_env("prod")
        req = Request(_handler(headers={"Authorization": "Bearer SECRET"}))
        r = Response.debug(req)
        assert r.status == 404
        body = r.body.decode("utf-8")
        assert "désactivé" in body or "désactive" in body
        # Aucune fuite du contenu de obj :
        assert "SECRET" not in body
        assert "/health" not in body
        assert "Authorization" not in body

    def test_prod_refuse_aussi_un_dict_brut(self):
        self._set_env("prod")
        r = Response.debug({"password": "hunter2"})
        body = r.body.decode("utf-8")
        assert r.status == 404
        assert "hunter2" not in body
        assert "password" not in body


# ── 8. `Response.data` et `Response.cookies` ─────────────────────────────────


class TestResponseInspection:
    def test_data_contient_status_content_type_body_size(self):
        r = Response.text("Bonjour", status=201)
        d = r.data
        assert d["status"] == 201
        assert d["content_type"] == "text/plain; charset=utf-8"
        assert d["body_size"] == len(b"Bonjour")

    def test_data_n_inclut_pas_le_body(self):
        r = Response.text("USER-CONTENT-LEAK")
        d = r.data
        flat = json.dumps(d, default=str)
        assert "USER-CONTENT-LEAK" not in flat

    def test_data_masque_set_cookie(self):
        r = Response.text("ok", headers={"Set-Cookie": "session=secret-token"})
        masked = r.data["headers"]["Set-Cookie"]
        assert masked == "[masked]"
        assert "secret-token" not in json.dumps(r.data, default=str)

    def test_data_masque_authorization(self):
        r = Response.text("ok", headers={"Authorization": "Bearer secret"})
        assert r.data["headers"]["Authorization"] == "[masked]"

    def test_data_laisse_les_headers_normaux_visibles(self):
        r = Response.text("ok", headers={"X-Custom": "value"})
        assert r.data["headers"]["X-Custom"] == "value"

    def test_cookies_expose_seulement_les_noms(self):
        r = Response.text("ok", headers={"Set-Cookie": "session_id=abc123; HttpOnly"})
        assert r.cookies == ["session_id"]
        # Aucune valeur ne fuit :
        assert "abc123" not in json.dumps(r.cookies)

    def test_cookies_vide_si_aucun_set_cookie(self):
        r = Response.text("ok")
        assert r.cookies == []

    def test_cookies_supporte_une_liste(self):
        r = Response.text("ok", headers={"Set-Cookie": ["a=1; Path=/", "b=2; HttpOnly"]})
        assert r.cookies == ["a", "b"]


# ── 9. Compat existante ──────────────────────────────────────────────────────


class TestBackwardsCompatibility:
    """L'API existante de Request/Response ne doit pas être cassée."""

    def test_request_attributs_historiques_inchanges(self):
        body = b"name=Alice"
        req = Request(_handler(
            method="POST",
            body=body,
            headers={"Content-Length": str(len(body)),
                     "Content-Type": "application/x-www-form-urlencoded"},
        ))
        assert req.method == "POST"
        assert req.path == "/"
        assert req.params == {}
        assert req.body == {"name": ["Alice"]}
        assert req.json_body == {}
        assert req.files == {}
        assert req.route_params == {}
        assert req.ip == "127.0.0.1"

    def test_response_constructeur_historique(self):
        r = Response(201, "created", "text/html; charset=utf-8", {"X-Note": "v"})
        assert r.status == 201
        assert r.body == b"created"
        assert r.content_type == "text/html; charset=utf-8"
        assert r.headers == {"X-Note": "v"}

    def test_response_body_bytes_intact(self):
        r = Response(200, b"\x00\x01")
        assert r.body == b"\x00\x01"

    def test_response_body_none_devient_bytes_vides(self):
        r = Response(204, None)
        assert r.body == b""
