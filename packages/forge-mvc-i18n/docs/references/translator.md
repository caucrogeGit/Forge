# La traduction dans Forge

Ce document explique comment `forge_mvc_i18n` traduit des clés en textes localisés, à partir de catalogues JSON.

Le fichier de code correspondant est `forge_mvc_i18n/translator.py`.

## 1. À quoi sert ce module ?

L'internationalisation consiste à afficher chaque texte dans la langue de l'utilisateur.
Forge i18n repose sur des **catalogues JSON** : un fichier `<locale>.json` par langue, où chaque clé est associée à sa traduction.

Le module fournit le helper `trans()` pour récupérer une traduction, plus les réglages de locale et la gestion du cache.

## 2. La traduction dans Forge

```python
from forge_mvc_i18n import trans, set_default_locale

set_default_locale("fr")
trans("welcome.title")        # cherche dans translations/fr.json
```

Un catalogue `translations/fr.json` ressemble à :

```json
{ "welcome.title": "Bienvenue", "welcome.cta": "Commencer" }
```

## 3. Régler les locales

| Fonction | Rôle |
|---|---|
| `get_default_locale()` | la locale active (lue dans la configuration du noyau) |
| `set_default_locale(locale)` | fixe la locale par défaut (chaîne non vide) |
| `get_fallback_locale()` | la locale de secours, ou `None` |
| `set_fallback_locale(locale)` | fixe la locale de secours (chaîne non vide, ou `None`) |

La locale par défaut sert quand `trans()` est appelé sans préciser de langue ; la locale de secours sert quand une clé manque (voir §5).

## 4. Traduire une clé (`trans`)

```python
def trans(
    key: str,
    locale: str | None = None,
    translations_dir: str | Path = "translations",
) -> str
```

`trans()` cherche `key` dans le catalogue de la `locale` (ou de la locale par défaut).
`translations_dir` indique le dossier des catalogues (`translations/` par défaut).

## 5. La règle de résolution

`trans()` suit un ordre strict, sans jamais lever d'erreur pour une clé absente :

1. la valeur de `key` dans le catalogue de la locale demandée ;
2. sinon, sa valeur dans le catalogue de la **locale de secours** (si elle diffère et existe) ;
3. sinon, **la clé elle-même** est renvoyée telle quelle.

Une clé non traduite reste donc visible (`welcome.title`) plutôt que de casser la page : un signal clair pour le développeur.

## 6. Charger un catalogue (`load_catalog`)

`load_catalog(locale, translations_dir="translations")` charge et **valide** le catalogue d'une locale, retournant un `dict[str, str]`.
Il garantit que le fichier existe, que c'est un objet JSON, et que toutes les clés et valeurs sont des chaînes.

La locale est validée comme un identifiant simple (`fr`, `en-US`, `pt_BR`) : tout caractère de chemin (`/`, `\`, `.`) est interdit, ce qui ferme le *path traversal*.

## 7. Le cache (`clear_translation_cache`)

Les catalogues sont **mis en cache** au premier chargement, pour ne pas relire le disque à chaque traduction.
`clear_translation_cache()` vide ce cache, utile en test ou après avoir modifié un fichier de catalogue à chaud.

## 8. Contextes d'utilisation

- **Gabarit** : exposer `trans` au contexte Jinja pour traduire dans les vues.
- **Démarrage** : `set_default_locale` / `set_fallback_locale` au câblage de l'application.
- **Tests** : `clear_translation_cache()` entre deux jeux de catalogues.

## 9. Voir aussi

- [Les erreurs i18n](exceptions.md) : `I18nError`, `TranslationCatalogError`.
- [Progression pédagogique i18n](../welcome/debutant/i18n-welcome.md) : apprendre le module pas à pas.
