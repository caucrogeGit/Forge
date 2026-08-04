"""
Tests SECURITY-CSRF-AUDIT-001 — Vérification CSRF en cycle quasi-HTTP.

Utilise Application.dispatch() + FakeRequest pour simuler des requêtes HTTP
complètes à travers le cycle CSRF de Forge sans démarrer de serveur réseau.

Couvre :
  - token absent → 403 ;
  - token invalide → 403 ;
  - session absente → 403 ;
  - token valide via champ de formulaire → passe le filtre CSRF ;
  - token valide via en-tête X-CSRF-Token (AJAX) → passe le filtre CSRF ;
  - GET / HEAD ne requièrent pas de token ;
  - POST / PUT / PATCH / DELETE requièrent un token ;
  - _method override (POST → DELETE/PUT/PATCH) avec token valide → passe ;
  - csrf=False exemptée explicitement ;
  - CSRF vérifié avant les middlewares d'authentification ;
  - CSRF vérifié même sur les routes publiques ;
  - cas limites (token vide, token de mauvaise session, session sans csrf_token) ;
  - templates générés par views_builder contiennent le champ csrf_token ;
  - formulaires publics générés par public_form contiennent le champ csrf_token.
"""
from __future__ import annotations

import re
from pathlib import Path


from core.app.application import Application
from core.http.response import Response
from core.http.router import Router
from core.security import session as _sessions
from core.templating.manager import template_manager
from integrations.jinja2.renderer import Jinja2Renderer
from forge_mvc_testing import FakeRequest


# ── Helpers partagés ──────────────────────────────────────────────────────────

def _ok_handler(request):
    return Response(200, b"ok")


def _prepare_403(tmp_path):
    """Configure le template 403 minimal pour que _html() puisse le rendre."""
    (tmp_path / "errors").mkdir(exist_ok=True)
    (tmp_path / "errors" / "403.html").write_text("csrf-erreur", encoding="utf-8")
    import core.forge as forge
    forge._cfg["views_dir"] = str(tmp_path)
    template_manager.register(Jinja2Renderer(str(tmp_path)))


def _make_app(router, *, middlewares=None):
    return Application(router, middlewares=middlewares if middlewares is not None else [])


def _session_with_token() -> tuple[str, str]:
    """Retourne (session_id, csrf_token) pour un test."""
    sid = _sessions.create_session()
    token = _sessions.get_session(sid)["csrf_token"]
    return sid, token


# ── Refus — token absent ou invalide ─────────────────────────────────────────

