# forge-mvc-i18n

Opt-in Forge pour l'**internationalisation**. Extrait du core (ADR-027) : le core
ne contient que les primitives générales ; la traduction est une brique
spécialisée, optionnelle.

## Contenu

- `trans(key, locale=None, translations_dir="translations")` : traduit une clé
  via le catalogue de la locale, avec repli sur la locale de fallback puis sur
  la clé elle-même.
- `load_catalog(locale, translations_dir)` : charge et valide un catalogue
  `translations/<locale>.json` (objet JSON de chaînes), mis en cache.
- `clear_translation_cache()` : vide le cache des catalogues.
- `get_default_locale` / `set_default_locale`, `get_fallback_locale` /
  `set_fallback_locale` : pilotent la configuration du noyau
  (`i18n_default_locale`, `i18n_fallback_locale`).
- Exceptions : `I18nError`, `TranslationCatalogError`.

Quand le paquet est installé, le renderer Jinja du noyau expose
automatiquement `trans()` comme fonction globale des templates.

## Installation

```bash
pip install --pre forge-mvc-i18n
```

## Configuration

Les locales par défaut et de fallback sont des clés du noyau, configurables au
démarrage :

```python
import core.forge as forge

forge.configure(i18n_default_locale="fr", i18n_fallback_locale="en")
```

## Exemple

```python
from forge_mvc_i18n import trans

# translations/fr.json -> {"common.save": "Enregistrer"}
trans("common.save")            # "Enregistrer"
trans("inconnu")                # "inconnu" (repli sur la clé)
```
