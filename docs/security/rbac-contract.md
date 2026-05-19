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

## Limites

Ce contrat n'est pas encore branché au runtime Forge.

- `make:crud` ne lit pas encore `mvc/security/rbac.json`.
- `build:model` ignore ce fichier.
- Aucun CLI ne génère ni ne valide ce fichier automatiquement.

La prochaine étape est RBAC-CONTRACT-003 : brancher `make:crud` au contrat RBAC séparé.

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
