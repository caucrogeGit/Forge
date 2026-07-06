# Couleur, libellé, classe

Objectif : accéder aux **pièces** d'un badge pour un affichage sur mesure.

**Ce que vous allez apprendre :** `workflow_status_label` (texte), `workflow_status_color` (couleur, défaut `gray`) et `workflow_status_badge_class` (classes Tailwind, repli gris si couleur inconnue) exposent séparément les éléments d'un statut.
Ils acceptent un statut **ou** une simple chaîne.

Deuxième palier du **niveau avancé** de la progression workflow.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-workflow` installé (palier « Installation »).

## Ce que ce starter montre

- `workflow_status_label`, `workflow_status_color`, `workflow_status_badge_class` ;
- un tableau pièce par pièce ;
- une transformation **pure**.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_workflow.workflow_status_label` | Libellé d'affichage d'un statut. | Workflow |
| `forge_mvc_workflow.workflow_status_color` | Couleur d'un statut (défaut `gray`). | Workflow |
| `forge_mvc_workflow.workflow_status_badge_class` | Classes Tailwind d'un badge. | Workflow |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/workflow-color` : libellé, couleur et classes par statut.

## Le contrôleur

```python
# mvc/controllers/workflow_color_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_workflow import (
    make_status,
    workflow_status_badge_class,
    workflow_status_color,
    workflow_status_label,
)

_STATUSES = [
    make_status("draft", "Brouillon", "gray", is_initial=True),
    make_status("review", "En revue", "yellow"),
    make_status("published", "Publié", "green"),
    make_status("archived", "Archivé", "red", is_final=True),
]


class WorkflowColorController(BaseController):
    """Starter pédagogique : accéder aux pièces d'un badge de statut."""

    @staticmethod
    def index(request: Request) -> Response:
        rows = [
            {
                "name": s.name,
                "label": workflow_status_label(s),
                "color": workflow_status_color(s),
                "css": workflow_status_badge_class(s),
            }
            for s in _STATUSES
        ]
        return BaseController.render(
            "workflow_color/index.html", context={"rows": rows}, request=request
        )
```

### Comprendre ce code

- Ces helpers servent quand le badge tout fait ne suffit pas (intégration design spécifique).
- Ils sont **tolérants** : une couleur inconnue retombe sur le gris, un `None` est géré.
- Accepter une chaîne **ou** un statut les rend utilisables même sans objet complet.

## La vue

```html
<!-- mvc/views/workflow_color/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Couleur, libellé, classe - Forge</title>
</head>
<body>
  <h1>Couleur, libellé, classe</h1>

  <table>
    <thead><tr><th>Statut</th><th>Libellé</th><th>Couleur</th><th>Classes</th></tr></thead>
    <tbody>
      {% for row in rows %}
      <tr>
        <td><code>{{ row.name }}</code></td>
        <td>{{ row.label }}</td>
        <td>{{ row.color }}</td>
        <td><code>{{ row.css }}</code></td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  <p>Ces pièces servent quand le badge tout fait ne suffit pas (intégration design
  spécifique). Une couleur inconnue retombe sur le gris.</p>
</body>
</html>
```

## La route

Dans le groupe public de `mvc/routes.py`, ajoutez l'import et la route :

```python
# mvc/routes.py
from mvc.controllers.workflow_color_controller import WorkflowColorController

with router.group("", public=True) as public:
    public.add("GET", "/workflow-color", WorkflowColorController.index, name="workflow_color_index")
```

## À retenir

- `label` / `color` / `badge_class` exposent les pièces d'un badge.
- Repli gris pour une couleur inconnue : pas de rendu cassé.
- Helpers tolérants (statut, chaîne ou `None`).

## Après ce starter

La suite : rendre ces helpers disponibles **dans les templates**.

[Helpers Workflow dans Jinja](workflow-jinja.md)
