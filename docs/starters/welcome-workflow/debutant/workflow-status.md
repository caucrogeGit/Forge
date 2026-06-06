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
| `forge_mvc_workflow.normalize_status_name` | Normaliser un nom de statut. | [Workflow](../../../reference/api.md) |
| `forge_mvc_workflow.validate_status_name` | Refuser un nom invalide. | [Workflow](../../../reference/api.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/workflow-status?name=En Revue` → `en_revue`.

## Le contrôleur

```python
# mvc/controllers/workflow_status_controller.py
from forge_mvc_workflow import WorkflowStatusError, normalize_status_name, validate_status_name


def _status_view(raw: str) -> dict:
    normalized = normalize_status_name(raw)
    try:
        validate_status_name(raw)
        return {"input": raw, "normalized": normalized, "valid": True, "error": None}
    except WorkflowStatusError as exc:
        return {"input": raw, "normalized": normalized, "valid": False, "error": str(exc)}
```

### Comprendre ce code

- Normaliser **avant** de comparer évite les faux négatifs (« En Revue » vs
  `en_revue`).
- Le nom est stable et machine-friendly ; le libellé reste libre pour l'affichage.
- `validate_status_name` lève `WorkflowStatusError` sur un nom vide ou mal formé.

## À retenir

- Un nom de statut est un identifiant `snake_case` normalisé.
- Normaliser puis valider est le réflexe.
- Nom (machine) et libellé (humain) sont distincts.

## Après ce starter

La suite : retrouver un statut par son nom.

[Retrouver un statut](workflow-find.md)
