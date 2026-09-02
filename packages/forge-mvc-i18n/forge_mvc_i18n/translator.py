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
def _load_catalog_cached(locale: str, translations_dir: str) -> dict[str, str]:
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
    for key, value in data.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise TranslationCatalogError(
                f"Clés et valeurs doivent être des chaînes dans {path}"
            )
    return cast("dict[str, str]", data)


def clear_translation_cache() -> None:
    """Vide le cache des catalogues de traduction."""
    _load_catalog_cached.cache_clear()


def load_catalog(
    locale: str,
    translations_dir: str | Path = "translations",
) -> dict[str, str]:
    return _load_catalog_cached(locale, str(translations_dir))


def trans(
    key: str,
    locale: str | None = None,
    translations_dir: str | Path = "translations",
) -> str:
    if locale is None:
        locale = get_default_locale()

    # Catalogue principal — lève TranslationCatalogError si absent.
    catalog = load_catalog(locale, translations_dir)
    value = catalog.get(key)
    if value is not None:
        return value

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
                return value

    # I18N-MISSING-KEYS-DEV-001 : la clé est rendue telle quelle, ce qui reste
    # le bon comportement (une page ne doit pas casser pour une traduction
    # absente). Mais RIEN ne le signalait, et « panier_vide » s'affichait à
    # l'utilisateur sans que personne ne s'en aperçoive avant lui.
    _report_missing_key(key, locale)
    return key


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
