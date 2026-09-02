# pyright: strict
"""Règle de pluriel minimale (`I18N-PLURALS-001`).

`trans()` rend une chaîne unique par clé. Afficher « 1 articles » ou écrire
deux clés, `article_un` et `article_plusieurs`, avec un `if` dans chaque
gabarit, sont les deux contournements qu'on rencontre, et aucun ne tient quand
une troisième langue arrive.

## Ce que Forge implémente, et ce qu'il n'implémente pas

CLDR définit **six** catégories de pluriel, `zero`, `one`, `two`, `few`,
`many`, `other`, et une règle propre à chacune des quelque deux cents langues
qu'il couvre. L'arabe en utilise six, le russe quatre, le gallois six.

Forge en implémente **deux**, `one` et `other`, avec une règle par famille de
langues. C'est exact pour le français, l'anglais et la plupart des langues
d'Europe occidentale, et **faux** pour le russe, l'arabe, le polonais et le
gallois.

Ce n'est pas un choix par facilité, c'est une frontière assumée. Une
implémentation partielle de CLDR serait pire qu'une absence : elle donnerait
l'impression de couvrir une langue qu'elle massacre. Une application qui doit
traduire vers l'une de ces langues emploie une bibliothèque d'internationalisation
complète, et le module le dit plutôt que de le laisser découvrir en production.

## Le format de catalogue

    {
      "articles": {"one": "{n} article", "other": "{n} articles"}
    }

Une clé dont la valeur est une chaîne reste une clé ordinaire : le format
existant continue de fonctionner sans changement.
"""
from __future__ import annotations

from typing import Any

__all__ = [
    "PluralError",
    "PLURAL_FORMS",
    "SINGULAR_INCLUDES_ZERO",
    "UNSUPPORTED_LANGUAGES",
    "plural_form",
    "select_plural",
    "language_of",
]


class PluralError(ValueError):
    """Forme de pluriel absente, ou catalogue mal formé."""


#: Les deux seules formes que Forge distingue.
PLURAL_FORMS = ("one", "other")

#: Langues où zéro prend le singulier. Le français écrit « 0 article ».
SINGULAR_INCLUDES_ZERO = frozenset({"fr", "pt", "hy", "ak", "bh", "ln", "mg", "ti"})

#: Langues dont la règle réelle demande plus de deux formes. Le module ne les
#: couvre pas, et le dit : `plural_form` lève plutôt que de rendre une forme
#: qu'elle sait fausse.
UNSUPPORTED_LANGUAGES = frozenset({
    "ar", "ru", "uk", "be", "pl", "cs", "sk", "lt", "lv", "hr", "sr", "bs",
    "cy", "ga", "gd", "mt", "sl", "ro",
})


def language_of(locale: str) -> str:
    """Code de langue d'une locale. `fr_BE` et `fr-BE` donnent `fr`.

    La règle de pluriel dépend de la langue, jamais de la région : le français
    de Belgique et celui de France comptent pareil.
    """
    return (locale or "").strip().lower().replace("_", "-").split("-")[0]


def plural_form(count: int, locale: str) -> str:
    """Forme à employer, `one` ou `other`.

    Raises:
        PluralError: la langue demande plus de deux formes. Rendre `one` ou
            `other` pour du russe produirait une phrase fausse dans un cas sur
            deux, ce qui est pire qu'un refus visible au développement.
    """
    langue = language_of(locale)
    if langue in UNSUPPORTED_LANGUAGES:
        raise PluralError(
            f"la langue {langue!r} demande plus de deux formes de pluriel, que "
            "Forge n'implémente pas. Une implémentation partielle donnerait "
            "l'impression de couvrir une langue qu'elle massacre : employez "
            "une bibliothèque d'internationalisation complète."
        )
    if not isinstance(count, int) or isinstance(count, bool):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise PluralError(f"le compte doit être un entier. Reçu : {count!r}.")

    nombre = abs(count)
    if langue in SINGULAR_INCLUDES_ZERO:
        return "one" if nombre < 2 else "other"
    return "one" if nombre == 1 else "other"


def select_plural(value: Any, count: int, locale: str) -> str:
    """Choisit la forme dans une valeur de catalogue.

    Une valeur qui est une chaîne est rendue telle quelle : le format existant
    continue de fonctionner, et une clé sans pluriel n'a pas à en gagner un.

    Raises:
        PluralError: la valeur est un dictionnaire auquel manque la forme
            retenue. Retomber sur l'autre forme afficherait « 3 article » sans
            que rien ne le signale.
    """
    if isinstance(value, str):
        return value
    if not isinstance(value, dict):
        raise PluralError(
            f"valeur de catalogue inattendue : {type(value).__name__}. Attendu "
            "une chaîne, ou un objet portant les formes « one » et « other »."
        )

    formes: "dict[str, Any]" = value  # pyright: ignore[reportUnknownVariableType]
    forme = plural_form(count, locale)
    choisie = formes.get(forme)
    if not isinstance(choisie, str):
        disponibles = ", ".join(sorted(str(k) for k in formes)) or "<aucune>"
        raise PluralError(
            f"forme de pluriel « {forme} » absente du catalogue. Formes "
            f"présentes : {disponibles}. Retomber sur l'autre afficherait une "
            "phrase fausse sans que rien ne le signale."
        )
    return choisie
