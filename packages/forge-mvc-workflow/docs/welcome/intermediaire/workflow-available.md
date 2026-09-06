# Transitions disponibles

Objectif : lister les statuts **atteignables** depuis un statut courant.

**Ce que vous allez apprendre :** `get_available_transitions(transitions, from)` liste les passages partant du statut courant : idéal pour générer dynamiquement les **boutons d'action** d'une fiche.

Troisième palier du **niveau intermédiaire** de la progression workflow.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-workflow` installé.

## Ce que ce starter montre

- `get_available_transitions(transitions, from)` → cibles possibles ;
- la génération des boutons d'action à partir des cibles ;
- une transformation **pure**.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_workflow.get_available_transitions` | Lister les transitions partant d'un statut. | Workflow |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/workflow-available?from=review` : `published`, `draft`.

## Le contrôleur

```python
# mvc/controllers/workflow_available_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_workflow import get_available_transitions, make_transition

_TRANSITIONS = [
    make_transition("draft", "review"),
    make_transition("review", "published"),
    make_transition("review", "draft"),
    make_transition("published", "archived"),
]


class WorkflowAvailableController(BaseController):
    """Starter pédagogique : lister les transitions possibles depuis un statut."""

    @staticmethod
    def index(request: Request) -> Response:
        from_name = request.query("from") or "review"
        available = get_available_transitions(_TRANSITIONS, from_name)
        return BaseController.render(
            "workflow_available/index.html",
            context={"from_name": from_name, "targets": [t.to_status for t in available]},
            request=request,
        )
```

### Comprendre ce code

- Plutôt que de coder chaque bouton en dur, on **dérive** les actions possibles du statut courant : l'UI suit le workflow automatiquement.
- Un statut final renvoie une liste vide → aucune action, naturellement.
- C'est la version « lecture »
  de `can_transition` : on liste au lieu de tester un cas.

## La vue

```html
<!-- mvc/views/workflow_available/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Transitions disponibles - Forge</title>
</head>
<body>
  <h1>Transitions disponibles</h1>

  <form method="get" action="/workflow-available">
    <label>Depuis le statut <input type="text" name="from" value="{{ from_name }}"></label>
    <button type="submit">Lister</button>
  </form>

  <p>Depuis <code>{{ from_name }}</code>, on peut aller vers :</p>
  {% if targets %}
  <ul>
    {% for target in targets %}<li><button>Passer à {{ target }}</button></li>{% endfor %}
  </ul>
  {% else %}
  <p><em>Aucune transition (statut final ou inconnu).</em></p>
  {% endif %}

  <p>Ces cibles génèrent directement les boutons d'action : l'UI suit le workflow.</p>
</body>
</html>
```

## La route

Dans le groupe public de `mvc/routes/__init__.py`, ajoutez l'import et la route :

```python
# mvc/routes/__init__.py
from mvc.controllers.workflow_available_controller import WorkflowAvailableController

with router.group("", public=True) as public:
    public.add("GET", "/workflow-available", WorkflowAvailableController.index, name="workflow_available_index")
```

## À retenir

- `get_available_transitions` donne les actions possibles d'un statut.
- L'UI (boutons) se génère depuis le workflow, pas en dur.
- Statut final → aucune transition, sans cas particulier à coder.

## Après ce starter

Vous maîtrisez statuts et transitions.
La suite (avancé) : l'**affichage**.

[Suivant : appliquer une transition](workflow-appliquer.md)
