# Écrire un catalogue

Objectif : structurer des catalogues pour deux langues et les charger.

**Ce que vous allez apprendre :** chaque locale a son fichier
`translations/<locale>.json`. `load_catalog(locale)` lit et **valide** le
catalogue (objet JSON de chaînes), puis retourne un dict.

!!! note "Module opt-in"
    Les clés et les valeurs doivent être des **chaînes** : un catalogue mal formé
    lève `TranslationCatalogError` (vu au niveau avancé).

## Classes Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `load_catalog(locale, translations_dir="translations")` | Charge et valide un catalogue. | Opt-ins |

## 1. Le catalogue français

```json
// translations/fr.json
{
  "welcome.title": "Welcome i18n",
  "welcome.greeting": "Bienvenue",
  "nav.home": "Accueil"
}
```

## 2. Le catalogue anglais

```json
// translations/en.json
{
  "welcome.title": "Hello Forge i18n",
  "welcome.greeting": "Welcome",
  "nav.home": "Home"
}
```

## 3. Inspecter un catalogue

```python
# mvc/controllers/i18n_catalog_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_i18n import load_catalog


class I18nCatalogController(BaseController):

    @staticmethod
    def inspect(request: Request) -> Response:
        catalogue = load_catalog("fr")
        return Response.json({
            "locale": "fr",
            "cles": sorted(catalogue.keys()),
            "exemple": catalogue.get("welcome.greeting"),
        })
```

### Comprendre ce code

- `load_catalog("fr")` lit `translations/fr.json` et retourne le dict
  `{clé: texte}`.
- Les deux catalogues partagent **les mêmes clés** : seule la valeur change selon
  la langue. C'est la base de l'i18n.
- La validation est stricte : clés et valeurs doivent être des chaînes.

## La route

```python
# mvc/routes.py
from mvc.controllers.i18n_catalog_controller import I18nCatalogController

with router.group("", public=True) as public:
    public.add("GET", "/i18n-catalog/inspect", I18nCatalogController.inspect, name="i18n_catalog_inspect")
```

## À retenir

- Un fichier par locale : `translations/fr.json`, `translations/en.json`.
- Les catalogues partagent les **mêmes clés**, valeurs différentes.
- `load_catalog` lit et valide (chaînes uniquement).

## Après ce starter

Les catalogues sont prêts. Traduisons selon la **langue demandée**.

[Traduire une clé](i18n-trans.md)
