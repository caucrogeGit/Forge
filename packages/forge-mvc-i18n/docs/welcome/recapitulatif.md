# Aide-mémoire de la progression i18n

Récapitulatif des paliers de la progression *Welcome i18n* et des API du module opt-in `forge-mvc-i18n` introduites à chaque étape.

!!! note "Module opt-in : repli no-op"
    `forge-mvc-i18n` est **publié sur PyPI** : `pip install --pre forge-mvc-i18n`.
    Sans le module, le noyau fournit un `trans()` **no-op** (retourne la clé) : une application sans i18n ne casse pas (ADR-027).

## Niveau débutant : traduire avec un catalogue

| # | Palier | Ce qu'on apprend | API-clé |
|---|--------|------------------|---------|
| 1 | [Welcome i18n](debutant/i18n-welcome.md) | Traduire une clé, repli no-op | `trans` |
| 2 | [Écrire un catalogue](debutant/i18n-catalog.md) | Structurer et charger des catalogues | `load_catalog` |
| 3 | [Traduire une clé](debutant/i18n-trans.md) | Servir FR ou EN à la demande | `trans` |

## Niveau intermédiaire : locale et repli

| # | Palier | Ce qu'on apprend | API-clé |
|---|--------|------------------|---------|
| 1 | [Locale par défaut](intermediaire/i18n-locale.md) | Fixer/lire la langue par défaut | `set_default_locale`, `get_default_locale` |
| 2 | [Locale de secours](intermediaire/i18n-fallback.md) | Repli sur une langue de secours | `set_fallback_locale`, `get_fallback_locale` |
| 3 | [Clé manquante](intermediaire/i18n-missing.md) | Clé introuvable → la clé en clair | `trans` |

## Niveau avancé : templates, cache, robustesse

| # | Palier | Ce qu'on apprend | API-clé |
|---|--------|------------------|---------|
| 1 | [trans dans un template](avance/i18n-jinja.md) | Traduire en Jinja (auto-échappement) | global Jinja `trans` |
| 2 | [Vider le cache](avance/i18n-cache.md) | Recharger après édition | `clear_translation_cache` |
| 3 | [Gérer les erreurs](avance/i18n-errors.md) | Catalogue absent/invalide, locale interdite | `TranslationCatalogError` |
