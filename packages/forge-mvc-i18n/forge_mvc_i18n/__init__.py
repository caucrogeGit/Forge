# pyright: strict
"""forge-mvc-i18n — Internationalisation opt-in (extraite du core, ADR-027).

Traduction par catalogues JSON (`translations/<locale>.json`), locale par défaut
et locale de fallback configurables via le noyau (`i18n_default_locale`,
`i18n_fallback_locale`), cache des catalogues, et helper `trans()` exposé aux
templates Jinja par le renderer du noyau quand ce paquet est installé.
"""
from forge_mvc_i18n.exceptions import I18nError, TranslationCatalogError
from forge_mvc_i18n.translator import (
    clear_translation_cache,
    get_default_locale,
    get_fallback_locale,
    load_catalog,
    set_default_locale,
    set_fallback_locale,
    trans,
)

__version__ = "1.0.0rc6"

__all__ = [
    "I18nError",
    "TranslationCatalogError",
    "get_default_locale",
    "set_default_locale",
    "get_fallback_locale",
    "set_fallback_locale",
    "load_catalog",
    "trans",
    "clear_translation_cache",
]
