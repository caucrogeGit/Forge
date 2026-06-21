# Le cœur RBAC dans Forge

Ce document décrit les modèles et les vérifications de permission de base de `forge_mvc_rbac`.

Le fichier de code correspondant est `forge_mvc_rbac/rbac.py`.

## 1. À quoi sert ce module ?

C'est le socle du contrôle d'accès : il modélise une **permission** et un **rôle**, valide leurs codes, et vérifie si la requête courante détient une permission.

## 2. Les modèles

```python
@dataclass
class Permission:
    id: int | None
    code: str
    label: str | None = None
    description: str | None = None

@dataclass
class Role:
    id: int | None
    name: str
    slug: str
    description: str | None = None
```

## 3. Vérifier une permission

```python
from forge_mvc_rbac import has_permission, make_can, require_permission

if has_permission(request, "article.publish"):
    ...

@require_permission("article.publish")
def publish(request):
    ...
```

| Fonction | Comportement |
|---|---|
| `get_request_permissions(request)` | l'ensemble des permissions de la requête courante |
| `has_permission(request, permission_code)` | `True` si la requête détient la permission |
| `make_can(request)` | un callable `can(code) -> bool` lié à la requête |
| `require_permission(permission_code)` | décorateur ; retourne `403` si la permission est absente |

## 4. Valider et normaliser

| Fonction | Comportement |
|---|---|
| `validate_permission(code)` | lève `RbacValidationError` si le code est invalide |
| `validate_role(name, slug)` | lève `RbacValidationError` si le rôle est invalide |
| `normalize_permission_code(code)` | minuscules, séparateurs pointés (`article.publish`) |
| `normalize_role_slug(name)` | dérive un slug valide depuis un nom de rôle |

## 5. Les erreurs

- `PermissionDenied` : levée quand une permission requise est absente.
- `RbacValidationError` : code de permission ou rôle invalide.

## 6. Contextes d'utilisation

- **Garde de route** : `@require_permission("...")`.
- **Affichage conditionnel** : `make_can(request)` exposé à Jinja (voir [jinja](jinja.md)).

## 7. Voir aussi

- [Le contrat RBAC](contract.md) : permissions déclarées dans `rbac.json`.
- [L'autorisation Auth/User](authorization.md) : vérifier pour l'utilisateur connecté.
- [Vue d'ensemble RBAC](../reference.md) : le modèle de sécurité complet.