class TestCsrfRefus:

    def test_post_sans_cookie_refuse(self, tmp_path):
        """POST sans session → 403 (pas de csrf_token attendu)."""
        _prepare_403(tmp_path)
        router = Router()
        router.add("POST", "/form", _ok_handler, public=True)
        resp = _make_app(router).dispatch(FakeRequest("POST", "/form"))
        assert resp.status == 403

    def test_post_avec_session_sans_token_refuse(self, tmp_path):
        """POST avec session mais sans csrf_token dans le body → 403."""
        _prepare_403(tmp_path)
        sid = _sessions.create_session()
        router = Router()
        router.add("POST", "/form", _ok_handler, public=True)
        req = FakeRequest("POST", "/form", session_id=sid)
        resp = _make_app(router).dispatch(req)
        assert resp.status == 403

    def test_post_token_invalide_refuse(self, tmp_path):
        """POST avec un token qui ne correspond pas à la session → 403."""
        _prepare_403(tmp_path)
        sid = _sessions.create_session()
        router = Router()
        router.add("POST", "/form", _ok_handler, public=True)
        req = FakeRequest("POST", "/form",
                          body={"csrf_token": "mauvais-token"},
                          session_id=sid)
        resp = _make_app(router).dispatch(req)
        assert resp.status == 403

    def test_post_token_vide_refuse(self, tmp_path):
        """POST avec csrf_token='' → 403 (token vide traité comme absent)."""
        _prepare_403(tmp_path)
        sid = _sessions.create_session()
        router = Router()
        router.add("POST", "/form", _ok_handler, public=True)
        req = FakeRequest("POST", "/form",
                          body={"csrf_token": ""},
                          session_id=sid)
        resp = _make_app(router).dispatch(req)
        assert resp.status == 403

    def test_put_sans_token_refuse(self, tmp_path):
        """PUT sans token → 403."""
        _prepare_403(tmp_path)
        router = Router()
        router.add("PUT", "/resource/1", _ok_handler, public=True)
        resp = _make_app(router).dispatch(FakeRequest("PUT", "/resource/1"))
        assert resp.status == 403

    def test_patch_sans_token_refuse(self, tmp_path):
        """PATCH sans token → 403."""
        _prepare_403(tmp_path)
        router = Router()
        router.add("PATCH", "/resource/1", _ok_handler, public=True)
        resp = _make_app(router).dispatch(FakeRequest("PATCH", "/resource/1"))
        assert resp.status == 403

    def test_delete_sans_token_refuse(self, tmp_path):
        """DELETE sans token → 403."""
        _prepare_403(tmp_path)
        router = Router()
        router.add("DELETE", "/resource/1", _ok_handler, public=True)
        resp = _make_app(router).dispatch(FakeRequest("DELETE", "/resource/1"))
        assert resp.status == 403

    def test_token_autre_session_refuse(self, tmp_path):
        """Token extrait d'une session différente de celle de la requête → 403."""
        _prepare_403(tmp_path)
        sid_a = _sessions.create_session()
        token_a = _sessions.get_session(sid_a)["csrf_token"]
        sid_b = _sessions.create_session()  # session différente
        router = Router()
        router.add("POST", "/form", _ok_handler, public=True)
        req = FakeRequest("POST", "/form",
                          body={"csrf_token": token_a},
                          session_id=sid_b)  # session B avec token de A
        resp = _make_app(router).dispatch(req)
        assert resp.status == 403

    def test_header_invalide_refuse(self, tmp_path):
        """X-CSRF-Token incorrect → 403."""
        _prepare_403(tmp_path)
        sid = _sessions.create_session()
        router = Router()
        router.add("POST", "/api/action", _ok_handler, public=True)
        req = FakeRequest("POST", "/api/action",
                          session_id=sid,
                          headers={"X-CSRF-Token": "faux-token"})
        resp = _make_app(router).dispatch(req)
        assert resp.status == 403


# ── Acceptation — token valide ────────────────────────────────────────────────

class TestCsrfAccepte:

    def test_post_token_body_valide_passe(self, tmp_path):
        """POST avec token correct dans le body → passe le filtre CSRF."""
        _prepare_403(tmp_path)
        sid, token = _session_with_token()
        router = Router()
        router.add("POST", "/form", _ok_handler, public=True)
        req = FakeRequest("POST", "/form",
                          body={"csrf_token": token},
                          session_id=sid)
        resp = _make_app(router).dispatch(req)
        assert resp.status == 200

    def test_post_token_header_ajax_valide_passe(self, tmp_path):
        """POST avec token valide dans X-CSRF-Token (AJAX) → passe le filtre CSRF."""
        _prepare_403(tmp_path)
        sid, token = _session_with_token()
        router = Router()
        router.add("POST", "/api/action", _ok_handler, public=True)
        req = FakeRequest("POST", "/api/action",
                          session_id=sid,
                          headers={"X-CSRF-Token": token})
        resp = _make_app(router).dispatch(req)
        assert resp.status == 200

    def test_put_token_valide_passe(self, tmp_path):
        """PUT avec token valide → passe le filtre CSRF."""
        _prepare_403(tmp_path)
        sid, token = _session_with_token()
        router = Router()
        router.add("PUT", "/resource/1", _ok_handler, public=True)
        req = FakeRequest("PUT", "/resource/1",
                          body={"csrf_token": token},
                          session_id=sid)
        resp = _make_app(router).dispatch(req)
        assert resp.status == 200

    def test_patch_token_valide_passe(self, tmp_path):
        """PATCH avec token valide → passe le filtre CSRF."""
        _prepare_403(tmp_path)
        sid, token = _session_with_token()
        router = Router()
        router.add("PATCH", "/resource/1", _ok_handler, public=True)
        req = FakeRequest("PATCH", "/resource/1",
                          body={"csrf_token": token},
                          session_id=sid)
        resp = _make_app(router).dispatch(req)
        assert resp.status == 200

    def test_delete_token_valide_passe(self, tmp_path):
        """DELETE avec token valide → passe le filtre CSRF."""
        _prepare_403(tmp_path)
        sid, token = _session_with_token()
        router = Router()
        router.add("DELETE", "/resource/1", _ok_handler, public=True)
        req = FakeRequest("DELETE", "/resource/1",
                          body={"csrf_token": token},
                          session_id=sid)
        resp = _make_app(router).dispatch(req)
        assert resp.status == 200

    def test_body_priorite_sur_header_si_les_deux(self, tmp_path):
        """Body token prioritaire si body et header fournis avec token valide."""
        _prepare_403(tmp_path)
        sid, token = _session_with_token()
        router = Router()
        router.add("POST", "/form", _ok_handler, public=True)
        req = FakeRequest("POST", "/form",
                          body={"csrf_token": token},
                          session_id=sid,
                          headers={"X-CSRF-Token": "mauvais-header"})
        # Le body apporte le bon token → passe
        resp = _make_app(router).dispatch(req)
        assert resp.status == 200


