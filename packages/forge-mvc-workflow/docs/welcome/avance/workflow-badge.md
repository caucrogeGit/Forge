# Badge de statut

Objectif : afficher un statut sous forme de **badge HTML** prêt à l'emploi.

**Ce que vous allez apprendre :** `workflow_status_badge(status)` produit un badge HTML **sûr** (`Markup` : Jinja ne le double-échappe pas), couleur et libellé inclus.

Premier palier du **niveau avancé** de la progression workflow.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-workflow` installé.

## Ce que ce starter montre

- `workflow_status_badge(status)` → un `<span>` HTML sûr ;
- l'affichage direct du badge dans la vue ;
- une transformation **pure**.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_workflow.workflow_status_badge` | Produire un badge HTML sûr pour un statut. | Workflow |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/workflow-badge` : un badge coloré par statut.

## Le contrôleur

```python
# mvc/controllers/workflow_badge_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_workflow import make_status, workflow_status_badge

_STATUSES = [
    make_status("draft", "Brouillon", "gray", is_initial=True),
    make_status("review", "En revue", "yellow"),
    make_status("published", "Publié", "green"),
    make_status("archived", "Archivé", "red", is_final=True),
]


class WorkflowBadgeController(BaseController):
    """Starter pédagogique : afficher un badge HTML de statut."""

    @staticmethod
    def index(request: Request) -> Response:
        badges = [(s.name, workflow_status_badge(s)) for s in _STATUSES]
        return BaseController.render(
            "workflow_badge/index.html", context={"badges": badges}, request=request
        )
```

## La vue

```html
<!-- mvc/views/workflow_badge/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Badge de statut - Forge</title>
</head>
<body>
  <h1>Badge de statut</h1>

  <ul>
    {% for name, badge in badges %}
    <li><code>{{ name }}</code> : {{ badge }}</li>
    {% endfor %}
  </ul>

  <p>Le badge est un <code>Markup</code> HTML sûr : <code>{{ "{{ workflow_status_badge(status) }}" }}</code>
  s'affiche directement, sans échappement ni HTML codé à la main.</p>
</body>
</html>
```

## La route

Dans le groupe public de `mvc/routes.py`, ajoutez l'import et la route :

```python
# mvc/routes.py
from mvc.controllers.workflow_badge_controller import WorkflowBadgeController

with router.group("", public=True) as public:
    public.add("GET", "/workflow-badge", WorkflowBadgeController.index, name="workflow_badge_index")
```

### Comprendre ce code

- Le badge est un `Markup` : Jinja l'affiche **tel quel**, sans rééchapper le HTML ; pas de `| safe` à risque, pas de HTML codé à la main.
- Couleur et libellé du statut sont déjà intégrés dans le badge.
- Centraliser le rendu d'un statut garantit la cohérence visuelle partout.

## À retenir

- `workflow_status_badge` rend un statut en un badge HTML sûr.
- `Markup` évite le double-échappement et le HTML manuel.
- Un seul endroit pour le rendu = cohérence garantie.

## Après ce starter

La suite : accéder aux **pièces** d'un badge pour un rendu sur mesure.

[Couleur, libellé, classe](workflow-color.md)
