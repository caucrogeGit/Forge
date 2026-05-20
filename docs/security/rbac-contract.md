# Contrat RBAC Forge

## Rôle

Le contrat RBAC Forge définit les rôles et permissions d'accès dans un projet.
Il est **séparé du schéma d'entité** (`entity.schema.json`) : le schéma d'entité
décrit la structure de données, le contrat RBAC décrit les règles d'autorisation.

Cette séparation est décidée dans [ADR-014](../adr/014-rbac-contract-location.md).

## Emplacement

```
mvc/security/rbac.json
```

## Exemple minimal

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

## Structure

| Clé | Type | Requis | Description |
|---|---|---|---|
| `schema_version` | `"1.0"` | Oui | Version du contrat. Seule valeur acceptée : `"1.0"`. |
| `entities` | objet | Non | Permissions par entité. Clé = nom d'entité (PascalCase). |
| `entities.*.permissions` | objet | Oui si `entities` présent | Action → code de permission. Ex : `"list": "article.list"`. |
| `roles` | objet | Non | Rôles et permissions associées. Clé = nom du rôle. |
| `roles.*` | tableau de chaînes | — | Liste de codes de permission attribués au rôle. |

### Propriétés inconnues

`additionalProperties: false` à la racine : aucune clé non documentée n'est acceptée.

### Validation du schéma

Le schéma JSON Schema est disponible dans `schemas/rbac.schema.json`.
Il peut être référencé dans l'éditeur via la clé `$schema` :

```json
{
  "$schema": "../../../schemas/rbac.schema.json",
  "schema_version": "1.0"
}
```

## Validation

Forge peut valider `mvc/security/rbac.json` depuis la racine du projet :

```bash
python forge.py rbac:validate
python forge.py rbac:validate --json
```

Le fichier est **optionnel** : s'il est absent, la commande se termine avec succès
(code retour 0) et affiche un message informatif. Le RBAC n'est pas requis.

S'il existe, il doit respecter `rbac.schema.json`. En cas d'erreur, la commande
affiche les problèmes et retourne le code 1.

## Chargement depuis le module RBAC opt-in

Le package `forge-mvc-rbac` peut charger et valider `mvc/security/rbac.json`
depuis Python :

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

Ce chargement est **lecture seule** — il ne crée ni ne modifie aucun fichier.
Il ne branche pas automatiquement les routes.
Il ne modifie pas `make:crud`.
Il prépare les futurs services RBAC applicatifs (RBAC-MODULE-004).

---

## Vérification des permissions depuis le contrat

Une fois le contrat chargé, le module `forge-mvc-rbac` peut vérifier si un
ensemble de rôles possède une permission déclarée dans `mvc/security/rbac.json` :

```python
from forge_mvc_rbac import (
    load_rbac_contract,
    has_contract_permission,
    get_contract_permissions,
    require_contract_permission,
)

contract = load_rbac_contract(".")

# Vérification booléenne
if has_contract_permission(contract, ["admin", "editor"], "article.update"):
    ...

# Toutes les permissions d'un rôle
perms = get_contract_permissions(contract, ["reader"])
# → {"article.list", "article.show"}

# Protection directe dans un contrôleur
response = require_contract_permission(contract, user_roles, "article.delete")
if response is not None:
    return response  # Response(403)
```

| Fonction | Retour si accordé | Retour si refusé |
|---|---|---|
| `has_contract_permission` | `True` | `False` |
| `get_contract_permissions` | `set[str]` des permissions | `set()` vide |
| `require_contract_permission` | `None` | `Response(403)` |

Cette vérification ne protège pas automatiquement les routes.
Elle ne modifie pas `make:crud`.
Elle prépare le futur branchement opt-in des contrôleurs ou routes (RBAC-MODULE-005).

---

## Protection opt-in d'une action

Le module `forge-mvc-rbac` peut être utilisé explicitement dans une route ou
un contrôleur pour protéger une action avec une permission contractuelle.

### Avec le helper direct

```python
from forge_mvc_rbac import require_contract_permission_for_request

def delete(request, article_id):
    denied = require_contract_permission_for_request(request, "article.delete")
    if denied:
        return denied  # Response(403)
    # ... traitement
```

### Avec le décorateur

```python
from forge_mvc_rbac import contract_permission_required

@contract_permission_required("article.delete")
def delete(request, article_id):
    # ... uniquement exécuté si la permission est accordée
```

Cette protection :
- ne modifie pas `make:crud` ;
- n'est pas générée automatiquement ;
- dépend des rôles présents dans `request.roles` ou la session ;
- retourne `Response(403)` si la permission est absente ou si le contrat est absent ;
- charge `mvc/security/rbac.json` à chaque appel (utiliser un cache si nécessaire en production).

| Helper | Retour si accordé | Retour si refusé |
|---|---|---|
| `require_contract_permission_for_request(request, permission)` | `None` | `Response(403)` |
| `@contract_permission_required(permission)` | exécute la fonction | `Response(403)` |

---

## Limites

Ce contrat est non branché au runtime Forge (décision RBAC-CONTRACT-004).

- `make:crud` ne lit pas `mvc/security/rbac.json` — il ne génère pas de guards RBAC depuis ce contrat.
- `build:model` ignore ce fichier.
- Aucun guard RBAC n'est généré par Forge Core depuis `mvc/security/rbac.json`.
- Le runtime RBAC reste hors périmètre de Forge Core.
- L'intégration d'un module RBAC opt-in est reportée.

## Relation avec entity.schema.json

`entity.schema.json` n'a **pas** de propriété `rbac`. Les entités canoniques
(`schema_version: "1.0"`) ne peuvent pas contenir de configuration RBAC.

```json
{
  "schema_version": "1.0",
  "name": "Article",
  "table": "articles",
  "fields": [...]
}
```

La configuration RBAC vit exclusivement dans `mvc/security/rbac.json`.

## Clôture du bloc contrat RBAC séparé

**Statut : terminé.**

Le bloc contrat RBAC séparé est clôturé après livraison de :

- RBAC-CONTRACT-001 — décision : RBAC hors `entity.schema.json` ;
- RBAC-CONTRACT-002 — création du schéma RBAC séparé (`rbac.schema.json`) ;
- RBAC-CONTRACT-003 — validation via `forge rbac:validate` ;
- RBAC-CONTRACT-004 — décision de non-branchement de `make:crud` au contrat séparé.

État final :

- le contrat RBAC vit hors du schéma d'entité ;
- le fichier cible est `mvc/security/rbac.json` ;
- le schéma est `rbac.schema.json` ;
- le contrat est validable avec `forge rbac:validate` ;
- `make:crud` ne consomme pas ce contrat ;
- aucun guard RBAC n'est généré par Forge Core depuis `mvc/security/rbac.json` ;
- le runtime RBAC reste hors périmètre de Forge Core ;
- le futur module RBAC opt-in est reporté.
