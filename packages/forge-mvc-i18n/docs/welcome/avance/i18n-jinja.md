# trans dans un template

Objectif : traduire directement dans une vue Jinja.

**Ce que vous allez apprendre :** quand `forge-mvc-i18n` est installé, `trans`
est disponible comme **global Jinja**. On écrit `{{ trans("welcome.title") }}`
dans un template. Les valeurs traduites sont **auto-échappées** comme tout le
reste : pas d'injection HTML.

Premier palier du **niveau avancé**.

!!! note "Module opt-in — auto-échappement"
    L'auto-échappement HTML de Jinja s'applique aux traductions : une valeur
    contenant `<` est rendue en `&lt;`, jamais interprétée.

## Classes Forge utilisées

| Élément | Rôle dans ce starter | Référence |
|---------|----------------------|-----------|
| Global Jinja `trans` | Traduire dans un template. | Opt-ins |

## La vue

```html
{# mvc/views/i18n_page/index.html #}
{% extends "layouts/app.html" %}
{% block content %}
<h1>{{ trans("welcome.title", locale) }}</h1>
<p>{{ trans("welcome.greeting", locale) }}</p>
<nav><a href="/">{{ trans("nav.home", locale) }}</a></nav>
{% endblock %}
```

## Le contrôleur

```python
# mvc/controllers/i18n_page_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


class I18nPageController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        locale = request.query("lang", default="fr")
        return BaseController.render(
            "i18n_page/index.html",
            context={"locale": locale},
            request=request,
        )
```

### Comprendre ce code

- `trans` est injecté comme global Jinja par le moteur de rendu Forge : pas
  d'import à faire dans le template.
- On passe la `locale` au contexte, puis `{{ trans("clé", locale) }}` rend la
  bonne langue.
- Si une traduction contenait du HTML, l'auto-échappement la neutralise.

## La route

```python
# mvc/routes.py
from mvc.controllers.i18n_page_controller import I18nPageController

with router.group("", public=True) as public:
    public.add("GET", "/i18n-page", I18nPageController.index, name="i18n_page_index")
```

## À retenir

- `trans` est un **global Jinja** quand l'opt-in est installé.
- `{{ trans("clé", locale) }}` traduit dans la vue.
- Les valeurs traduites sont auto-échappées (pas d'injection HTML).

## Après ce starter

Vous éditez un catalogue à chaud : pourquoi la page ne change-t-elle pas ? Le **cache**.

[Vider le cache](i18n-cache.md)
