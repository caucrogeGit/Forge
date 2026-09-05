# pyright: strict
from __future__ import annotations

import json
import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

import core.forge as _forge
from forge_mvc_i18n.exceptions import I18nError, TranslationCatalogError
from forge_mvc_i18n.plurals import (
    PLURAL_FORMS,
    PluralError,
    UNSUPPORTED_LANGUAGES,
    language_of,
    select_plural,
)

#: Valeur d'une entrée de catalogue : un texte, ou les formes d'un pluriel.
#:
#: Le second cas était **refusé au chargement** alors que `select_plural` était
#: écrite pour lui, sa docstring disant « choisit la forme dans une valeur de
#: catalogue » (`I18N-PLURAL-CATALOG-REACHABLE-001`). L'entrée que la fonction
#: attendait ne pouvait donc pas venir d'un catalogue, et le pluriel n'était
#: joignable qu'en construisant le dictionnaire à la main.
CatalogValue = str | dict[str, str]

# Une locale ne sert qu'à composer un nom de fichier `<locale>.json` : on
# interdit tout caractère de chemin (`/`, `\`, `.`, NUL) pour fermer le
# traversal (I18N-LOCALE-TRAVERSAL-GUARD-001). Couvre fr, en-US, pt_BR.
_LOCALE_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def get_default_locale() -> str:
    return _forge.get("i18n_default_locale")


def set_default_locale(locale: str) -> None:
    if not isinstance(locale, str) or not locale.strip():  # pyright: ignore[reportUnnecessaryIsInstance]
        raise I18nError("La locale par défaut doit être une chaîne non vide.")
    _forge.configure(i18n_default_locale=locale)


def get_fallback_locale() -> str | None:
    return _forge.get("i18n_fallback_locale")


def set_fallback_locale(locale: str | None) -> None:
    if locale is not None and (not isinstance(locale, str) or not locale.strip()):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise I18nError("La locale de fallback doit être une chaîne non vide ou None.")
    _forge.configure(i18n_fallback_locale=locale)


@lru_cache(maxsize=None)
def _load_catalog_cached(locale: str, translations_dir: str) -> dict[str, CatalogValue]:
    if not _LOCALE_RE.fullmatch(locale):
        raise TranslationCatalogError(
            f"Locale invalide : {locale!r} (caractères de chemin interdits)"
        )
    path = Path(translations_dir) / f"{locale}.json"
    if not path.is_file():
        raise TranslationCatalogError(f"Catalogue introuvable : {path}")
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TranslationCatalogError(f"JSON invalide dans {path} : {exc}") from exc
    if not isinstance(parsed, dict):
        raise TranslationCatalogError(f"Le catalogue {path} doit être un objet JSON")
    data = cast("dict[Any, Any]", parsed)
    langue = language_of(locale)
    for key, value in data.items():
        if not isinstance(key, str):
            raise TranslationCatalogError(f"Les clés doivent être des chaînes dans {path}")
        if isinstance(value, str):
            continue
        if not isinstance(value, dict):
            raise TranslationCatalogError(
                f"La clé « {key} » de {path} doit porter une chaîne, ou un objet "
                f"portant les formes {', '.join(PLURAL_FORMS)}."
            )
        _valider_formes(key, cast("dict[Any, Any]", value), path, langue)
    return cast("dict[str, CatalogValue]", data)


def _valider_formes(
    key: str, formes: "dict[Any, Any]", path: Path, langue: str
) -> None:
    """Refuse au **chargement** un pluriel qui casserait à l'affichage.

    Une forme absente ne se voit sinon qu'à la requête qui porte le nombre
    correspondant : la page marche pour un élève et casse pour deux.
    """
    if langue in UNSUPPORTED_LANGUAGES:
        raise TranslationCatalogError(
            f"La clé « {key} » de {path} est pluralisée, mais la langue "
            f"« {langue} » demande plus de deux formes, que ce module ne "
            "couvre pas. Écrivez des clés distinctes."
        )
    manquantes = [f for f in PLURAL_FORMS if f not in formes]
    if manquantes:
        raise TranslationCatalogError(
            f"La clé « {key} » de {path} ne porte pas la forme "
            f"{', '.join(manquantes)}. Retomber sur l'autre afficherait une "
            "phrase fausse sans que rien ne le signale."
        )
    for forme, texte in formes.items():
        if not isinstance(texte, str) or not texte.strip():
            raise TranslationCatalogError(
                f"La forme « {forme} » de la clé « {key} » dans {path} doit "
                "être une chaîne non vide."
            )


def clear_translation_cache() -> None:
    """Vide le cache des catalogues de traduction."""
    _load_catalog_cached.cache_clear()


