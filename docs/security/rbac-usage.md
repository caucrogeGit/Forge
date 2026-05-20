# RBAC opt-in — Guide d'usage applicatif

Le RBAC Forge est **opt-in** : le package `forge-mvc-rbac` doit être installé
et ses helpers appliqués explicitement par le développeur. Aucune route n'est
protégée automatiquement par Forge Core.

Cette page décrit le workflow complet, de la déclaration du contrat à la
protection d'une action dans un contrôleur.

## Prérequis

Le package `forge-mvc-rbac` doit être installé dans l'environnement Python :

```bash
pip install forge-mvc-rbac
```

## Étape 1 — Déclarer le contrat RBAC

Créez `mvc/security/rbac.json` à la racine de votre projet. Ce fichier est
**optionnel** : s'il est absent, Forge fonctionne sans RBAC contractuel.

Exemple complet :

```json
{
  "schema_version": "1.0",
  "entities": {
    "Article": {
      "permissions": {
        "list":   "article.list",
        "show":   "article.show",
        "create": "article.create",
        "update": "article.update",
        "delete": "article.delete"
      }
    }
  },
  "roles": {
    "admin": [
      "article.list",
      "article.show",
      "article.create",
      "article.update",
      "article.delete"
    ],
    "editor": [
      "article.list",
      "article.show",
      "article.create",
      "article.update"
    ],
    "reader": [
      "article.list",
      "article.show"
    ]
  }
}
```

Ajoutez la clé `$schema` pour l'autocomplétion dans VS Code :

```json
{
  "$schema": "../../../schemas/rbac.schema.json",
  "schema_version": "1.0"
}
```

## Étape 2 — Valider la structure

`rbac:validate` vérifie que `mvc/security/rbac.json` respecte le schéma JSON
Forge. C'est une vérification **structurelle** (forme du fichier).

```bash
python forge.py rbac:validate
python forge.py rbac:validate --json
```

| Code retour | Signification |
|---|---|
| 0 | Fichier absent (RBAC optionnel) ou fichier valide |
| 1 | Fichier présent mais invalide |

## Étape 3 — Auditer la cohérence

`rbac:audit` vérifie la cohérence **fonctionnelle** du contrat : rôles sans
permissions, entités sans actions CRUD, permissions inutilisées, etc.

```bash
python forge.py rbac:audit
python forge.py rbac:audit --json
```

Codes d'avertissement :

| Code | Description |
|---|---|
| `missing_roles` | Aucun rôle déclaré |
| `missing_entities` | Aucune entité déclarée |
| `empty_role` | Rôle sans permissions |
| `entity_without_permissions` | Entité sans permissions déclarées |
| `missing_crud_action` | Entité sans les cinq actions CRUD (list, show, create, update, delete) |
| `role_permission_not_declared` | Permission d'un rôle absente de toute entité |
| `entity_permission_unused` | Permission déclarée dans une entité mais assignée à aucun rôle |

Les avertissements sont **informatifs** : ils n'entraînent pas un code de retour 1.
`rbac:audit` est **lecture seule** — il ne modifie aucun fichier.

Différence `rbac:validate` / `rbac:audit` :

| Commande | Ce qu'elle vérifie |
|---|---|
| `rbac:validate` | Structure JSON (conformité au schéma) |
| `rbac:audit` | Cohérence fonctionnelle (rôles, entités, permissions) |

## Étape 4 — Charger le contrat depuis Python

```python
from forge_mvc_rbac import load_rbac_contract

result = load_rbac_contract(".")  # ou Path("/chemin/vers/projet")

if result.exists and result.valid:
    print(f"Rôles : {result.roles_count}")
    print(f"Entités : {result.entities_count}")
elif result.exists and not result.valid:
    for err in result.errors:
        print(f"{err.path} : {err.message}")
else:
    print("Pas de contrat RBAC — RBAC est opt-in.")
```

Le chargement est **lecture seule** — aucun fichier n'est créé ni modifié.
Il ne branche pas automatiquement les routes.

## Étape 5 — Vérifier une permission

```python
from forge_mvc_rbac import load_rbac_contract, has_contract_permission, get_contract_permissions

contract = load_rbac_contract(".")

# Vérification booléenne
allowed = has_contract_permission(contract, ["admin"], "article.delete")

# Toutes les permissions effectives d'un ou plusieurs rôles
perms = get_contract_permissions(contract, ["reader"])
# → {"article.list", "article.show"}
```

| Fonction | Retour si accordé | Retour si refusé / contrat absent |
|---|---|---|
| `has_contract_permission` | `True` | `False` |
| `get_contract_permissions` | `set[str]` des permissions | `set()` vide |

## Étape 6 — Protéger une action (helper direct)

```python
from forge_mvc_rbac import require_contract_permission_for_request

def delete(request, article_id):
    denied = require_contract_permission_for_request(
        request,
        "article.delete",
        project_root=".",
    )
    if denied:
        return denied  # Response(403)

    # suppression réelle ici
```

Le helper :

- charge `mvc/security/rbac.json` à chaque appel ;
- extrait les rôles depuis `request.roles` ou la session ;
- retourne `None` si la permission est accordée, `Response(403)` sinon.

## Étape 7 — Protéger une fonction (décorateur)

```python
from forge_mvc_rbac import contract_permission_required

@contract_permission_required("article.delete", project_root=".")
def delete(request, article_id):
    # uniquement exécuté si la permission est accordée
    # suppression réelle ici
```

Le décorateur est équivalent au helper direct — il applique
`require_contract_permission_for_request` avant d'appeler la fonction.

| Helper | Retour si accordé | Retour si refusé |
|---|---|---|
| `require_contract_permission_for_request(request, permission)` | `None` | `Response(403)` |
| `@contract_permission_required(permission)` | exécute la fonction | `Response(403)` |

## Résolution des rôles

Les helpers `require_contract_permission_for_request` et
`contract_permission_required` extraient les rôles dans cet ordre :

1. `request.roles` — liste injectée directement (tests, middleware applicatif)
2. Session utilisateur — champ `"roles"` dans la session Forge

Si aucun rôle n'est trouvé (attribut absent, session vide ou invalide),
l'accès est refusé avec `Response(403)`.

## Imports publics disponibles

```python
from forge_mvc_rbac import (
    load_rbac_contract,                       # charge mvc/security/rbac.json
    get_contract_permissions,                  # set[str] des permissions pour des rôles
    has_contract_permission,                   # bool — la permission est-elle accordée ?
    require_contract_permission,               # None ou Response(403), contrat déjà chargé
    get_request_roles,                         # extrait les rôles depuis la requête
    require_contract_permission_for_request,   # helper direct (charge + extrait + vérifie)
    contract_permission_required,              # décorateur opt-in
)
```

## Limites actuelles

- Le RBAC est **opt-in** : le développeur doit appliquer les helpers explicitement.
- `make:crud` ne génère pas de guards RBAC — les contrôleurs générés sont neutres.
- Les routes ne sont **pas protégées automatiquement** par Forge Core.
- `rbac:audit` ne corrige rien automatiquement — il signale des avertissements informatifs.
- Le contrat est **rechargé à chaque appel** dans l'état actuel. Si les
  performances sont critiques, charger le contrat une fois et réutiliser le
  résultat avec `require_contract_permission`.
- `entity.schema.json` ne contient pas de propriété RBAC — la configuration RBAC
  vit exclusivement dans `mvc/security/rbac.json`.