# ── Méthodes sûres exemptées ──────────────────────────────────────────────────

class TestCsrfMethodesSuures:

    def test_get_ne_requiert_pas_csrf(self, tmp_path):
        """GET ne requiert jamais de token CSRF."""
        _prepare_403(tmp_path)
        router = Router()
        router.add("GET", "/page", _ok_handler, public=True)
        resp = _make_app(router).dispatch(FakeRequest("GET", "/page"))
        assert resp.status == 200

    def test_head_ne_requiert_pas_csrf(self, tmp_path):
        """HEAD ne requiert jamais de token CSRF."""
        _prepare_403(tmp_path)
        router = Router()
        router.add("HEAD", "/page", _ok_handler, public=True)
        resp = _make_app(router).dispatch(FakeRequest("HEAD", "/page"))
        assert resp.status == 200

    def test_options_ne_requiert_pas_csrf(self, tmp_path):
        """OPTIONS ne requiert jamais de token CSRF."""
        _prepare_403(tmp_path)
        router = Router()
        router.add("OPTIONS", "/page", _ok_handler, public=True)
        resp = _make_app(router).dispatch(FakeRequest("OPTIONS", "/page"))
        assert resp.status == 200


# ── Exemptions explicites csrf=False ─────────────────────────────────────────

class TestCsrfExemptions:

    def test_route_csrf_false_passe_sans_token(self, tmp_path):
        """Route avec csrf=False : POST sans token → 200 (route API, webhook...)."""
        _prepare_403(tmp_path)
        router = Router()
        router.add("POST", "/webhooks/stripe", _ok_handler,
                   public=True, csrf=False)
        resp = _make_app(router).dispatch(FakeRequest("POST", "/webhooks/stripe"))
        assert resp.status == 200

    def test_route_api_true_csrf_false_passe(self, tmp_path):
        """Route api=True csrf=False : POST sans token → 200."""
        _prepare_403(tmp_path)
        router = Router()
        router.add("POST", "/api/data", _ok_handler,
                   public=True, csrf=False, api=True)
        resp = _make_app(router).dispatch(FakeRequest("POST", "/api/data"))
        assert resp.status == 200

    def test_route_groupe_csrf_false_passe(self, tmp_path):
        """Groupe de routes avec csrf=False partagé."""
        _prepare_403(tmp_path)
        router = Router()
        with router.group("/api", csrf=False, public=True) as api:
            api.add("POST", "/items", _ok_handler)
            api.add("DELETE", "/items/1", _ok_handler)
        assert _make_app(router).dispatch(FakeRequest("POST", "/api/items")).status == 200
        assert _make_app(router).dispatch(FakeRequest("DELETE", "/api/items/1")).status == 200

    def test_route_publique_sans_csrf_false_requiert_quand_meme_token(self, tmp_path):
        """Une route public=True sans csrf=False : POST sans token → 403.
        public=True ne désactive PAS la protection CSRF."""
        _prepare_403(tmp_path)
        router = Router()
        router.add("POST", "/login", _ok_handler, public=True)
        resp = _make_app(router).dispatch(FakeRequest("POST", "/login"))
        assert resp.status == 403


