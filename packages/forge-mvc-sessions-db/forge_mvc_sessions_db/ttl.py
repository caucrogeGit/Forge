# pyright: strict
"""Durée de vie par nature de session (`SESSIONS-TTL-PER-KIND-001`).

Le store portait **une** durée pour tout le monde, `DEFAULT_SESSION_TTL`. Les
trois natures de session n'ont pourtant ni le même risque ni le même usage.

| Nature | Ce qu'elle porte | Ce qu'une fuite coûte |
|---|---|---|
| `anonymous` | un jeton CSRF, un panier | presque rien |
| `authenticated` | une identité | l'accès au compte |
| `remembered` | une identité, sur des semaines | l'accès au compte, longtemps |

Une durée unique force donc un arbitrage perdant. Réglée court, elle déconnecte
les utilisateurs authentifiés toutes les heures. Réglée long, elle laisse
traîner des sessions anonymes par milliers, que la purge doit balayer et qui
occupent la table pour un jeton CSRF.

## Trois natures, fermées

Une quatrième nature inventée par une application rendrait la métrique et la
purge incomparables d'un projet à l'autre, ce qui est ce que ce champ doit
permettre.

## Une valeur de configuration illisible lève

Comme pour les quotas de `forge-mvc-files` et les limites de
`forge-mvc-images`. Retomber en silence sur le défaut donnerait une durée que
personne n'a écrite, et une session qui expire trop tôt se diagnostique très
mal.
"""
from __future__ import annotations

import os

__all__ = [
    "SessionTtlError",
    "KIND_ANONYMOUS",
    "KIND_AUTHENTICATED",
    "KIND_REMEMBERED",
    "SESSION_KINDS",
    "DEFAULT_TTLS",
    "ENV_PREFIX",
    "ttl_for",
    "normalize_kind",
]

#: Session sans identité. Un jeton CSRF, un panier, une locale.
KIND_ANONYMOUS = "anonymous"
#: Session authentifiée ordinaire.
KIND_AUTHENTICATED = "authenticated"
#: Session authentifiée de longue durée, « se souvenir de moi ».
KIND_REMEMBERED = "remembered"

#: Vocabulaire fermé des natures de session.
SESSION_KINDS = frozenset({KIND_ANONYMOUS, KIND_AUTHENTICATED, KIND_REMEMBERED})

#: Durées par défaut, en secondes.
#:
#: Deux heures pour l'anonyme, assez pour remplir un formulaire long, assez
#: court pour que la table ne se remplisse pas de jetons CSRF abandonnés.
#: Une heure pour l'authentifié, valeur historique du store, inchangée pour ne
#: pas raccourcir sans prévenir les sessions des projets existants.
#: Trente jours pour le souvenir, durée usuelle d'un « se souvenir de moi ».
DEFAULT_TTLS: "dict[str, int]" = {
    KIND_ANONYMOUS: 2 * 3600,
    KIND_AUTHENTICATED: 3600,
    KIND_REMEMBERED: 30 * 24 * 3600,
}

ENV_PREFIX = "SESSION_TTL_"


class SessionTtlError(ValueError):
    """Nature inconnue, ou durée mal déclarée."""


def normalize_kind(kind: object) -> str:
    """Nature normalisée.

    Raises:
        SessionTtlError: la nature n'est pas l'une des trois. Une nature
            inventée rendrait la métrique et la purge incomparables.
    """
    valeur = str(kind or "").strip().lower()
    if valeur not in SESSION_KINDS:
        raise SessionTtlError(
            f"nature de session inconnue : {kind!r}. Attendu "
            f"{', '.join(sorted(SESSION_KINDS))}."
        )
    return valeur


def ttl_for(kind: str, *, env: "dict[str, str] | None" = None) -> int:
    """Durée de vie, en secondes, de la nature demandée.

    Lue de `SESSION_TTL_ANONYMOUS`, `SESSION_TTL_AUTHENTICATED` ou
    `SESSION_TTL_REMEMBERED`, avec le défaut de la nature à défaut.

    Raises:
        SessionTtlError: nature inconnue, ou valeur illisible ou non positive.
            Retomber en silence sur le défaut donnerait une durée que personne
            n'a écrite, et une session qui expire trop tôt se diagnostique très
            mal.
    """
    nature = normalize_kind(kind)
    source = env if env is not None else dict(os.environ)
    nom = f"{ENV_PREFIX}{nature.upper()}"
    brut = (source.get(nom) or "").strip()
    if not brut:
        return DEFAULT_TTLS[nature]
    try:
        valeur = int(brut)
    except ValueError:
        raise SessionTtlError(
            f"{nom} doit être un nombre de secondes entier. Reçu : {brut!r}."
        ) from None
    if valeur <= 0:
        raise SessionTtlError(
            f"{nom} doit être strictement positif. Reçu : {valeur}. Une durée "
            "nulle expirerait la session avant même de la rendre."
        )
    return valeur
