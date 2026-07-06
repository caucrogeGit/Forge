# Vérifier une transition

Objectif : répondre « peut-on passer de ce statut à cet autre ?
».

**Ce que vous allez apprendre :** `can_transition(transitions, from, to)` dit si le passage est autorisé par les transitions déclarées.
C'est le contrôle à poser **avant** d'appliquer un changement de statut.

Deuxième palier du **niveau intermédiaire** de la progression workflow.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-workflow` installé (palier « Installation »).

## Ce que ce starter montre

- un formulaire (de / vers) ;
- `can_transition` → autorisé / refusé ;
- une vérification **pure**.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_workflow.can_transition` | Vérifier qu'un passage est autorisé. | Workflow |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/workflow-check?from=draft&to=review` (autorisé) puis `from=draft&to=published` (refusé).

## Le contrôleur

```python
# mvc/controllers/workflow_check_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_workflow import can_transition, make_transition

_TRANSITIONS = [
    make_transition("draft", "review"),
    make_transition("review", "published"),
    make_transition("review", "draft"),
    make_transition("published", "archived"),
]


class WorkflowCheckController(BaseController):
    """Starter pédagogique : vérifier qu'une transition est autorisée."""

    @staticmethod
    def index(request: Request) -> Response:
        from_name = request.query("from") or "draft"
        to_name = request.query("to") or "published"
        allowed = can_transition(_TRANSITIONS, from_name, to_name)
        return BaseController.render(
            "workflow_check/index.html",
            context={"from_name": from_name, "to_name": to_name, "allowed": allowed},
            request=request,
        )
```

### Comprendre ce code

- On vérifie **avant** d'agir : si `can_transition` est faux, on refuse le changement.
- Le contrôle est **pur** : transitions + from + to → booléen.
  Aucune base.
- `draft → published` est refusé : il faut passer par `review`, le workflow impose le chemin.

## La vue

```html
<!-- mvc/views/workflow_check/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Vérifier une transition - Forge</title>
</head>
<body>
  <h1>Vérifier une transition</h1>

  <form method="get" action="/workflow-check">
    <label>De <input type="text" name="from" value="{{ from_name }}"></label>
    <label>Vers <input type="text" name="to" value="{{ to_name }}"></label>
    <button type="submit">Vérifier</button>
  </form>

  <p>
    <code>{{ from_name }}</code> → <code>{{ to_name }}</code> :
    <strong>{% if allowed %}autorisé{% else %}refusé{% endif %}</strong>
  </p>

  <p>Essayez <code>draft → review</code> (autorisé) puis <code>draft → published</code>
  (refusé : il faut passer par la revue).</p>
</body>
</html>
```

## La route

Dans le groupe public de `mvc/routes.py`, ajoutez l'import et la route :

```python
# mvc/routes.py
from mvc.controllers.workflow_check_controller import WorkflowCheckController

with router.group("", public=True) as public:
    public.add("GET", "/workflow-check", WorkflowCheckController.index, name="workflow_check_index")
```

## À retenir

- `can_transition` est le garde-fou avant un changement de statut.
- Le workflow impose les chemins valides.
- Contrôle pur, sans base.

## Après ce starter

La suite : lister tout ce qui est possible depuis un statut.

[Transitions disponibles](workflow-available.md)