# ── CSRF avant les middlewares d'authentification ─────────────────────────────

class TestCsrfAvantAuth:

    def test_csrf_invalide_bloque_avant_middleware(self, tmp_path):
        """CSRF invalide sur route protégée → 403 sans appeler le middleware."""
        _prepare_403(tmp_path)
        appele = []

        class _MiddlewareEspion:
            def check(self, request):
                appele.append(True)
                return None

        router = Router()
        router.add("POST", "/protege", _ok_handler)  # public=False, csrf=True
        app = _make_app(router, middlewares=[_MiddlewareEspion()])
        resp = app.dispatch(FakeRequest("POST", "/protege"))
        assert resp.status == 403
        assert not appele, "Le middleware ne doit pas être appelé si CSRF invalide"

    def test_csrf_valide_puis_middleware_bloque(self, tmp_path):
        """CSRF valide sur route protégée → middleware appelé, peut bloquer."""
        _prepare_403(tmp_path)
        sid, token = _session_with_token()

        class _MiddlewareBloquant:
            def check(self, request):
                return Response(401, b"non authentifie")

        router = Router()
        router.add("POST", "/protege", _ok_handler)  # public=False, csrf=True
        app = _make_app(router, middlewares=[_MiddlewareBloquant()])
        req = FakeRequest("POST", "/protege",
                          body={"csrf_token": token},
                          session_id=sid)
        resp = app.dispatch(req)
        assert resp.status == 401, "CSRF passé → middleware appliqué"

    def test_csrf_valide_middleware_passe_handler_appele(self, tmp_path):
        """CSRF valide + middleware qui passe → handler exécuté."""
        _prepare_403(tmp_path)
        sid, token = _session_with_token()

        class _MiddlewarePasse:
            def check(self, request):
                return None

        router = Router()
        router.add("POST", "/protege", _ok_handler)
        app = _make_app(router, middlewares=[_MiddlewarePasse()])
        req = FakeRequest("POST", "/protege",
                          body={"csrf_token": token},
                          session_id=sid)
        resp = app.dispatch(req)
        assert resp.status == 200


# ── Method override (POST → DELETE / PUT / PATCH) ────────────────────────────

class TestCsrfMethodOverride:

    def test_post_to_delete_override_token_valide(self, tmp_path):
        """POST + _method=DELETE avec token valide → route DELETE exécutée."""
        _prepare_403(tmp_path)
        sid, token = _session_with_token()
        router = Router()
        router.add("DELETE", "/items/42", _ok_handler, public=True)
        req = FakeRequest("POST", "/items/42",
                          body={"_method": "DELETE", "csrf_token": token},
                          session_id=sid)
        resp = _make_app(router).dispatch(req)
        assert resp.status == 200

    def test_post_to_delete_override_sans_token_refuse(self, tmp_path):
        """POST + _method=DELETE sans token → 403."""
        _prepare_403(tmp_path)
        sid = _sessions.create_session()
        router = Router()
        router.add("DELETE", "/items/42", _ok_handler, public=True)
        req = FakeRequest("POST", "/items/42",
                          body={"_method": "DELETE"},
                          session_id=sid)
        resp = _make_app(router).dispatch(req)
        assert resp.status == 403

    def test_post_to_put_override_token_valide(self, tmp_path):
        """POST + _method=PUT avec token valide → route PUT exécutée."""
        _prepare_403(tmp_path)
        sid, token = _session_with_token()
        router = Router()
        router.add("PUT", "/items/42", _ok_handler, public=True)
        req = FakeRequest("POST", "/items/42",
                          body={"_method": "PUT", "csrf_token": token},
                          session_id=sid)
        resp = _make_app(router).dispatch(req)
        assert resp.status == 200

    def test_post_to_patch_override_token_valide(self, tmp_path):
        """POST + _method=PATCH avec token valide → route PATCH exécutée."""
        _prepare_403(tmp_path)
        sid, token = _session_with_token()
        router = Router()
        router.add("PATCH", "/items/42", _ok_handler, public=True)
        req = FakeRequest("POST", "/items/42",
                          body={"_method": "PATCH", "csrf_token": token},
                          session_id=sid)
        resp = _make_app(router).dispatch(req)
        assert resp.status == 200


