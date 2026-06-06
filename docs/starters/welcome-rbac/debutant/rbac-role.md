# Rôle et slug

Objectif : comprendre la brique **rôle** — son nom lisible et son slug stable.

**Ce que vous allez apprendre :** un rôle a un **nom** (« Éditeur en chef ») et un
**slug** identifiant (`editeur-en-chef`). `normalize_role_slug` dérive le slug ;
`validate_role` refuse un rôle invalide.

Troisième palier du **niveau débutant** de la progression RBAC.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-rbac` installé (palier « Installation »).

## Ce que ce starter montre

- `normalize_role_slug(name)` → slug stable ;
- `validate_role(name, slug)` → validité ;
- une transformation **pure**.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_rbac.normalize_role_slug` | Dériver un slug depuis un nom de rôle. | [RBAC](../../../reference/api.md) |
| `forge_mvc_rbac.validate_role` | Refuser un rôle invalide. | [RBAC](../../../reference/api.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/rbac-role?name=Éditeur en chef` → slug
`editeur-en-chef`.

## Le contrôleur

```python
# mvc/controllers/rbac_role_controller.py
from forge_mvc_rbac import RbacValidationError, normalize_role_slug, validate_role


def _role_view(name: str) -> dict:
    slug = normalize_role_slug(name)
    try:
        validate_role(name, slug)
        return {"name": name, "slug": slug, "valid": True, "error": None}
    except RbacValidationError as exc:
        return {"name": name, "slug": slug, "valid": False, "error": str(exc)}
```

### Comprendre ce code

- Le **slug** est l'identifiant stable du rôle ; il ne change pas même si le nom
  d'affichage évolue.
- Séparer nom et slug évite de coder en dur des libellés dans les comparaisons.
- `validate_role` garantit un couple nom/slug cohérent.

## À retenir

- Un rôle = un **nom** (affichage) + un **slug** (identité stable).
- Le slug est ce qui apparaît dans le contrat et les associations.
- Nom et slug se valident ensemble.

## Après ce starter

Vous avez les briques (permission, rôle). La suite (intermédiaire) : les confronter.

[Bilan du niveau débutant](bilan.md)