def load_catalog(
    locale: str,
    translations_dir: str | Path = "translations",
) -> dict[str, CatalogValue]:
    return _load_catalog_cached(locale, str(translations_dir))


def trans(
    key: str,
    locale: str | None = None,
    translations_dir: str | Path = "translations",
    *,
    count: "int | None" = None,
) -> str:
    """Texte traduit de `key`, ou la clé elle même si elle manque.

    `count` choisit la forme d'une entrée pluralisée
    (`I18N-PLURAL-CATALOG-REACHABLE-001`). Il manquait ici, si bien que le
    pluriel n'était joignable qu'en appelant `select_plural` sur une valeur que
    le catalogue refusait de porter : la mécanique existait sans porte.

    Une entrée textuelle ignore `count`, ce qui permet d'écrire l'appel
    pluralisé sans savoir si la clé l'est encore.

    Raises:
        PluralError: la clé est pluralisée et `count` manque. Rendre alors la
            forme « one » afficherait « 3 élève » en silence.
    """
    if locale is None:
        locale = get_default_locale()

    # Catalogue principal — lève TranslationCatalogError si absent.
    catalog = load_catalog(locale, translations_dir)
    value = catalog.get(key)
    if value is not None:
        return _rendre(key, value, count, locale)

    # Fallback : cherche dans la locale de secours si elle diffère.
    fallback = get_fallback_locale()
    if fallback and fallback != locale:
        try:
            fallback_catalog = load_catalog(fallback, translations_dir)
        except TranslationCatalogError:
            pass
        else:
            value = fallback_catalog.get(key)
            if value is not None:
                # La forme se choisit dans la langue **du texte rendu**, non
                # dans celle demandée : un texte anglais servi en repli suit la
                # règle anglaise, où zéro est pluriel.
                return _rendre(key, value, count, fallback)

    # I18N-MISSING-KEYS-DEV-001 : la clé est rendue telle quelle, ce qui reste
    # le bon comportement (une page ne doit pas casser pour une traduction
    # absente). Mais RIEN ne le signalait, et « panier_vide » s'affichait à
    # l'utilisateur sans que personne ne s'en aperçoive avant lui.
    _report_missing_key(key, locale)
    return key


def _rendre(
    key: str, value: CatalogValue, count: "int | None", locale: str
) -> str:
    """Texte à rendre, forme de pluriel choisie s'il y a lieu."""
    if isinstance(value, str):
        return value
    if count is None:
        raise PluralError(
            f"La clé « {key} » est pluralisée : appelez trans(..., count=n). "
            "Rendre une forme au hasard afficherait une phrase fausse."
        )
    return select_plural(value, count, locale)


# ---------------------------------------------------------------------------
# Clés manquantes (I18N-MISSING-KEYS-DEV-001)
# ---------------------------------------------------------------------------

logger = logging.getLogger("forge.i18n")

#: Clés rendues telles quelles faute de traduction, hors production.
#:
#: Un ensemble et non une liste : la même clé manquante sur mille requêtes est
#: un seul défaut, et l'accumuler mille fois ferait grossir la mémoire d'un
#: processus de développement sans rien apprendre de plus.
_missing: "set[tuple[str, str]]" = set()


def _report_missing_key(key: str, locale: str) -> None:
    """Signale une clé absente, hors production seulement.

    En production, le silence est délibéré : journaliser chaque clé manquante
    à chaque requête noierait le journal, et une traduction absente n'est pas
    un incident d'exploitation. C'est un défaut à corriger au développement,
    et c'est là qu'il doit se voir.

    Le signalement ne lève **jamais**. Une page qui casse parce qu'il manque
    une traduction serait un remède pire que le mal, y compris en
    développement, où elle empêcherait de voir le reste de la page.
    """
    from core.app.env import is_prod, read_app_env

    if is_prod(read_app_env()):
        return
    marqueur = (locale, key)
    if marqueur in _missing:
        return
    _missing.add(marqueur)
    logger.warning(
        "Forge i18n : clé absente du catalogue %r, la clé est affichée telle "
        "quelle : %r", locale, key,
    )


def missing_keys() -> "tuple[tuple[str, str], ...]":
    """Clés manquantes rencontrées, en couples `(locale, clé)`, triées.

    Vide en production, où rien n'est collecté. Sert à un écran de diagnostic
    ou à un test qui refuse de livrer avec des traductions manquantes.
    """
    return tuple(sorted(_missing))


def clear_missing_keys() -> None:
    """Vide le registre. Utile aux tests, et entre deux campagnes."""
    _missing.clear()
