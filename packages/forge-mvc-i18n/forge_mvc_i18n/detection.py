# pyright: strict
"""Détection de la locale active (I18N-LOCALE-DETECTION-001).

Le paquet annonçait « locale et fallback » et ne savait pas d'où venait la
locale : `trans()` retombait sur une valeur **globale** de configuration, la
même pour tous les visiteurs. Une application multilingue devait donc écrire
sa propre détection, ce que la documentation ne disait pas.

La détection suit un ordre explicite, du plus intentionnel au plus supposé.

1. Le choix enregistré en session, posé par un geste de l'utilisateur.
2. L'en-tête `Accept-Language` du navigateur, qui exprime une préférence.
3. La locale par défaut de l'application.

Les fonctions sont **pures** et prennent des valeurs simples, jamais une
requête HTTP : elles se testent sans monter de serveur, et le paquet ne dépend
pas de la couche HTTP du cœur.

Rien ne se détecte tout seul. `trans()` ne change pas de comportement, et
l'application appelle `detect_locale` puis passe le résultat, comme le
principe 3 le demande.
"""
from __future__ import annotations

import re
from pathlib import Path

__all__ = [
    "SESSION_KEY_LOCALE",
    "available_locales",
    "parse_accept_language",
    "negotiate_locale",
    "detect_locale",
]

#: Clé de session portant la locale choisie par l'utilisateur.
#:
#: Nommée ici pour que l'application et le paquet désignent la même, plutôt que
#: de recopier une chaîne de part et d'autre.
SESSION_KEY_LOCALE = "_i18n_locale"

#: Une locale ne sert qu'à composer un nom de fichier `<locale>.json`.
#: Même expression que le traducteur, pour la même raison.
_LOCALE_RE = re.compile(r"^[A-Za-z0-9_-]+$")

#: `Accept-Language` est une entrée non fiable : on borne ce qu'on en lit.
#: Un en-tête de plusieurs kilo-octets ne doit pas coûter une analyse.
_MAX_HEADER_LENGTH = 512
_MAX_ENTRIES = 20


def available_locales(translations_dir: "str | Path" = "translations") -> list[str]:
    """Locales pour lesquelles un catalogue existe, triées.

    Sert de liste blanche à la négociation. Sans elle, un `Accept-Language`
    forgé ferait chercher un catalogue arbitraire, et l'en-tête vient du client.
    """
    dossier = Path(translations_dir)
    if not dossier.is_dir():
        return []
    return sorted(
        fichier.stem
        for fichier in dossier.glob("*.json")
        if _LOCALE_RE.fullmatch(fichier.stem)
    )


def parse_accept_language(header: "str | None") -> list[str]:
    """Locales d'un en-tête `Accept-Language`, de la plus voulue à la moins.

    Suit les facteurs de qualité (`q=`) de la RFC 9110. Une entrée sans `q`
    vaut 1, et `q=0` signifie un refus explicite, donc l'entrée est écartée.

    Les valeurs illisibles sont ignorées plutôt que de faire échouer la
    requête : un en-tête malformé ne doit pas rendre un site inaccessible.
    """
    if not header:
        return []
    brut = header.strip()[:_MAX_HEADER_LENGTH]

    pondérées: list[tuple[float, int, str]] = []
    for rang, morceau in enumerate(brut.split(",")[:_MAX_ENTRIES]):
        parties = morceau.split(";")
        étiquette = parties[0].strip()
        if not étiquette or étiquette == "*":
            continue
        if not _LOCALE_RE.fullmatch(étiquette):
            continue

        qualité = 1.0
        for paramètre in parties[1:]:
            nom, _, valeur = paramètre.partition("=")
            if nom.strip().lower() != "q":
                continue
            try:
                qualité = float(valeur.strip())
            except ValueError:
                qualité = 0.0
            break

        if qualité <= 0:
            continue
        # Le rang départage à qualité égale : l'ordre de l'en-tête fait foi,
        # et un tri instable rendrait la détection imprévisible.
        pondérées.append((qualité, -rang, étiquette))

    pondérées.sort(reverse=True)
    return [étiquette for _, _, étiquette in pondérées]


def negotiate_locale(voulues: "list[str]", disponibles: "list[str]") -> "str | None":
    """Première locale voulue qu'on sait servir, ou `None`.

    La correspondance est insensible à la casse, et `fr-FR` retombe sur `fr`
    quand seul `fr` a un catalogue : un navigateur annonce presque toujours une
    région, et exiger la correspondance exacte ne servirait jamais personne.

    L'inverse n'est pas vrai. `fr` ne choisit pas `fr-CA` : servir une variante
    régionale que personne n'a demandée serait une supposition, pas une
    négociation.
    """
    if not voulues or not disponibles:
        return None
    par_clé = {locale.lower(): locale for locale in disponibles}

    for voulue in voulues:
        clé = voulue.lower()
        if clé in par_clé:
            return par_clé[clé]
        base = clé.split("-")[0].split("_")[0]
        if base in par_clé:
            return par_clé[base]
    return None


def detect_locale(
    *,
    session_locale: "str | None" = None,
    accept_language: "str | None" = None,
    available: "list[str] | None" = None,
    default: "str | None" = None,
) -> "str | None":
    """Locale active, du choix le plus intentionnel au plus supposé.

    L'ordre est celui du module : la session, puis l'en-tête, puis le défaut.

    `available` borne les deux premières sources, qui viennent du client. Sans
    elle, elles sont refusées : mieux vaut rendre le défaut que de charger un
    catalogue qu'on n'a pas choisi de servir.

    `default` n'est pas filtré par `available`, l'application répondant de sa
    propre configuration. Rend `None` quand rien ne convient, à charge de
    l'appelant de décider.
    """
    disponibles = available or []

    if session_locale:
        choisie = negotiate_locale([session_locale], disponibles)
        if choisie is not None:
            return choisie

    négociée = negotiate_locale(parse_accept_language(accept_language), disponibles)
    if négociée is not None:
        return négociée

    return default
