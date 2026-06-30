# Nom de statut

Objectif : comprendre le **nom de statut** et comment Forge le normalise et le valide.

**Ce que vous allez apprendre :** un nom de statut est un identifiant `snake_case`.
`normalize_status_name` le met en forme (« En Revue » → `en_revue`) ;
`validate_status_name` refuse les noms invalides.

Deuxième palier du **niveau débutant** de la progression workflow.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-workflow` installé (palier « Installation »).

## Ce que ce starter montre

- `normalize_status_name(name)` → forme `snake_case` ;
- `validate_status_name(name)` → validité (ou `WorkflowStatusError`) ;
- une transformation **pure**.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_workflow.normalize_status_name` | Normaliser un nom de statut. | Workflow |
| `forge_mvc_workflow.validate_status_name` | Refuser un nom invalide. | Workflow |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/workflow-status?name=En Revue` → `en_revue`.

## Le contrôleur

```python
# mvc/controllers/workflow_status_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_workflow import WorkflowStatusError, normalize_status_name, validate_status_name

_DEMO_NAME = "En Revue"


def _status_view(raw: str) -> dict:
    normalized = normalize_status_name(raw)
    try:
        validate_status_name(raw)
        return {"input": raw, "normalized": normalized, "valid": True, "error": None}
    except WorkflowStatusError as exc:
        return {"input": raw, "normalized": normalized, "valid": False, "error": str(exc)}


class WorkflowStatusController(BaseController):
    """Starter pédagogique : normaliser et valider un nom de statut."""

    @staticmethod
    def index(request: Request) -> Response:
        raw = request.query("name") or _DEMO_NAME
        return BaseController.render(
            "workflow_status/index.html", context=_status_view(raw), request=request
        )
```

### Comprendre ce code

- Normaliser **avant** de comparer évite les faux négatifs (« En Revue » vs
  `en_revue`).
- Le nom est stable et machine-friendly ; le libellé reste libre pour l'affichage.
- `validate_status_name` lève `WorkflowStatusError` sur un nom vide ou mal formé.

## La vue

```html
<!-- mvc/views/workflow_status/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Nom de statut - Forge</title>
</head>
<body>
  <h1>Nom de statut</h1>

  <form method="get" action="/workflow-status">
    <input type="text" name="name" value="{{ input }}" size="40">
    <button type="submit">Normaliser & valider</button>
  </form>

  <ul>
    <li>Entrée : <code>{{ input }}</code></li>
    <li>Normalisé : <code>{{ normalized }}</code></li>
    <li>Valide : <strong>{% if valid %}oui{% else %}non{% endif %}</strong>{% if error %} - {{ error }}{% endif %}</li>
  </ul>

  <p>Le nom <code>snake_case</code> est l'identifiant stable du statut ; le libellé
  est l'affichage.</p>
</body>
</html>
```

## La route

Dans le groupe public de `mvc/routes.py`, ajoutez l'import et la route :

```python
# mvc/routes.py
from mvc.controllers.workflow_status_controller import WorkflowStatusController

with router.group("", public=True) as public:
    public.add("GET", "/workflow-status", WorkflowStatusController.index, name="workflow_status_index")
```

## À retenir

- Un nom de statut est un identifiant `snake_case` normalisé.
- Normaliser puis valider est le réflexe.
- Nom (machine) et libellé (humain) sont distincts.

## Après ce starter

La suite : retrouver un statut par son nom.

[Retrouver un statut](workflow-find.md)
