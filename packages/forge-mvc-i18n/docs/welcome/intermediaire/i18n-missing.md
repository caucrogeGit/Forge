# Clé manquante

Objectif : comprendre ce que renvoie `trans` quand une clé n'existe nulle part.

**Ce que vous allez apprendre :** si une clé est absente de la locale courante **et** de la locale de secours, `trans` retourne **la clé elle-même**, sans lever d'exception.
La page reste affichable ; la clé non traduite est visible, ce qui aide à repérer les oublis.

!!! note "Module opt-in"
    Ce comportement « clé en dernier recours »
    vaut pour une **clé** manquante.
    Un catalogue principal absent ou invalide est traité différemment (avancé).

## Classes Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `trans(key, locale)` | Retourne la clé si elle est introuvable partout. | Opt-ins |

## Le contrôleur

```python
# mvc/controllers/i18n_missing_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_i18n import set_default_locale, set_fallback_locale, trans


class I18nMissingController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        set_default_locale("fr")
        set_fallback_locale("en")
        # "page.inexistante" n'est ni en fr ni en en
        return Response.json({
            "valeur": trans("page.inexistante"),
        })
```

### Comprendre ce code

- `trans("page.inexistante")` cherche en `fr`, puis en `en` (secours), puis retourne `"page.inexistante"`.
- Aucune exception : une clé oubliée ne casse pas la page, elle s'affiche en clair : signal visible pour le développeur.
- C'est un choix **délibéré** : la robustesse d'affichage prime sur l'échec dur.

## La route

```python
# mvc/routes/__init__.py
from mvc.controllers.i18n_missing_controller import I18nMissingController

with router.group("", public=True) as public:
    public.add("GET", "/i18n-missing", I18nMissingController.index, name="i18n_missing_index")
```

## À retenir

- Clé absente partout → `trans` retourne la **clé**, sans exception.
- La page reste affichable ; l'oubli est visible.
- Robustesse d'affichage assumée par défaut.

## Après ce starter

Faisons le **bilan** du niveau intermédiaire.

[Bilan du niveau intermédiaire](bilan.md)
