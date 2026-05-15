from types import SimpleNamespace
from core.security.session import (
    create_session, get_session, delete_session,
    authenticate_session, is_authenticated,
    get_user, user_has_role,
)

_UTILISATEUR = {
    "UtilisateurId": 1,
    "Login": "jdupont",
    "Prenom": "Jean",
    "Nom": "Dupont",
    "Email": "jdupont@test.fr",
    "Actif": True,
    "PasswordHash": "x",
    "roles": ["admin", "vendeur"],
}


def _req(session_id=None):
    cookie = f"__Host-session_id={session_id}" if session_id else ""
    return SimpleNamespace(headers={"Cookie": cookie}, ip="127.0.0.1")


class TestCreerSession:
    def test_retourne_chaine_hex(self):
        sid = create_session()
        assert isinstance(sid, str) and len(sid) == 64

    def test_session_existe(self):
        sid = create_session()
        assert get_session(sid) is not None

    def test_pas_authentifiee_par_defaut(self):
        sid = create_session()
        assert get_session(sid)["authenticated"] is False

    def test_csrf_token_present(self):
        sid = create_session()
        assert len(get_session(sid)["csrf_token"]) == 32


class TestGetSession:
    def test_id_inconnu_retourne_none(self):
        assert get_session("inexistant") is None


class TestSupprimerSession:
    def test_session_supprimee(self):
        sid = create_session()
        delete_session(sid)
        assert get_session(sid) is None

    def test_suppression_id_inexistant_sans_erreur(self):
        delete_session("inexistant")  # ne doit pas lever


class TestAuthentifierSession:
    def test_retourne_nouvel_id(self):
        sid = create_session()
        nouveau = authenticate_session(sid, _UTILISATEUR)
        assert nouveau is not None
        assert nouveau != sid

    def test_ancien_id_supprime(self):
        sid = create_session()
        authenticate_session(sid, _UTILISATEUR)
        assert get_session(sid) is None

    def test_nouvelle_session_authentifiee(self):
        sid = create_session()
        nouveau = authenticate_session(sid, _UTILISATEUR)
        assert get_session(nouveau)["authenticated"] is True

    def test_utilisateur_stocke(self):
        sid = create_session()
        nouveau = authenticate_session(sid, _UTILISATEUR)
        user = get_session(nouveau)["user"]
        assert user["login"] == "jdupont"
        assert "admin" in user["roles"]

    def test_id_invalide_retourne_none(self):
        assert authenticate_session("faux_id", _UTILISATEUR) is None


class TestEstAuthentifie:
    def test_sans_cookie_retourne_false(self):
        assert is_authenticated(_req()) is False

    def test_session_non_authentifiee_retourne_false(self):
        sid = create_session()
        assert is_authenticated(_req(sid)) is False

    def test_session_authentifiee_retourne_true(self):
        sid = create_session()
        nouveau = authenticate_session(sid, _UTILISATEUR)
        assert is_authenticated(_req(nouveau)) is True


class TestGetUtilisateur:
    def test_sans_session_retourne_none(self):
        assert get_user(_req()) is None

    def test_retourne_utilisateur_authentifie(self):
        sid = create_session()
        nouveau = authenticate_session(sid, _UTILISATEUR)
        user = get_user(_req(nouveau))
        assert user["login"] == "jdupont"


class TestUtilisateurARole:
    def test_possede_le_role(self):
        sid = create_session()
        nouveau = authenticate_session(sid, _UTILISATEUR)
        assert user_has_role(_req(nouveau), "admin") is True

    def test_ne_possede_pas_le_role(self):
        sid = create_session()
        nouveau = authenticate_session(sid, _UTILISATEUR)
        assert user_has_role(_req(nouveau), "comptable") is False

    def test_sans_session_retourne_false(self):
        assert user_has_role(_req(), "admin") is False
