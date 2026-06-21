# Les erreurs i18n dans Forge

Ce document décrit les exceptions levées par le module d'internationalisation `forge_mvc_i18n`.

Le fichier de code correspondant est `forge_mvc_i18n/exceptions.py`.

## 1. À quoi servent ces erreurs ?

Le module distingue ses propres erreurs des erreurs Python génériques, pour que l'application puisse les attraper précisément.
Toutes héritent d'une base commune, `I18nError`.

## 2. La hiérarchie

| Exception | Hérite de | Quand elle est levée |
|---|---|---|
| `I18nError` | `Exception` | erreur de base de l'internationalisation Forge |
| `TranslationCatalogError` | `I18nError` | un catalogue est absent, illisible ou invalide |

## 3. `TranslationCatalogError` en détail

C'est l'erreur concrète que vous rencontrerez le plus.
`load_catalog()` la lève quand :

- la locale contient un caractère de chemin interdit ;
- le fichier `<locale>.json` est introuvable ;
- le contenu n'est pas un JSON valide ;
- le JSON n'est pas un objet, ou une clé/valeur n'est pas une chaîne.

Le message précise toujours le fichier et la cause.

## 4. Bien les attraper

```python
from forge_mvc_i18n import trans, I18nError, TranslationCatalogError

try:
    label = trans("welcome.title", locale="fr")
except TranslationCatalogError as err:
    # catalogue fr.json absent ou cassé
    ...
except I18nError as err:
    # toute autre erreur i18n
    ...
```

Attraper `I18nError` couvre l'ensemble du module ; attraper `TranslationCatalogError` cible précisément un problème de catalogue.

## 5. Contextes d'utilisation

- **Chargement de catalogue** : `TranslationCatalogError` signale un fichier manquant ou malformé au démarrage.
- **Réglage de locale** : `I18nError` si une locale vide est fournie à `set_default_locale`.

## 6. Voir aussi

- [La traduction](translator.md) : `trans`, `load_catalog`, les locales et le cache.
