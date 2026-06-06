# Vérifier une transition

Objectif : répondre « peut-on passer de ce statut à cet autre ? ».

**Ce que vous allez apprendre :** `can_transition(transitions, from, to)` dit si le
passage est autorisé par les transitions déclarées. C'est le contrôle à poser
**avant** d'appliquer un changement de statut.

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
| `forge_mvc_workflow.can_transition` | Vérifier qu'un passage est autorisé. | [Workflow](../../../reference/api.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/workflow-check?from=draft&to=review` (autorisé) puis
`from=draft&to=published` (refusé).

## Le contrôleur

```python
# mvc/controllers/workflow_check_controller.py
from forge_mvc_workflow import can_transition, make_transition

_TRANSITIONS = [make_transition("draft", "review"), make_transition("review", "published"), ...]


class WorkflowCheckController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        from_name = request.param("from") or "draft"
        to_name = request.param("to") or "published"
        allowed = can_transition(_TRANSITIONS, from_name, to_name)
```

### Comprendre ce code

- On vérifie **avant** d'agir : si `can_transition` est faux, on refuse le changement.
- Le contrôle est **pur** : transitions + from + to → booléen. Aucune base.
- `draft → published` est refusé : il faut passer par `review` — le workflow impose
  le chemin.

## À retenir

- `can_transition` est le garde-fou avant un changement de statut.
- Le workflow impose les chemins valides.
- Contrôle pur, sans base.

## Après ce starter

La suite : lister tout ce qui est possible depuis un statut.

[Transitions disponibles](workflow-available.md)
