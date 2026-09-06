"""SESSIONS-DELETE-FOR-USER-DEPRECATED-DOOR-001 : révoquer atteint les deux portes.

Forge porte deux représentations de l'identité en session, et un pont entre
elles. `get_authenticated_user_id` lit les deux : la clé canonique
`_auth_user_id` que pose `login_user`, et la forme legacy
`{"authenticated": True, "user": {...}}` que pose `authenticate_session`,
dépréciée mais toujours livrée.

`delete_for_user` ne lisait que la première, sans pont. Une session ouverte par
la porte dépréciée s'authentifiait donc parfaitement et **survivait à la
révocation** : la mesure rendait 0 supprimée, session intacte.

Ce que cela coûtait : une application encore sur ce chemin, activant un second
facteur ou changeant un mot de passe, croyait avoir fermé les autres sessions
(`MFA-SESSION-INVALIDATION-001`, `SESSIONS-DELETE-FOR-USER-001`). Une opération
de sécurité qui ne fait rien en silence est pire qu'une qui échoue bruyamment.

La correction fait **converger** les deux représentations, la porte dépréciée
posant désormais la clé canonique, plutôt qu'ajouter un second pont dans chaque
magasin : c'est la direction de l'ADR-086.
"""
from __future__ import annotations

import warnings
from typing import Any

import pytest

from core.sessions.keys import SESSION_KEY_AUTH_USER_ID


@pytest.fixture
def magasin():
    import core.forge as forge
    from core.sessions.manager import get_session_store

    forge.configure(app_name="test_revocation")
    return get_session_store()


def _ouvrir(magasin: Any, user: dict[str, Any]) -> "str | None":
    """Ouvre une session par la porte dépréciée, sans en écouter l'avertissement."""
    from core.security.session import authenticate_session

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return authenticate_session(magasin.create(), user)


class TestRevocationParLaPorteDepreciee:

    def test_une_session_de_cette_porte_est_revocable(self, magasin: Any) -> None:
        """Elle rendait 0, et la session survivait."""
        identifiant = _ouvrir(magasin, {"id": 7, "email": "x@y.z"})

        assert magasin.delete_for_user(7) == 1
        assert magasin.get(identifiant) is None

    def test_toutes_les_sessions_du_compte_partent(self, magasin: Any) -> None:
        une = _ouvrir(magasin, {"id": 7})
        deux = _ouvrir(magasin, {"id": 7})

        assert magasin.delete_for_user(7) == 2
        assert magasin.get(une) is None
        assert magasin.get(deux) is None

    def test_les_autres_comptes_ne_sont_pas_touches(self, magasin: Any) -> None:
        _ouvrir(magasin, {"id": 7})
        autre = _ouvrir(magasin, {"id": 9})

        magasin.delete_for_user(7)

        assert magasin.get(autre) is not None

    def test_la_session_epargnee_survit(self, magasin: Any) -> None:
        """Activer un second facteur ne doit pas déconnecter qui l'active."""
        gardee = _ouvrir(magasin, {"id": 7})
        autre = _ouvrir(magasin, {"id": 7})

        magasin.delete_for_user(7, except_session_id=gardee)

        assert magasin.get(gardee) is not None
        assert magasin.get(autre) is None


class TestLaCleCanonique:

    def test_elle_est_posee_a_cote_de_la_forme_legacy(self, magasin: Any) -> None:
        identifiant = _ouvrir(magasin, {"id": 7})
        donnees = magasin.get(identifiant) or {}

        assert donnees.get(SESSION_KEY_AUTH_USER_ID) == 7
        assert donnees.get("authenticated") is True, "la forme legacy reste lisible"

    @pytest.mark.parametrize("identite", ["sept", None, 0, -1, True, 3.5])
    def test_un_identifiant_qui_n_est_pas_un_entier_positif_ne_la_pose_pas(
        self, magasin: Any, identite: Any
    ) -> None:
        """Le pont exige déjà un entier positif : y écrire autre chose serait illisible."""
        identifiant = _ouvrir(magasin, {"id": identite})
        donnees = magasin.get(identifiant) or {}

        assert SESSION_KEY_AUTH_USER_ID not in donnees

    def test_l_authentification_par_le_pont_marche_toujours(
        self, magasin: Any
    ) -> None:
        """Faire converger les représentations ne doit pas casser la lecture."""
        from core.auth.session import get_authenticated_user_id
        from core.sessions.access import SESSION_COOKIE_NAME

        identifiant = _ouvrir(magasin, {"id": 7})

        class _Requete:
            headers = {"Cookie": f"{SESSION_COOKIE_NAME}={identifiant}"}

        assert get_authenticated_user_id(_Requete()) == 7


class TestLaPorteCanonique:
    """Elle marchait déjà : la correction ne doit pas la perdre au passage."""

    def test_une_session_canonique_reste_revocable(self, magasin: Any) -> None:
        identifiant = magasin.create()
        donnees = magasin.get(identifiant) or {}
        donnees[SESSION_KEY_AUTH_USER_ID] = 42
        magasin.set(identifiant, donnees)

        assert magasin.delete_for_user(42) == 1

    def test_une_session_anonyme_n_est_jamais_touchee(self, magasin: Any) -> None:
        anonyme = magasin.create()
        _ouvrir(magasin, {"id": 7})

        magasin.delete_for_user(7)

        assert magasin.get(anonyme) is not None