# ── Cycle CRUD simulé ────────────────────────────────────────────────────────

class TestCsrfCrudSimule:
    """Simule un cycle CRUD complet : POST create, POST update, POST delete."""

    def _build_crud_router(self):
        """Construit un routeur CRUD minimal (non-public, csrf=True)."""
        router = Router()
        router.add("GET",    "/contacts",         _ok_handler)
        router.add("GET",    "/contacts/new",      _ok_handler)
        router.add("POST",   "/contacts",          _ok_handler, name="contacts_create")
        router.add("GET",    "/contacts/{id}",     _ok_handler)
        router.add("GET",    "/contacts/{id}/edit",_ok_handler)
        router.add("PUT",    "/contacts/{id}",     _ok_handler, name="contacts_update")
        router.add("DELETE", "/contacts/{id}",     _ok_handler, name="contacts_delete")
        return router

    def test_create_sans_token_refuse(self, tmp_path):
        """POST /contacts sans token → 403."""
        _prepare_403(tmp_path)
        router = self._build_crud_router()
        resp = _make_app(router).dispatch(
            FakeRequest("POST", "/contacts")
        )
        assert resp.status == 403

    def test_create_token_invalide_refuse(self, tmp_path):
        """POST /contacts avec token invalide → 403."""
        _prepare_403(tmp_path)
        sid = _sessions.create_session()
        router = self._build_crud_router()
        resp = _make_app(router).dispatch(
            FakeRequest("POST", "/contacts",
                        body={"Nom": "Dupont", "csrf_token": "invalide"},
                        session_id=sid)
        )
        assert resp.status == 403

    def test_create_token_valide_passe_csrf(self, tmp_path):
        """POST /contacts avec token valide → passe le filtre CSRF (puis middleware auth)."""
        _prepare_403(tmp_path)
        sid, token = _session_with_token()
        router = self._build_crud_router()

        class _AutoriseAuth:
            def check(self, request):
                return None  # simule un utilisateur authentifié

        app = Application(router, middlewares=[_AutoriseAuth()])
        resp = app.dispatch(
            FakeRequest("POST", "/contacts",
                        body={"Nom": "Dupont", "csrf_token": token},
                        session_id=sid)
        )
        assert resp.status == 200

    def test_update_via_override_sans_token_refuse(self, tmp_path):
        """POST + _method=PUT /contacts/1 sans token → 403."""
        _prepare_403(tmp_path)
        sid = _sessions.create_session()
        router = self._build_crud_router()
        resp = _make_app(router).dispatch(
            FakeRequest("POST", "/contacts/1",
                        body={"_method": "PUT", "Nom": "Durand"},
                        session_id=sid)
        )
        assert resp.status == 403

    def test_update_via_override_token_valide_passe(self, tmp_path):
        """POST + _method=PUT /contacts/1 avec token valide → passe CSRF."""
        _prepare_403(tmp_path)
        sid, token = _session_with_token()
        router = self._build_crud_router()

        class _AutoriseAuth:
            def check(self, request):
                return None

        app = Application(router, middlewares=[_AutoriseAuth()])
        resp = app.dispatch(
            FakeRequest("POST", "/contacts/1",
                        body={"_method": "PUT", "Nom": "Durand", "csrf_token": token},
                        session_id=sid)
        )
        assert resp.status == 200

    def test_delete_via_override_sans_token_refuse(self, tmp_path):
        """POST + _method=DELETE /contacts/1 sans token → 403."""
        _prepare_403(tmp_path)
        sid = _sessions.create_session()
        router = self._build_crud_router()
        resp = _make_app(router).dispatch(
            FakeRequest("POST", "/contacts/1",
                        body={"_method": "DELETE"},
                        session_id=sid)
        )
        assert resp.status == 403

    def test_get_list_ne_requiert_pas_csrf(self, tmp_path):
        """GET /contacts ne requiert pas de token CSRF."""
        _prepare_403(tmp_path)
        router = self._build_crud_router()

        class _AutoriseAuth:
            def check(self, request):
                return None

        app = Application(router, middlewares=[_AutoriseAuth()])
        resp = app.dispatch(FakeRequest("GET", "/contacts"))
        assert resp.status == 200

    def test_get_form_ne_requiert_pas_csrf(self, tmp_path):
        """GET /contacts/new ne requiert pas de token CSRF."""
        _prepare_403(tmp_path)
        router = self._build_crud_router()

        class _AutoriseAuth:
            def check(self, request):
                return None

        app = Application(router, middlewares=[_AutoriseAuth()])
        resp = app.dispatch(FakeRequest("GET", "/contacts/new"))
        assert resp.status == 200


