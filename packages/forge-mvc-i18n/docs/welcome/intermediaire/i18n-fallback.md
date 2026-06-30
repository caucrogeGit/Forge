# Locale de secours

Objectif : retomber sur une autre langue quand une clé manque.

**Ce que vous allez apprendre :** `set_fallback_locale("en")` déclare une langue
de secours. Si une clé est absente du catalogue de la locale courante mais
présente dans le catalogue de secours, `trans` renvoie la valeur de secours.

!!! note "Module opt-in"
    Le repli porte sur les **clés manquantes** d'une locale existante. Si le
    catalogue principal lui-même est absent, c'est une erreur (niveau avancé).

## Classes Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `set_fallback_locale(locale)` | Déclare la locale de secours. | Opt-ins |
| `get_fallback_locale()` | Lit la locale de secours. | Opt-ins |

## 1. Catalogues volontairement déséquilibrés

```json
// translations/fr.json  (il manque "footer.note")
{
  "welcome.title": "Welcome i18n",
  "nav.home": "Accueil"
}
```

```json
// translations/en.json  (présent partout)
{
  "welcome.title": "Hello Forge i18n",
  "nav.home": "Home",
  "footer.note": "All rights reserved"
}
```

## 2. Le contrôleur

```python
# mvc/controllers/i18n_fallback_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_i18n import set_default_locale, set_fallback_locale, trans


class I18nFallbackController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        set_default_locale("fr")
        set_fallback_locale("en")
        return Response.json({
            # présent en fr → valeur française
            "home": trans("nav.home"),
            # absent en fr, présent en en → repli anglais
            "footer": trans("footer.note"),
        })
```

### Comprendre ce code

- `trans("nav.home")` trouve la clé en `fr` → `"Accueil"`.
- `trans("footer.note")` ne la trouve pas en `fr`, bascule sur le catalogue de
  secours `en` → `"All rights reserved"`.
- Le repli **n'écrase pas** la langue principale : il ne sert que de filet pour
  les clés manquantes.

## La route

```python
# mvc/routes.py
from mvc.controllers.i18n_fallback_controller import I18nFallbackController

with router.group("", public=True) as public:
    public.add("GET", "/i18n-fallback", I18nFallbackController.index, name="i18n_fallback_index")
```

## À retenir

- `set_fallback_locale` déclare une langue de secours.
- Une clé manquante dans la locale courante est cherchée dans le secours.
- Le repli ne couvre que les **clés** manquantes, pas un catalogue absent.

## Après ce starter

Et si la clé manque **partout** ? Voyons le comportement par défaut.

[Clé manquante](i18n-missing.md)
