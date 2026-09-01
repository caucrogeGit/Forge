"""SESSIONS-DELETE-FOR-USER-001 : révoquer toutes les sessions d'un utilisateur.

Le contrat `SessionStore` n'avait que `delete(session_id)`. Rien ne permettait
de fermer les sessions déjà ouvertes d'un compte, alors que trois événements
l'exigent : l'activation d'un second facteur, le changement de mot de passe et
la déconnexion à distance. Une session ouverte leur survivait.

Les trois stores livrés implémentent la primitive. Les deux stores locaux
balaient, le store BDD interroge une colonne indexée.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from core.sessions.contract import SessionStore
from core.sessions.file_store import FileSessionStore
from core.sessions.keys import SESSION_KEY_AUTH_USER_ID as CLE_UTILISATEUR
from core.sessions.memory_store import MemorySessionStore


@pytest.fixture(params=["memoire", "fichier"])
def store(request: pytest.FixtureRequest, tmp_path: Path) -> SessionStore:
    """Les deux stores livrés par le cœur, exercés par les mêmes tests."""
    if request.param == "memoire":
        return MemorySessionStore()
    return FileSessionStore(sessions_dir=tmp_path / "sessions")


class TestRevocation:
    def test_les_sessions_du_compte_tombent(self, store: SessionStore) -> None:
        premiere = store.create({CLE_UTILISATEUR: 7})
        seconde = store.create({CLE_UTILISATEUR: 7})

        assert store.delete_for_user(7) == 2
        assert store.get(premiere) is None
        assert store.get(seconde) is None

    def test_les_sessions_des_autres_survivent(self, store: SessionStore) -> None:
        """Le point qui distingue une révocation d'une purge."""
        cible = store.create({CLE_UTILISATEUR: 7})
        voisine = store.create({CLE_UTILISATEUR: 9})

        assert store.delete_for_user(7) == 1
        assert store.get(cible) is None
        assert store.get(voisine) is not None

    def test_une_session_anonyme_n_est_jamais_touchee(self, store: SessionStore) -> None:
        anonyme = store.create()

        assert store.delete_for_user(7) == 0
        assert store.get(anonyme) is not None

    def test_un_compte_sans_session_ne_leve_pas(self, store: SessionStore) -> None:
        assert store.delete_for_user(404) == 0

    def test_identite_absente_ne_revoque_rien(self, store: SessionStore) -> None:
        """`None` ne doit pas se confondre avec « toutes les sessions anonymes »."""
        anonyme = store.create()

        assert store.delete_for_user(None) == 0
        assert store.get(anonyme) is not None

    def test_la_revocation_est_idempotente(self, store: SessionStore) -> None:
        store.create({CLE_UTILISATEUR: 7})

        assert store.delete_for_user(7) == 1
        assert store.delete_for_user(7) == 0


class TestContrat:
    def test_les_stores_livres_satisfont_le_contrat(self, store: SessionStore) -> None:
        """`SessionStore` est `runtime_checkable` : une méthode manquante s'y voit."""
        assert isinstance(store, SessionStore)

    def test_la_primitive_est_au_contrat(self) -> None:
        assert hasattr(SessionStore, "delete_for_user")


class TestIdentitePartagee:
    """La clé d'identité était dupliquée en dur dans `core.security.session`."""

    def test_une_seule_definition(self) -> None:
        from core.auth.session import AUTH_USER_ID_SESSION_KEY

        assert AUTH_USER_ID_SESSION_KEY is CLE_UTILISATEUR

    def test_core_security_ne_la_duplique_plus(self) -> None:
        import core.security.session as module

        source = Path(module.__file__).read_text(encoding="utf-8")
        assert '"_auth_user_id"' not in source, (
            "la clé est redevenue une chaîne en dur dans core/security/session.py"
        )


class TestSessionAuthentifieeReelle:
    """La révocation doit voir l'identité telle que `login_user` la pose."""

    def test_une_session_posee_par_login_user_est_revocable(
        self, store: SessionStore
    ) -> None:
        from core.auth.session import AUTH_USER_ID_SESSION_KEY

        session_id = store.create()
        donnees = store.get(session_id)
        assert donnees is not None
        donnees[AUTH_USER_ID_SESSION_KEY] = 42
        store.set(session_id, donnees)

        assert store.delete_for_user(42) == 1
        assert store.get(session_id) is None