# ── Cas limites ───────────────────────────────────────────────────────────────

class TestCsrfCasLimites:

    def test_session_inconnue_refuse(self, tmp_path):
        """Session_id inconnu (non présente en store) → 403 car pas de csrf_token attendu."""
        _prepare_403(tmp_path)
        router = Router()
        router.add("POST", "/form", _ok_handler, public=True)
        req = FakeRequest("POST", "/form",
                          body={"csrf_token": "quelconque"},
                          session_id="session-id-inexistante")
        resp = _make_app(router).dispatch(req)
        assert resp.status == 403

    def test_route_inconnue_retourne_404(self, tmp_path):
        """Route inconnue → 404 (pas de CSRF demandé pour une route inexistante)."""
        (tmp_path / "errors").mkdir(exist_ok=True)
        (tmp_path / "errors" / "404.html").write_text("not found", encoding="utf-8")
        (tmp_path / "errors" / "403.html").write_text("csrf-erreur", encoding="utf-8")
        import core.forge as forge
        forge._cfg["views_dir"] = str(tmp_path)
        template_manager.register(Jinja2Renderer(str(tmp_path)))
        router = Router()
        resp = _make_app(router).dispatch(FakeRequest("POST", "/inconnu"))
        assert resp.status == 404

    def test_token_numerique_refuse(self, tmp_path):
        """csrf_token=12345 (type numérique passé comme string) → 403 si ne correspond pas."""
        _prepare_403(tmp_path)
        sid = _sessions.create_session()
        router = Router()
        router.add("POST", "/form", _ok_handler, public=True)
        req = FakeRequest("POST", "/form",
                          body={"csrf_token": "12345"},
                          session_id=sid)
        resp = _make_app(router).dispatch(req)
        assert resp.status == 403

    def test_multiples_tokens_dans_body_premier_utilise(self, tmp_path):
        """Si le body contient plusieurs valeurs pour csrf_token, le premier est utilisé."""
        _prepare_403(tmp_path)
        sid, token = _session_with_token()
        router = Router()
        router.add("POST", "/form", _ok_handler, public=True)
        # FakeRequest met les valeurs en liste — simuler le bon token en premier
        req = FakeRequest("POST", "/form", session_id=sid)
        req.body["csrf_token"] = [token, "faux"]  # bon token en premier
        resp = _make_app(router).dispatch(req)
        assert resp.status == 200


# ── Vérification des templates générés ───────────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent


