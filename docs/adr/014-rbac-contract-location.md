# ADR-014 — Emplacement du contrat RBAC Forge

## Statut

Accepté — Forge 3.x (ticket `RBAC-CONTRACT-001-DEFINE-SEPARATE-RBAC-CONTRACT`).

---

## Date

2026-05-19

---

## Contexte

Le ticket ENTITY-SCHEMA-RBAC-001 a conclu que `rbac` ne doit pas être intégré dans
`entity.schema.json`. La raison : le schéma d'entité canonique doit rester centré
sur la structure de données (champs, types, index, options). RBAC relève de la
sécurité applicative, non du modèle de données.

Le format interne de génération (`validation.py`) accepte déjà `rbac` comme
attribut de définition d'entité, permettant à `make:crud` de générer des guards
`@require_permission` dans les contrôleurs et `{% if can() %}` dans les templates.
Cette intégration fonctionne et est testée (56 tests passent), mais via le format
interne uniquement — pas via le format canonique.

La question ouverte après ENTITY-SCHEMA-RBAC-001 : **où doit vivre la configuration
RBAC dans un projet Forge ?**

---

## Problème

1. La configuration RBAC dispersée entité par entité (clé `rbac` dans chaque fichier
   d'entité) couple la définition du modèle de données et les règles d'autorisation.

2. `entity.schema.json` utilise `additionalProperties: false` — il ne peut pas
   accueillir `rbac` sans modification délibérée.

3. Le module `forge-mvc-rbac` est opt-in. Coupler sa configuration au schéma d'entité
   de base obligerait tous les projets Forge à connaître la structure RBAC même sans
   installer le module.

4. Un contrat RBAC doit couvrir des notions absentes du schéma d'entité : rôles,
   politiques multi-entités, héritages de permissions.

---

## Décision

**Le RBAC ne sera pas intégré dans `entity.schema.json`.**

**La configuration RBAC vivra dans un fichier séparé : `mvc/security/rbac.json`.**

Ce fichier est distinct du répertoire `mvc/entities/`. Il appartient à la zone
de sécurité applicative du projet, aux côtés des autres fichiers de configuration
de sécurité.

---

## Format recommandé

Fichier : `mvc/security/rbac.json`

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

Ce format est **documentaire uniquement** dans ce ticket. Il n'est pas encore
validé par un JSON Schema ni lu par le runtime Forge.

---

## Justification du choix `mvc/security/rbac.json`

| Critère | Raison |
|---|---|
| Centralisation | Un seul fichier contient toutes les règles d'accès du projet |
| Découplage | `entity.schema.json` reste strict sur la structure de données |
| Modules opt-in | Un projet sans `forge-mvc-rbac` peut ignorer ce fichier |
| Vision multi-entités | Les rôles peuvent couvrir plusieurs entités dans un seul endroit |
| Cohérence | `mvc/security/` regroupe déjà les préoccupations de sécurité |

---

## Conséquences

- `entity.schema.json` reste inchangé (`additionalProperties: false`, pas de `rbac`).
- Le format interne de génération (`validation.py`) continue d'accepter `rbac` dans
  les définitions d'entités — il reste un détail d'implémentation du pipeline CLI.
- `make:crud` continue de lire `rbac` depuis la définition interne, sans changement.
- Aucun runtime n'est modifié dans ce ticket.
- Le fichier `mvc/security/rbac.json` n'est pas encore créé ni lu — c'est la
  décision d'architecture, pas l'implémentation.

---

## Hors périmètre de cet ADR

- Créer un JSON Schema pour `mvc/security/rbac.json`.
- Lire `mvc/security/rbac.json` dans `make:crud` ou `build:model`.
- Modifier les starters pour inclure `mvc/security/rbac.json`.
- Publier une nouvelle version de `forge-mvc-rbac`.

---

## Tickets futurs

| Ticket | Objectif |
|---|---|
| `RBAC-CONTRACT-002` | Créer `schemas/rbac.schema.json` et valider `mvc/security/rbac.json` |
| `RBAC-CONTRACT-003` | Lire `mvc/security/rbac.json` dans `make:crud` pour générer les guards |
| `RBAC-CONTRACT-004` | Ajouter un starter de sécurité avec `mvc/security/rbac.json` |

---

## Référence

- Audit ENTITY-SCHEMA-RBAC-001 : `docs/history/audits/entity-schema-rbac-decision-001.md`
- Module RBAC : `packages/forge-mvc-rbac/`
- ADR-004 Périmètre core : `docs/adr/004-core-perimeter.md`
- ADR-012 Suppression format legacy : `docs/adr/012-legacy-format-deprecation-policy.md`
