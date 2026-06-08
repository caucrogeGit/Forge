from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import core.forge as _forge
from forge_mvc_i18n.exceptions import I18nError, TranslationCatalogError


def get_default_locale() -> str:
    return _forge._cfg["i18n_default_locale"]  # type: ignore[return-value]


def set_default_locale(locale: str) -> None:
    if not isinstance(locale, str) or not locale.strip():
        raise I18nError("La locale par défaut doit être une chaîne non vide.")
    _forge._cfg["i18n_default_locale"] = locale


def get_fallback_locale() -> str | None:
    return _forge._cfg["i18n_fallback_locale"]  # type: ignore[return-value]


def set_fallback_locale(locale: str | None) -> None:
    if locale is not None and (not isinstance(locale, str) or not locale.strip()):
        raise I18nError("La locale de fallback doit être une chaîne non vide ou None.")
    _forge._cfg["i18n_fallback_locale"] = locale


@lru_cache(maxsize=None)
def _load_catalog_cached(locale: str, translations_dir: str) -> dict[str, str]:
    path = Path(translations_dir) / f"{locale}.json"
    if not path.is_file():
        raise TranslationCatalogError(f"Catalogue introuvable : {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TranslationCatalogError(f"JSON invalide dans {path} : {exc}") from exc
    if not isinstance(data, dict):
        raise TranslationCatalogError(f"Le catalogue {path} doit être un objet JSON")
    for key, value in data.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise TranslationCatalogError(
                f"Clés et valeurs doivent être des chaînes dans {path}"
            )
    return data


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

    return key