class TestCsrfFormulairesGeneres:

    def test_views_builder_new_contient_csrf_token(self):
        """La vue 'new' générée par views_builder contient un champ csrf_token caché."""
        source = (ROOT / "packages" / "forge-mvc-entities" / "forge_mvc_entities" / "crud" / "views_builder.py")
        text = source.read_text(encoding="utf-8")
        assert 'name="csrf_token"' in text

    def test_views_builder_edit_contient_csrf_token(self):
        """La vue 'edit' générée par views_builder contient un champ csrf_token caché."""
        source = (ROOT / "packages" / "forge-mvc-entities" / "forge_mvc_entities" / "crud" / "views_builder.py")
        text = source.read_text(encoding="utf-8")
        # Plusieurs occurrences — au moins deux (new + edit)
        occurrences = text.count('name="csrf_token"')
        assert occurrences >= 2, (
            f"views_builder.py devrait contenir ≥2 champs csrf_token (new+edit), trouvé {occurrences}"
        )

    def test_views_builder_delete_contient_csrf_token(self):
        """La vue de suppression générée contient un champ csrf_token."""
        source = (ROOT / "packages" / "forge-mvc-entities" / "forge_mvc_entities" / "crud" / "views_builder.py")
        text = source.read_text(encoding="utf-8")
        # Au moins 3 occurrences (new, edit, delete)
        occurrences = text.count('name="csrf_token"')
        assert occurrences >= 3, (
            f"views_builder.py devrait contenir ≥3 champs csrf_token (new+edit+delete), trouvé {occurrences}"
        )

    def test_views_builder_csrf_value_templated(self):
        """Le token est injecté via {{ csrf_token }} (valeur dynamique, pas hardcodée)."""
        source = (ROOT / "packages" / "forge-mvc-entities" / "forge_mvc_entities" / "crud" / "views_builder.py")
        text = source.read_text(encoding="utf-8")
        assert 'value="{{ csrf_token }}"' in text

    def test_public_form_contient_csrf_token(self):
        """cli/public/public_form.py génère un champ csrf_token dans les formulaires publics."""
        source = (ROOT / "cli" / "public" / "public_form.py")
        text = source.read_text(encoding="utf-8")
        assert 'name="csrf_token"' in text

    def test_views_builder_csrf_input_hidden(self):
        """Le champ csrf_token est de type hidden."""
        source = (ROOT / "packages" / "forge-mvc-entities" / "forge_mvc_entities" / "crud" / "views_builder.py")
        text = source.read_text(encoding="utf-8")
        # Recherche le pattern complet input type hidden avec csrf_token
        assert re.search(r'type="hidden"[^>]*name="csrf_token"'
                         r'|name="csrf_token"[^>]*type="hidden"'
                         r'|input type="hidden" name="csrf_token"', text)

    def test_le_squelette_livre_le_champ_csrf(self):
        """Le partiel inclus par tous les formulaires générés porte le jeton.

        STARTERS-TESTS-REPOINT-001 : ce test visait les vues du starter
        « Communes & Séjours », supprimé par l'ADR-035. Il se sautait donc
        toujours, en annonçant un starter absent comme s'il s'agissait d'une
        condition d'environnement.

        Son intention reste valable, et son nouveau sujet n'était couvert par
        rien : `partials/csrf.html` est le fichier que chaque formulaire du
        squelette inclut. S'il perdait son champ caché, tous les formulaires
        d'un projet neuf posteraient sans jeton.
        """
        partiel = ROOT / "skeleton" / "data" / "mvc" / "views" / "partials" / "csrf.html"

        assert partiel.is_file(), f"{partiel} absent du squelette"

        contenu = partiel.read_text(encoding="utf-8")

        assert 'name="csrf_token"' in contenu
        assert 'type="hidden"' in contenu
        assert "{{ csrf_token }}" in contenu, (
            "le champ doit interpoler la variable de contexte, pas une valeur figée")

    def test_tout_formulaire_post_du_squelette_porte_le_jeton(self):
        """Un partiel juste qu'aucun formulaire n'inclut ne protège rien.

        Le squelette ne livre aujourd'hui aucun formulaire POST : ses trois
        occurrences de `<form` sont un commentaire d'usage, une modale native
        `method="dialog"` et une démonstration `onsubmit="return false"`. La
        règle est donc vraie à vide.

        Ce constat est **affirmé** plutôt que sauté. Un `pytest.skip` ici
        rendrait la règle invisible le jour où quelqu'un ajoute un formulaire
        POST, et c'est exactement le mode de panne que ce fichier vient de
        corriger. Le jour venu, ce test bascule tout seul sur la vérification
        du jeton.
        """
        vues = ROOT / "skeleton" / "data" / "mvc" / "views"
        # `method` peut être en toute casse et avec n'importe quel guillemet.
        poste = re.compile(r"<form[^>]*\bmethod\s*=\s*[\"']?post\b", re.IGNORECASE)

        formulaires = [(v, v.read_text(encoding="utf-8")) for v in sorted(vues.rglob("*.html"))]
        postants = [(v, texte) for v, texte in formulaires if poste.search(texte)]

        sans_jeton = [
            v.relative_to(vues).as_posix() for v, texte in postants
            if "partials/csrf.html" not in texte and 'name="csrf_token"' not in texte
        ]

        assert not sans_jeton, f"formulaires POST sans jeton CSRF : {sans_jeton}"


