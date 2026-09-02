# pyright: strict
"""forge-mvc-i18n — Internationalisation opt-in (extraite du core, ADR-027).

Traduction par catalogues JSON (`translations/<locale>.json`), locale par défaut
et locale de fallback configurables via le noyau (`i18n_default_locale`,
`i18n_fallback_locale`), cache des catalogues, et helper `trans()` exposé aux
templates Jinja par le renderer du noyau quand ce paquet est installé.

Depuis `I18N-LOCALE-DETECTION-001`, le paquet sait aussi **d'où vient** la
locale : session, puis `Accept-Language`, puis défaut. La détection reste
explicite, `trans()` ne changeant pas de comportement de lui même.
"""
from forge_mvc_i18n.detection import (
    SESSION_KEY_LOCALE,
    available_locales,
    detect_locale,
    negotiate_locale,
    parse_accept_language,
)
from forge_mvc_i18n.exceptions import I18nError, TranslationCatalogError
from forge_mvc_i18n.extract import (
    ExtractionResult,
    extract_from_directory,
    extract_from_text,
)
from forge_mvc_i18n.plurals import (
    PLURAL_FORMS,
    UNSUPPORTED_LANGUAGES,
    PluralError,
    language_of,
    plural_form,
    select_plural,
)
from forge_mvc_i18n.translator import (
    clear_translation_cache,
    get_default_locale,
    get_fallback_locale,
    load_catalog,
    set_default_locale,
    set_fallback_locale,
    clear_missing_keys,
    missing_keys,
    trans,
)

__version__ = "1.0.0rc7"

__all__ = [
    "I18nError",
    "TranslationCatalogError",
    "get_default_locale",
    "set_default_locale",
    "get_fallback_locale",
    "set_fallback_locale",
    "load_catalog",
    "trans",
    # Clés manquantes signalées hors production (I18N-MISSING-KEYS-DEV-001)
    "missing_keys",
    "clear_missing_keys",
    # Règle de pluriel minimale (I18N-PLURALS-001)
    "plural_form",
    "select_plural",
    "language_of",
    "PLURAL_FORMS",
    "UNSUPPORTED_LANGUAGES",
    "PluralError",
    # Extraction des clés employées (I18N-EXTRACT-CLI-001)
    "extract_from_directory",
    "extract_from_text",
    "ExtractionResult",
    "clear_translation_cache",
    # Détection de la locale active (I18N-LOCALE-DETECTION-001)
    "detect_locale",
    "available_locales",
    "parse_accept_language",
    "negotiate_locale",
    "SESSION_KEY_LOCALE",
]
