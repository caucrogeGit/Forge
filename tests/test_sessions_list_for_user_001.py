"""ADMIN-SESSIONS-VIEW-001 : voir les sessions d'un compte, sans les compromettre.

Révoquer était possible depuis `SESSIONS-DELETE-FOR-USER-001`, voir ne l'était
pas : l'exploitant déconnectait à l'aveugle, sans savoir combien de sessions
étaient ouvertes ni depuis quand.

Tout l'enjeu tient en une phrase : **un identifiant de session est le jeton
d'authentification lui même**. L'afficher donnerait à qui lit la page le pouvoir
d'usurper la session, et un écran d'administration est justement lu par
quelqu'un d'autre que son titulaire.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from core.sessions.contract import HANDLE_LENGTH, SessionStore, SessionSummary
from core.sessions.file_store import FileSessionStore
from core.sessions.keys import SESSION_KEY_AUTH_USER_ID as CLE
from core.sessions.memory_store import MemorySessionStore


@pytest.fixture(params=["memoire", "fichier"])
def store(request: pytest.FixtureRequest, tmp_path: Path) -> SessionStore:
    if request.param == "memoire":
        return MemorySessionStore()
    return FileSessionStore(sessions_dir=tmp_path / "sessions")


class TestAucunJetonExpose:
    """Le cœur du ticket."""

    def test_le_resume_ne_porte_aucun_identifiant_complet(
        self, store: SessionStore
    ) -> None:
        identifiant = store.create({CLE: 7})

        resume = store.list_for_user(7)[0]

        assert identifiant not in str(resume)
        assert resume.handle != identifiant

    def test_le_prefixe_est_trop_court_pour_servir_de_jeton(
        self, store: SessionStore
    ) -> None:
        store.create({CLE: 7})

        resume = store.list_for_user(7)[0]

        assert len(resume.handle) == HANDLE_LENGTH
        assert HANDLE_LENGTH < 16

    def test_le_resume_n_a_pas_de_champ_d_identifiant(self) -> None:
        """Un champ nommé `session_id` inviterait à l'afficher."""
        champs = SessionSummary.__dataclass_fields__
        assert "session_id" not in champs
        assert set(champs) == {"handle", "created_at", "expires_at", "is_current"}

    def test_le_prefixe_ne_permet_pas_de_revoquer(self, store: SessionStore) -> None:
        """La révocation passe par le compte, ou par la session que son titulaire connaît."""
        identifiant = store.create({CLE: 7})
        resume = store.list_for_user(7)[0]

        store.delete(resume.handle)

        assert store.get(identifiant) is not None, "un préfixe ne doit rien révoquer"


class TestListage:
    def test_seules_les_sessions_du_compte_sont_rendues(
        self, store: SessionStore
    ) -> None:
        store.create({CLE: 7})
        store.create({CLE: 7})
        store.create({CLE: 9})

        assert len(store.list_for_user(7)) == 2

    def test_une_session_anonyme_n_apparait_pas(self, store: SessionStore) -> None:
        store.create()
        assert store.list_for_user(7) == []

    def test_un_compte_sans_session_rend_une_liste_vide(
        self, store: SessionStore
    ) -> None:
        assert store.list_for_user(404) == []

    def test_une_identite_absente_ne_rend_rien(self, store: SessionStore) -> None:
        """`None` ne doit pas se confondre avec « toutes les sessions anonymes »."""
        store.create()
        assert store.list_for_user(None) == []

    def test_l_ordre_est_stable_du_plus_recent_au_plus_ancien(
        self, store: SessionStore
    ) -> None:
        """Un ordre de dictionnaire changerait d'un rafraîchissement à l'autre."""
        for _ in range(5):
            store.create({CLE: 7})

        expirations = [r.expires_at or 0.0 for r in store.list_for_user(7)]

        assert expirations == sorted(expirations, reverse=True)


class TestSessionCourante:
    def test_la_session_courante_est_signalee(self, store: SessionStore) -> None:
        """Sans elle, l'utilisateur ne saurait pas laquelle il ne doit pas fermer."""
        courante = store.create({CLE: 7})
        store.create({CLE: 7})

        resumes = store.list_for_user(7, current_session_id=courante)

        assert sum(1 for r in resumes if r.is_current) == 1

    def test_sans_session_courante_aucune_n_est_signalee(
        self, store: SessionStore
    ) -> None:
        store.create({CLE: 7})
        assert not any(r.is_current for r in store.list_for_user(7))


class TestDates:
    def test_les_deux_dates_sont_rendues(self, store: SessionStore) -> None:
        """L'écran n'a que les dates pour distinguer deux lignes."""
        store.create({CLE: 7})

        resume = store.list_for_user(7)[0]

        assert resume.created_at is not None
        assert resume.expires_at is not None
        assert resume.expires_at > resume.created_at

    def test_une_session_sans_date_de_creation_rend_none(
        self, store: SessionStore
    ) -> None:
        """Une session d'avant ce ticket n'en a pas : zéro se lirait comme 1970."""
        identifiant = store.create({CLE: 7})
        donnees = store.get(identifiant)
        assert donnees is not None
        donnees.pop("created_at", None)
        store.replace(identifiant, donnees)

        assert store.list_for_user(7)[0].created_at is None


class TestContrat:
    def test_les_stores_livres_satisfont_le_contrat(self, store: SessionStore) -> None:
        assert isinstance(store, SessionStore)

    def test_la_primitive_est_au_contrat(self) -> None:
        assert hasattr(SessionStore, "list_for_user")

    def test_le_resume_est_immuable(self) -> None:
        resume = SessionSummary(handle="abcd1234")
        with pytest.raises(Exception):
            resume.handle = "autre"  # type: ignore[misc]


class TestVoirPuisRevoquer:
    """Le parcours réel d'un écran de sessions."""

    def test_voir_puis_deconnecter_partout_sauf_ici(self, store: SessionStore) -> None:
        courante = store.create({CLE: 7})
        store.create({CLE: 7})
        store.create({CLE: 7})

        assert len(store.list_for_user(7, current_session_id=courante)) == 3

        revoquees = store.delete_for_user(7, except_session_id=courante)

        assert revoquees == 2
        restantes = store.list_for_user(7, current_session_id=courante)
        assert len(restantes) == 1
        assert restantes[0].is_current
