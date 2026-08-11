from types import SimpleNamespace
from core.auth.user import AuthUser
from core.security.middleware import AuthMiddleware
from core.security.session import create_session, authenticate_session

_UTILISATEUR = {
    "UtilisateurId": 1, "Login": "u", "Prenom": "", "Nom": "",
    "Email": "", "Actif": True, "PasswordHash": "x", "roles": [],
}

_VALID_USER = AuthUser(id=1, login="u@x.fr", password_hash="x", is_active=True)


def _req(cookie=""):
    return SimpleNamespace(headers={"Cookie": cookie}, ip="127.0.0.1")


def _req_session(session):
    # Session résolue directement (request.session dict), sans store réel.
    return SimpleNamespace(session=session, headers={"Cookie": ""}, ip="127.0.0.1")


class TestAuthMiddleware:
    def setup_method(self):
        self.mw = AuthMiddleware("/login")

    def test_sans_session_redirige(self):
        resp = self.mw.check(_req())
        assert resp is not None
        assert resp.status == 302
        assert resp.headers["Location"] == "/login"

    def test_session_non_authentifiee_redirige(self):
        sid = create_session()
        resp = self.mw.check(_req(f"__Host-session_id={sid}"))
        assert resp is not None
        assert resp.status == 302

    def test_session_authentifiee_passe(self):
        sid = create_session()
        nouveau = authenticate_session(sid, _UTILISATEUR)
        resp = self.mw.check(_req(f"__Host-session_id={nouveau}"))
        assert resp is None

    def test_url_login_personnalisee(self):
        mw = AuthMiddleware("/auth/login")
        resp = mw.check(_req())
        assert resp.headers["Location"] == "/auth/login"


class TestAuthMiddlewareSubjectValidation:
    """ADR-080 (F54) : validation de l'existence du sujet + fermeture orpheline."""

    def test_valid_subject_passes(self):
        mw = AuthMiddleware("/login", user_loader=lambda _uid: _VALID_USER)
        assert mw.check(_req_session({"_auth_user_id": 1})) is None

    def test_orphan_session_closed_and_redirects(self):
        # loader renvoie None : le compte n'existe plus (session orpheline).
        mw = AuthMiddleware("/login", user_loader=lambda _uid: None)
        session = {"_auth_user_id": 1}
        resp = mw.check(_req_session(session))
        assert resp is not None and resp.status == 302
        assert resp.headers["Location"] == "/login"
        # la session est fermée : l'id d'auth a été retiré...
        assert "_auth_user_id" not in session
        # ...et le cookie de session est purgé.
        assert "__Host-session_id=" in resp.headers.get("Set-Cookie", "")

    def test_inactive_subject_is_orphan(self):
        inactive = AuthUser(id=1, login="u@x.fr", password_hash="x", is_active=False)
        mw = AuthMiddleware("/login", user_loader=lambda _uid: inactive)
        session = {"_auth_user_id": 1}
        resp = mw.check(_req_session(session))
        assert resp is not None and resp.status == 302
        assert "_auth_user_id" not in session

    def test_anonymous_redirects_without_closing_cookie(self):
        # aucun id en session : rien à fermer, pas de purge de cookie.
        mw = AuthMiddleware("/login", user_loader=lambda _uid: _VALID_USER)
        resp = mw.check(_req_session({}))
        assert resp is not None and resp.status == 302
        assert "Set-Cookie" not in resp.headers
