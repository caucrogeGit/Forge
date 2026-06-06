# Retrouver un statut

Objectif : localiser un statut **par son nom** dans un jeu de statuts.

**Ce que vous allez apprendre :** `find_status(statuses, name)` retourne le statut
correspondant, ou `None` s'il n'existe pas — utile avant d'agir sur un objet dont on
connaît le nom de statut courant.

Troisième palier du **niveau débutant** de la progression workflow.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-workflow` installé (palier « Installation »).

## Ce que ce starter montre

- `find_status(statuses, name)` → statut trouvé ou `None` ;
- la normalisation du nom recherché ;
- une transformation **pure**.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_workflow.find_status` | Retrouver un statut par son nom. | [Workflow](../../../reference/api.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/workflow-find?name=review` (trouvé) puis
`?name=inconnu` (introuvable).

## Le contrôleur

```python
# mvc/controllers/workflow_find_controller.py
from forge_mvc_workflow import find_status, make_status, normalize_status_name

_STATUSES = [make_status("draft", "Brouillon", "gray", is_initial=True), ...]


class WorkflowFindController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        name = normalize_status_name(request.param("name") or "review")
        found = find_status(_STATUSES, name)
        # found.label si trouvé, sinon None
```

### Comprendre ce code

- `find_status` renvoie `None` plutôt que de lever une exception : on teste
  explicitement l'existence.
- On normalise le nom recherché avant la recherche (cohérence avec les noms stockés).
- C'est la brique qui relie un objet (« cet article est en `review` ») à la définition
  de son statut.

## À retenir

- `find_status` localise un statut, ou `None`.
- Normaliser le nom recherché évite les ratés.
- C'est le pont entre un objet et la définition de son statut.

## Après ce starter

Vous avez les briques « statut ». La suite (intermédiaire) : les **transitions**.

[Bilan du niveau débutant](bilan.md)
