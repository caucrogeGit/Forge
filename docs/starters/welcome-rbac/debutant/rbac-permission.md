# Code de permission

Objectif : comprendre ce qu'est un **code de permission** et comment Forge le
normalise et le valide.

**Ce que vous allez apprendre :** une permission est un code en **notation pointée**
(`entité.action`, ex. `article.create`). `normalize_permission_code` le met en forme ;
`validate_permission` refuse les codes invalides.

Deuxième palier du **niveau débutant** de la progression RBAC.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-rbac` installé (palier « Installation »).

## Ce que ce starter montre

- `normalize_permission_code(code)` → forme canonique ;
- `validate_permission(code)` → validité (ou `RbacValidationError`) ;
- une transformation **pure**.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_rbac.normalize_permission_code` | Normaliser un code de permission. | [RBAC](../../../reference/api.md) |
| `forge_mvc_rbac.validate_permission` | Refuser un code invalide. | [RBAC](../../../reference/api.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/rbac-permission?code=Article.Create` :
`article.create`, valide.

## Le contrôleur

```python
# mvc/controllers/rbac_permission_controller.py
from forge_mvc_rbac import RbacValidationError, normalize_permission_code, validate_permission


def _permission_view(code: str) -> dict:
    normalized = normalize_permission_code(code)
    try:
        validate_permission(normalized)
        return {"input": code, "normalized": normalized, "valid": True, "error": None}
    except RbacValidationError as exc:
        return {"input": code, "normalized": normalized, "valid": False, "error": str(exc)}
```

### Comprendre ce code

- La **notation pointée** `entité.action` rend les permissions lisibles et
  cohérentes à travers l'application.
- Normaliser **avant** de comparer évite les faux négatifs (`Article.Create` vs
  `article.create`).
- `validate_permission` lève `RbacValidationError` sur un code vide ou mal formé.

## À retenir

- Une permission est un **code pointé** normalisé.
- Normaliser puis valider est le réflexe avant toute comparaison.
- Des codes cohérents = un contrat RBAC fiable.

## Après ce starter

La suite : la brique « rôle ».

[Rôle et slug](rbac-role.md)
