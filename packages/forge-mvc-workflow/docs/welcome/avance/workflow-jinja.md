# Helpers Workflow dans Jinja

Objectif : utiliser les helpers de statut **directement dans un template**.

**Ce que vous allez apprendre :** `make_workflow_jinja_helpers()` retourne un dict des helpers (`workflow_status_badge`, `_label`, `_color`, `_badge_class`) prêt à injecter dans le contexte d'une vue.
Contrairement à RBAC, ils ne sont **pas** auto-enregistrés.

Troisième palier du **niveau avancé** de la progression workflow.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-workflow` installé.

## Ce que ce starter montre

- `make_workflow_jinja_helpers()` → dict de helpers ;
- l'injection des helpers dans le contexte de la vue ;
- leur usage direct dans le template.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_workflow.make_workflow_jinja_helpers` | Helpers de statut prêts à injecter dans Jinja. | Workflow |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/workflow-jinja` : badge, libellé, couleur et classes calculés dans le template.

## Le contrôleur

```python
# mvc/controllers/workflow_jinja_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_workflow import make_status, make_workflow_jinja_helpers

_DEMO_STATUS = make_status("review", "En revue", "yellow")


class WorkflowJinjaController(BaseController):
    """Starter pédagogique : injecter les helpers Workflow dans un template."""

    @staticmethod
    def index(request: Request) -> Response:
        context = {"status": _DEMO_STATUS}
        context.update(make_workflow_jinja_helpers())
        return BaseController.render(
            "workflow_jinja/index.html", context=context, request=request
        )
```

## La vue

```html
<!-- mvc/views/workflow_jinja/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Helpers Workflow dans Jinja - Forge</title>
</head>
<body>
  <h1>Helpers Workflow dans Jinja</h1>

  <p>Helpers injectés dans le contexte, utilisés directement dans le template :</p>
  <ul>
    <li>Badge : {{ workflow_status_badge(status) }}</li>
    <li>Libellé : {{ workflow_status_label(status) }}</li>
    <li>Couleur : {{ workflow_status_color(status) }}</li>
    <li>Classes : <code>{{ workflow_status_badge_class(status) }}</code></li>
  </ul>

  <p>Les helpers de <code>forge-mvc-workflow</code> ne sont pas auto-enregistrés : on
  les ajoute au contexte (ou à l'environnement Jinja) explicitement.</p>
</body>
</html>
```

## La route

Dans le groupe public de `mvc/routes/__init__.py`, ajoutez l'import et la route :

```python
# mvc/routes/__init__.py
from mvc.controllers.workflow_jinja_controller import WorkflowJinjaController

with router.group("", public=True) as public:
    public.add("GET", "/workflow-jinja", WorkflowJinjaController.index, name="workflow_jinja_index")
```

### Comprendre ce code

- Les helpers de `forge-mvc-workflow` ne sont **pas** auto-enregistrés (contrairement au `can()` de RBAC) : on les ajoute au contexte de la vue, ou à l'environnement Jinja de l'application une fois pour toutes.
- Une fois injectés, ils s'utilisent comme des fonctions de template.
- Cela laisse l'application **maîtresse** de ce qu'elle expose à ses templates (explicite plutôt que magique).

## À retenir

- `make_workflow_jinja_helpers()` regroupe les helpers d'affichage.
- Injection **explicite** dans le contexte ou l'environnement Jinja.
- Pas de magie : l'application décide ce qu'elle expose.

## Après ce starter

Vous avez parcouru toute la progression workflow : statuts, transitions, affichage.

[Bilan du niveau avancé](bilan.md)
