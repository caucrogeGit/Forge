# Locale par défaut

Objectif : définir la langue par défaut de l'application.

**Ce que vous allez apprendre :** `set_default_locale("fr")` fixe la locale utilisée quand on appelle `trans(clé)` **sans** préciser de locale.
`get_default_locale()` la relit.

Premier palier du **niveau intermédiaire**.

!!! note "Module opt-in"
    La locale par défaut est une **configuration d'application** : on la fixe au démarrage, pas à chaque requête.

## Classes Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `set_default_locale(locale)` | Fixe la locale par défaut. | Opt-ins |
| `get_default_locale()` | Lit la locale par défaut. | Opt-ins |

## Fixer la locale au démarrage

Dans le point d'entrée de l'application (ou un module de configuration chargé au boot) :

```python
# mvc/config_i18n.py  (importé au démarrage)
from forge_mvc_i18n import set_default_locale

set_default_locale("fr")
```

## Le contrôleur

```python
# mvc/controllers/i18n_locale_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_i18n import get_default_locale, trans


class I18nLocaleController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        # Aucune locale passée : trans utilise la locale par défaut.
        return Response.json({
            "default_locale": get_default_locale(),
            "title": trans("welcome.title"),
        })
```

### Comprendre ce code

- `trans("welcome.title")` **sans** `locale=` utilise `get_default_locale()`.
- La locale par défaut est globale : la fixer une fois suffit.
- On peut toujours forcer une autre langue ponctuellement avec `trans(clé, locale="en")`.

## La route

```python
# mvc/routes.py
from mvc.controllers.i18n_locale_controller import I18nLocaleController

with router.group("", public=True) as public:
    public.add("GET", "/i18n-locale", I18nLocaleController.index, name="i18n_locale_index")
```

## À retenir

- `set_default_locale` fixe la langue par défaut (au démarrage).
- `trans(clé)` sans locale utilise cette valeur.
- `get_default_locale` la relit.

## Après ce starter

Que se passe-t-il si une clé manque dans la langue par défaut ?
Voyons le **repli**.

[Locale de secours](i18n-fallback.md)
