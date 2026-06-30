# Déclarer les transitions

Objectif : déclarer les **passages autorisés** entre statuts.

**Ce que vous allez apprendre :** `make_transition(from, to)` crée une transition ;
`validate_transitions` vérifie l'ensemble contre les statuts connus. Ce qui n'est
**pas** déclaré est interdit (fermé par défaut).

Premier palier du **niveau intermédiaire** de la progression workflow.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-workflow` installé (palier « Installation »).

## Ce que ce starter montre

- `make_transition(from, to)` pour chaque passage ;
- `validate_transitions(transitions, statuses)` ;
- la liste des transitions validées.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_workflow.make_transition` | Créer une transition `from → to`. | Workflow |
| `forge_mvc_workflow.validate_transitions` | Valider l'ensemble des transitions. | Workflow |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/workflow-transition` : la liste des passages autorisés.

## Le contrôleur

```python
# mvc/controllers/workflow_transition_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_workflow import make_status, make_transition, validate_transitions

_STATUSES = [
    make_status("draft", "Brouillon", "gray", is_initial=True),
    make_status("review", "En revue", "yellow"),
    make_status("published", "Publié", "green"),
    make_status("archived", "Archivé", "red", is_final=True),
]
_RAW_TRANSITIONS = [
    ("draft", "review"),
    ("review", "published"),
    ("review", "draft"),
    ("published", "archived"),
]


class WorkflowTransitionController(BaseController):
    """Starter pédagogique : déclarer et valider les transitions d'un workflow."""

    @staticmethod
    def index(request: Request) -> Response:
        transitions = validate_transitions(
            [make_transition(f, t) for f, t in _RAW_TRANSITIONS], _STATUSES
        )
        return BaseController.render(
            "workflow_transition/index.html",
            context={"transitions": [(t.from_status, t.to_status) for t in transitions]},
            request=request,
        )
```

### Comprendre ce code

- Le workflow est **fermé par défaut** : seuls les passages déclarés sont possibles.
- `validate_transitions` peut vérifier que chaque transition relie des statuts connus.
- Déclarer explicitement les transitions rend le cycle de vie **auditable**.

## La vue

```html
<!-- mvc/views/workflow_transition/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Déclarer les transitions - Forge</title>
</head>
<body>
  <h1>Déclarer les transitions</h1>

  <p>Transitions autorisées (validées contre les statuts connus) :</p>
  <ul>
    {% for from_status, to_status in transitions %}
    <li><code>{{ from_status }}</code> → <code>{{ to_status }}</code></li>
    {% endfor %}
  </ul>

  <p>Tout passage <strong>non déclaré</strong> ici sera <strong>refusé</strong> : le
  workflow est explicite et fermé par défaut.</p>
</body>
</html>
```

## La route

Dans le groupe public de `mvc/routes.py`, ajoutez l'import et la route :

```python
# mvc/routes.py
from mvc.controllers.workflow_transition_controller import WorkflowTransitionController

with router.group("", public=True) as public:
    public.add("GET", "/workflow-transition", WorkflowTransitionController.index, name="workflow_transition_index")
```

## À retenir

- Une transition autorise un passage `from → to`.
- Tout ce qui n'est pas déclaré est **interdit**.
- Le cycle de vie est explicite et validé.

## Après ce starter

La suite : vérifier si un passage précis est autorisé.

[Vérifier une transition](workflow-check.md)
