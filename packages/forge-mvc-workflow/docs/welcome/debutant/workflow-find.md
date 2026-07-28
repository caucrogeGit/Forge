# Retrouver un statut

Objectif : localiser un statut **par son nom** dans un jeu de statuts.

**Ce que vous allez apprendre :** `find_status(statuses, name)` retourne le statut correspondant, ou `None` s'il n'existe pas : utile avant d'agir sur un objet dont on connaît le nom de statut courant.

Troisième palier du **niveau débutant** de la progression workflow.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-workflow` installé.

## Ce que ce starter montre

- `find_status(statuses, name)` → statut trouvé ou `None` ;
- la normalisation du nom recherché ;
- une transformation **pure**.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_workflow.find_status` | Retrouver un statut par son nom. | Workflow |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/workflow-find?name=review` (trouvé) puis `?name=inconnu` (introuvable).

## Le contrôleur

```python
# mvc/controllers/workflow_find_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_workflow import find_status, make_status, normalize_status_name

_STATUSES = [
    make_status("draft", "Brouillon", "gray", is_initial=True),
    make_status("review", "En revue", "yellow"),
    make_status("published", "Publié", "green"),
    make_status("archived", "Archivé", "red", is_final=True),
]


class WorkflowFindController(BaseController):
    """Starter pédagogique : retrouver un statut par son nom."""

    @staticmethod
    def index(request: Request) -> Response:
        name = normalize_status_name(request.query("name") or "review")
        found = find_status(_STATUSES, name)
        return BaseController.render(
            "workflow_find/index.html",
            context={
                "name": name,
                "found": found is not None,
                "label": found.label if found else None,
                "color": found.color if found else None,
            },
            request=request,
        )
```

### Comprendre ce code

- `find_status` renvoie `None` plutôt que de lever une exception : on teste explicitement l'existence.
- On normalise le nom recherché avant la recherche (cohérence avec les noms stockés).
- C'est la brique qui relie un objet (« cet article est en `review` »)
  à la définition de son statut.

## La vue

```html
<!-- mvc/views/workflow_find/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Retrouver un statut - Forge</title>
</head>
<body>
  <h1>Retrouver un statut</h1>

  <form method="get" action="/workflow-find">
    <input type="text" name="name" value="{{ name }}" size="30">
    <button type="submit">Retrouver</button>
  </form>

  {% if found %}
  <p data-level="success">Trouvé : <code>{{ name }}</code> - « {{ label }} » (couleur {{ color }}).</p>
  {% else %}
  <p data-level="error">Statut <code>{{ name }}</code> introuvable dans le jeu de démo.</p>
  {% endif %}

  <p>Jeu de démo : <code>draft</code>, <code>review</code>, <code>published</code>,
  <code>archived</code>.</p>
</body>
</html>
```

## La route

Dans le groupe public de `mvc/routes/__init__.py`, ajoutez l'import et la route :

```python
# mvc/routes/__init__.py
from mvc.controllers.workflow_find_controller import WorkflowFindController

with router.group("", public=True) as public:
    public.add("GET", "/workflow-find", WorkflowFindController.index, name="workflow_find_index")
```

## À retenir

- `find_status` localise un statut, ou `None`.
- Normaliser le nom recherché évite les ratés.
- C'est le pont entre un objet et la définition de son statut.

## Après ce starter

Vous avez les briques « statut ».
La suite (intermédiaire) : les **transitions**.

[Bilan du niveau débutant](bilan.md)
