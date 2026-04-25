from types import SimpleNamespace
from core.security.middleware import AuthMiddleware
from core.security.session import creer_session, authentifier_session

_UTILISATEUR = {
    "UtilisateurId": 1, "Login": "u", "Prenom": "", "Nom": "",
    "Email": "", "Actif": True, "PasswordHash": "x", "roles": [],
}


def _req(cookie=""):
    return SimpleNamespace(headers={"Cookie": cookie}, ip="127.0.0.1")


class TestAuthMiddleware:
    def setup_method(self):
        self.mw = AuthMiddleware("/login")

    def test_sans_session_redirige(self):
        resp = self.mw.check(_req())
        assert resp is not None
        assert resp.status == 302
        assert resp.headers["Location"] == "/login"

    def test_session_non_authentifiee_redirige(self):
        sid = creer_session()
        resp = self.mw.check(_req(f"session_id={sid}"))
        assert resp is not None
        assert resp.status == 302

    def test_session_authentifiee_passe(self):
        sid = creer_session()
        nouveau = authentifier_session(sid, _UTILISATEUR)
        resp = self.mw.check(_req(f"session_id={nouveau}"))
        assert resp is None

    def test_url_login_personnalisee(self):
        mw = AuthMiddleware("/auth/login")
        resp = mw.check(_req())
        assert resp.headers["Location"] == "/auth/login"
