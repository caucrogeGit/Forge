# pyright: strict
"""Assertions de session et de jeton anti-rejeu (`TESTING-ASSERTIONS-001`).

Vérifier qu'un contrôleur a bien authentifié, qu'il a bien fait tourner
l'identifiant de session, ou qu'un jeton à usage unique a bien été consommé,
demandait d'aller lire le magasin à la main dans chaque test.

Chacun écrivait donc sa version, et aucune ne disait la même chose en cas
d'échec : « assert store.get(sid)["authenticated"] » rend `KeyError` quand la
session n'existe plus, message qui n'apprend rien.

## Ce que ces assertions apportent

Un **message qui nomme la cause**. Une assertion de test n'a pas d'autre
raison d'exister que de raccourcir le chemin entre l'échec et la correction.

Elles ne remplacent pas `assert` : ce sont des fonctions qui lèvent
`AssertionError`, employées là où le diagnostic compte.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from forge_mvc_testing.client import ForgeTestClient

__all__ = [
    "assert_authenticated",
    "assert_not_authenticated",
    "assert_session_key",
    "assert_session_rotated",
    "assert_no_session",
    "assert_token_consumed",
    "assert_token_valid",
]


def _session(client: "ForgeTestClient") -> "tuple[str | None, dict[str, Any] | None]":
    from core.sessions.access import SESSION_COOKIE_NAME
    from core.sessions.manager import get_session_store

    identifiant = client.cookies.get(SESSION_COOKIE_NAME)
    if not identifiant:
        return (None, None)
    return (identifiant, get_session_store().get(identifiant))


def assert_authenticated(client: "ForgeTestClient") -> None:
    """Le client porte une session authentifiée.

    Distingue les trois échecs possibles, qu'un `assert` unique confondrait :
    pas de cookie, cookie pointant sur une session disparue, session présente
    mais non authentifiée.
    """
    identifiant, donnees = _session(client)
    if identifiant is None:
        raise AssertionError(
            "le client ne porte aucun cookie de session : rien n'a été "
            "authentifié, ou la réponse n'a pas posé le cookie."
        )
    if donnees is None:
        raise AssertionError(
            f"le cookie de session {identifiant[:8]}… ne correspond à aucune "
            "session : elle a expiré, été purgée, ou détruite entre temps."
        )
    if not donnees.get("authenticated"):
        raise AssertionError(
            "la session existe mais n'est pas authentifiée. Clés présentes : "
            f"{', '.join(sorted(donnees)) or '<aucune>'}."
        )


def assert_not_authenticated(client: "ForgeTestClient") -> None:
    """Le client ne porte aucune session authentifiée.

    Une session anonyme est acceptée : un visiteur en a une dès qu'il reçoit
    un jeton CSRF, et exiger l'absence totale de session ferait échouer un test
    de déconnexion parfaitement correct.
    """
    _, donnees = _session(client)
    if donnees is not None and donnees.get("authenticated"):
        utilisateur = donnees.get("user")
        raise AssertionError(
            f"le client est authentifié alors qu'il ne devrait pas : {utilisateur!r}."
        )


def assert_no_session(client: "ForgeTestClient") -> None:
    """Le client ne porte aucune session, pas même anonyme."""
    identifiant, donnees = _session(client)
    if donnees is not None:
        raise AssertionError(
            f"le client porte encore la session {str(identifiant)[:8]}…, avec "
            f"{len(donnees)} clé(s)."
        )


def assert_session_key(
    client: "ForgeTestClient", key: str, expected: Any = ...
) -> Any:
    """La session porte `key`. Rend sa valeur.

    Sans `expected`, vérifie seulement la présence. Avec, compare et montre les
    deux valeurs en cas d'écart : « attendu 3, trouvé '3' » se corrige, « faux »
    ne se corrige pas.
    """
    _, donnees = _session(client)
    if donnees is None:
        raise AssertionError(
            f"aucune session : impossible d'y chercher la clé {key!r}."
        )
    if key not in donnees:
        raise AssertionError(
            f"clé {key!r} absente de la session. Clés présentes : "
            f"{', '.join(sorted(donnees)) or '<aucune>'}."
        )
    valeur = donnees[key]
    if expected is not ... and valeur != expected:
        raise AssertionError(
            f"session[{key!r}] : attendu {expected!r}, trouvé {valeur!r}."
        )
    return valeur


def assert_session_rotated(before: str, client: "ForgeTestClient") -> str:
    """L'identifiant de session a changé, et l'ancien n'est plus utilisable.

    La rotation à la connexion est ce qui empêche la fixation de session. Un
    test qui vérifierait seulement que l'identifiant a changé laisserait passer
    une rotation qui garde l'ancienne session vivante, ce qui ne protège de
    rien.
    """
    from core.sessions.access import SESSION_COOKIE_NAME
    from core.sessions.manager import get_session_store

    apres = client.cookies.get(SESSION_COOKIE_NAME)
    if not apres:
        raise AssertionError(
            "le client ne porte plus de cookie de session : ce n'est pas une "
            "rotation mais une déconnexion."
        )
    if apres == before:
        raise AssertionError(
            f"l'identifiant de session n'a pas changé ({before[:8]}…) : une "
            "session non renouvelée à la connexion ouvre la fixation de session."
        )
    if get_session_store().get(before) is not None:
        raise AssertionError(
            f"l'ancienne session {before[:8]}… est toujours vivante après "
            "rotation : changer l'identifiant sans détruire l'ancien ne "
            "protège de rien."
        )
    return apres


def assert_token_valid(store: Any, token: str, *, subject: object = None) -> None:
    """Le jeton anti-rejeu est encore utilisable.

    `store` expose `is_used(token)` ou `has(token)`, contrat des magasins
    anti-rejeu du MFA. Le duck typing est délibéré : `forge-mvc-testing` ne
    dépend d'aucun opt-in.
    """
    if _token_used(store, token, subject):
        raise AssertionError(
            f"le jeton {token[:8]}… est déjà consommé alors qu'il devrait "
            "encore être valide."
        )


def assert_token_consumed(store: Any, token: str, *, subject: object = None) -> None:
    """Le jeton anti-rejeu a bien été consommé.

    C'est l'assertion qui manquait le plus : un jeton à usage unique qui reste
    utilisable après emploi est une faille silencieuse, et rien ne la révèle
    sans la vérifier explicitement.
    """
    if not _token_used(store, token, subject):
        raise AssertionError(
            f"le jeton {token[:8]}… est encore utilisable après emploi : un "
            "jeton à usage unique doit être consommé, sans quoi il est "
            "rejouable."
        )


def _token_used(store: Any, token: str, subject: object) -> bool:
    """Interroge un magasin anti-rejeu, quel que soit le nom de sa méthode."""
    for nom in ("is_used", "has", "contains", "seen"):
        methode = getattr(store, nom, None)
        if callable(methode):
            try:
                return bool(methode(subject, token) if subject is not None else methode(token))
            except TypeError:
                return bool(methode(token))
    raise AssertionError(
        f"{type(store).__name__} n'expose aucune méthode d'interrogation "
        "connue (is_used, has, contains, seen) : impossible de dire si le "
        "jeton est consommé."
    )