# ── Vérification du contrat CsrfMiddleware ────────────────────────────────────

class TestCsrfMiddlewareContrat:
    """Teste le middleware CSRF directement (sans Application.dispatch)."""

    def _make_request(self, body=None, session_id=None, headers=None):
        return FakeRequest("POST", "/test",
                           body=body,
                           session_id=session_id,
                           headers=headers)

    def test_pas_de_session_retourne_403(self, tmp_path):
        """Pas de cookie session → csrf_token attendu absent → retourne une Response 403."""
        _prepare_403(tmp_path)
        from core.security.middleware import CsrfMiddleware
        csrf = CsrfMiddleware()
        req = self._make_request()
        result = csrf.check(req)
        assert result is not None
        assert result.status == 403

    def test_token_absent_retourne_403(self, tmp_path):
        """Session présente, token absent → 403."""
        _prepare_403(tmp_path)
        from core.security.middleware import CsrfMiddleware
        sid = _sessions.create_session()
        csrf = CsrfMiddleware()
        req = self._make_request(session_id=sid)
        result = csrf.check(req)
        assert result is not None
        assert result.status == 403

    def test_token_valide_retourne_none(self, tmp_path):
        """Session présente, token valide → retourne None (pas de blocage)."""
        _prepare_403(tmp_path)
        from core.security.middleware import CsrfMiddleware
        sid, token = _session_with_token()
        csrf = CsrfMiddleware()
        req = self._make_request(body={"csrf_token": token}, session_id=sid)
        result = csrf.check(req)
        assert result is None

    def test_token_valide_via_header_retourne_none(self, tmp_path):
        """Session présente, token valide dans X-CSRF-Token → retourne None."""
        _prepare_403(tmp_path)
        from core.security.middleware import CsrfMiddleware
        sid, token = _session_with_token()
        csrf = CsrfMiddleware()
        req = self._make_request(session_id=sid,
                                 headers={"X-CSRF-Token": token})
        result = csrf.check(req)
        assert result is None

    def test_field_name_personnalise(self, tmp_path):
        """CsrfMiddleware avec field_name personnalisé lit le bon champ."""
        _prepare_403(tmp_path)
        from core.security.middleware import CsrfMiddleware
        sid, token = _session_with_token()
        csrf = CsrfMiddleware(field_name="mon_token")
        req = self._make_request(body={"mon_token": token}, session_id=sid)
        result = csrf.check(req)
        assert result is None

    def test_header_name_personnalise(self, tmp_path):
        """CsrfMiddleware avec header_name personnalisé lit le bon en-tête."""
        _prepare_403(tmp_path)
        from core.security.middleware import CsrfMiddleware
        sid, token = _session_with_token()
        csrf = CsrfMiddleware(header_name="X-Mon-Token")
        req = self._make_request(session_id=sid,
                                 headers={"X-Mon-Token": token})
        result = csrf.check(req)
        assert result is None
