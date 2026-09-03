# pyright: strict
"""Authentifier un client de test (`TESTING-LOGIN-AS-001`).

Tester une page protégée demandait de jouer le formulaire de connexion, donc
d'avoir un utilisateur en base, un mot de passe haché, et un jeton CSRF. Un
test de « la page d'administration refuse un visiteur » passait ainsi par cinq
étapes qui n'ont rien à voir avec ce qu'il vérifie, et cassait dès que le
formulaire changeait.

## L'aide passe par le vrai magasin de sessions

Elle **n'écrit pas un cookie signé à la main**. Elle crée une session par le
magasin configuré, l'authentifie par la méthode que le cœur emploie, et pose le
cookie que le serveur aurait posé.

Fabriquer le cookie soi même produirait un jumeau : le test passerait avec une
session que la production aurait refusée, et les deux dériveraient sans que
rien ne le signale.

## Ce que l'aide ne fait pas

Elle ne crée **aucun utilisateur en base**. Le contenu de la session est celui
que l'appelant donne, et il n'a pas à correspondre à une ligne : un test de
contrôle d'accès vérifie ce que le middleware fait d'une session, pas ce que le
dépôt contient.

Un test qui a besoin des deux crée son utilisateur lui même, comme il le ferait
en production.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from forge_mvc_testing.client import ForgeTestClient

__all__ = [
    "AuthHelperError",
    "DEFAULT_TTL_SECONDS",
    "login_as",
    "logout",
    "session_of",
]

#: Durée par défaut d'une session de test. Une heure : assez pour un scénario,
#: assez court pour qu'un test qui dépendrait de l'expiration se voie.
DEFAULT_TTL_SECONDS = 3600


class AuthHelperError(RuntimeError):
    """L'authentification de test n'a pas pu être posée."""


def login_as(
    client: "ForgeTestClient",
    user_id: object,
    *,
    roles: "list[str] | tuple[str, ...] | None" = None,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
    **extra: Any,
) -> str:
    """Authentifie `client` et rend l'identifiant de session posé.

    ```python
    login_as(client, 42, roles=["admin"])
    assert client.get("/admin").status == 200
    ```

    `roles` est rangé dans la session sous la clé que le RBAC y cherche. Le
    paquet ne dépend pas de `forge-mvc-rbac`, aucun opt-in n'important un
    autre : il pose une donnée, et le contrôle d'accès en fait ce qu'il veut.

    Raises:
        AuthHelperError: le magasin de sessions a refusé l'authentification.
    """
    from core.sessions.access import SESSION_COOKIE_NAME
    from core.sessions.keys import SESSION_KEY_AUTH_USER_ID
    from core.sessions.manager import get_session_store

    magasin = get_session_store()
    identifiant = magasin.create()

    donnees: dict[str, Any] = {"id": user_id, **extra}
    if roles is not None:
        donnees["roles"] = list(roles)

    nouveau = magasin.authenticate(identifiant, donnees, ttl_seconds)
    if nouveau is None:
        raise AuthHelperError(
            "le magasin de sessions a refusé l'authentification : la session "
            "créée n'existe plus. Un magasin partagé entre tests, purgé entre "
            "deux, en est la cause la plus fréquente."
        )

    # La clé canonique du pont d'authentification, que le middleware lit.
    # L'omettre laisserait une session « authentifiée » que le cœur ne
    # reconnaît pas, et le test échouerait pour une raison illisible.
    courant = magasin.get(nouveau) or {}
    courant[SESSION_KEY_AUTH_USER_ID] = user_id
    magasin.set(nouveau, courant)

    client.cookies[SESSION_COOKIE_NAME] = nouveau
    return nouveau


def logout(client: "ForgeTestClient") -> None:
    """Supprime la session du client et son cookie.

    La session est **détruite** dans le magasin, pas seulement oubliée du
    client : oublier le cookie sans détruire la session laisserait un test de
    déconnexion passer alors que la session reste utilisable par qui la
    connaît.
    """
    from core.sessions.access import SESSION_COOKIE_NAME
    from core.sessions.manager import get_session_store

    identifiant = client.cookies.pop(SESSION_COOKIE_NAME, None)
    if identifiant:
        get_session_store().delete(identifiant)


def session_of(client: "ForgeTestClient") -> "dict[str, Any] | None":
    """Contenu de la session du client, ou `None` s'il n'en a pas.

    Sert aux assertions de `forge_mvc_testing.assertions`, et à un test qui
    veut vérifier ce qu'un contrôleur a rangé en session.
    """
    from core.sessions.access import SESSION_COOKIE_NAME
    from core.sessions.manager import get_session_store

    identifiant = client.cookies.get(SESSION_COOKIE_NAME)
    if not identifiant:
        return None
    return get_session_store().get(identifiant)
