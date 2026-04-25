from types import SimpleNamespace
from core.security.session import (
    creer_session, get_session, supprimer_session,
    authentifier_session, est_authentifie,
    get_utilisateur, utilisateur_a_role,
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
    cookie = f"session_id={session_id}" if session_id else ""
    return SimpleNamespace(headers={"Cookie": cookie}, ip="127.0.0.1")


class TestCreerSession:
    def test_retourne_chaine_hex(self):
        sid = creer_session()
        assert isinstance(sid, str) and len(sid) == 64

    def test_session_existe(self):
        sid = creer_session()
        assert get_session(sid) is not None

    def test_pas_authentifiee_par_defaut(self):
        sid = creer_session()
        assert get_session(sid)["authentifie"] is False

    def test_csrf_token_present(self):
        sid = creer_session()
        assert len(get_session(sid)["csrf_token"]) == 32


class TestGetSession:
    def test_id_inconnu_retourne_none(self):
        assert get_session("inexistant") is None


class TestSupprimerSession:
    def test_session_supprimee(self):
        sid = creer_session()
        supprimer_session(sid)
        assert get_session(sid) is None

    def test_suppression_id_inexistant_sans_erreur(self):
        supprimer_session("inexistant")  # ne doit pas lever


class TestAuthentifierSession:
    def test_retourne_nouvel_id(self):
        sid = creer_session()
        nouveau = authentifier_session(sid, _UTILISATEUR)
        assert nouveau is not None
        assert nouveau != sid

    def test_ancien_id_supprime(self):
        sid = creer_session()
        authentifier_session(sid, _UTILISATEUR)
        assert get_session(sid) is None

    def test_nouvelle_session_authentifiee(self):
        sid = creer_session()
        nouveau = authentifier_session(sid, _UTILISATEUR)
        assert get_session(nouveau)["authentifie"] is True

    def test_utilisateur_stocke(self):
        sid = creer_session()
        nouveau = authentifier_session(sid, _UTILISATEUR)
        user = get_session(nouveau)["utilisateur"]
        assert user["login"] == "jdupont"
        assert "admin" in user["roles"]

    def test_id_invalide_retourne_none(self):
        assert authentifier_session("faux_id", _UTILISATEUR) is None


class TestEstAuthentifie:
    def test_sans_cookie_retourne_false(self):
        assert est_authentifie(_req()) is False

    def test_session_non_authentifiee_retourne_false(self):
        sid = creer_session()
        assert est_authentifie(_req(sid)) is False

    def test_session_authentifiee_retourne_true(self):
        sid = creer_session()
        nouveau = authentifier_session(sid, _UTILISATEUR)
        assert est_authentifie(_req(nouveau)) is True


class TestGetUtilisateur:
    def test_sans_session_retourne_none(self):
        assert get_utilisateur(_req()) is None

    def test_retourne_utilisateur_authentifie(self):
        sid = creer_session()
        nouveau = authentifier_session(sid, _UTILISATEUR)
        user = get_utilisateur(_req(nouveau))
        assert user["login"] == "jdupont"


class TestUtilisateurARole:
    def test_possede_le_role(self):
        sid = creer_session()
        nouveau = authentifier_session(sid, _UTILISATEUR)
        assert utilisateur_a_role(_req(nouveau), "admin") is True

    def test_ne_possede_pas_le_role(self):
        sid = creer_session()
        nouveau = authentifier_session(sid, _UTILISATEUR)
        assert utilisateur_a_role(_req(nouveau), "comptable") is False

    def test_sans_session_retourne_false(self):
        assert utilisateur_a_role(_req(), "admin") is False
