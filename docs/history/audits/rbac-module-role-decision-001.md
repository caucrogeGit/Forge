# Décision — Rôle du module RBAC opt-in

**Ticket** : RBAC-MODULE-001-DEFINE-OPTIN-RBAC-MODULE-ROLE
**Date** : 2026-05-20
**Statut** : décision arrêtée

---

## 1. Résumé

Le module `forge-mvc-rbac` existe déjà dans `packages/forge-mvc-rbac/` avec une
implémentation substantielle (`has_permission`, `require_permission`,
`require_user_permission`, Jinja helpers, modèles `Role` / `Permission`, SQL).

Ce ticket arrête formellement le rôle du module vis-à-vis du contrat
`mvc/security/rbac.json` : le module doit charger ce contrat au runtime et
résoudre les permissions à partir de lui. Ce chaînon est absent aujourd'hui.

Forge Core reste neutre. `make:crud` core reste inchangé. `entity.schema.json`
n'est pas modifié.

---

## 2. Contexte

### Tickets livrés avant ce ticket

| Ticket | Livraison |
|---|---|
| RBAC-CONTRACT-001 | RBAC séparé de `entity.schema.json`, emplacement `mvc/security/rbac.json` |
| RBAC-CONTRACT-002 | `schemas/rbac.schema.json` créé, ajouté au registre |
| RBAC-CONTRACT-003 | Commande `rbac:validate` ajoutée |
| RBAC-CONTRACT-CLOSE-001 | Bloc contrat RBAC clôturé |

### Décisions en vigueur

- `make:crud` core ne lit pas `mvc/security/rbac.json`.
- `make:crud` core ne génère pas de guards RBAC depuis ce contrat.
- Forge Core reste neutre : un projet sans RBAC fonctionne normalement.
- Le RBAC applicatif passe par le module opt-in `forge-mvc-rbac`.

---

## 3. Méthode d'audit

### Commandes exécutées

```bash
python forge.py schema:list
python forge.py schema:doctor
python forge.py rbac:validate
python forge.py rbac:validate --json
python forge.py entity:validate
python forge.py build:model
pytest tests/test_rbac_validate_command.py -q
pytest tests/test_rbac_schema_contract.py -q
pytest tests/meta/test_rbac_contract_close_001.py -q
grep -RInE 'rbac|RBAC|permission|require_permission|has_permission|403' \
  forge_cli core mvc tests docs schemas README.md
```

### Zones auditées

- `packages/forge-mvc-rbac/forge_mvc_rbac/` — état du module existant
- `forge_cli/rbac_validate.py` — commande `rbac:validate`
- `forge_cli/entities/crud/context.py` — helper `_with_permission` / CRUD
- `forge_cli/entities/make_crud.py` — branchement RBAC interne
- `schemas/rbac.schema.json` — schéma de contrat
- `docs/security/rbac-contract.md` — documentation du contrat
- `docs/adr/014-rbac-contract-location.md` — décision architecturale

---

## 4. État actuel du contrat RBAC

### Ce qui est livré

| Élément | État |
|---|---|
| `schemas/rbac.schema.json` | Présent, valide (6 schémas OK) |
| `mvc/security/rbac.json` | Absent — optionnel, non créé dans ce projet |
| `forge rbac:validate` | Fonctionnel — retourne 0 si absent (RBAC optionnel) |
| `forge rbac:validate --json` | Fonctionnel — JSON structuré |
| ADR-014 | Accepté — RBAC hors `entity.schema.json` |

### Module `forge-mvc-rbac` existant

Le module est dans `packages/forge-mvc-rbac/` (version `1.0.0b5`).
Il expose déjà une API publique substantielle :

| Symbole | Rôle |
|---|---|
| `has_permission(request, code)` | Vérifie une permission depuis la session/requête |
| `require_permission(code)` | Décorateur de contrôle d'accès (session legacy) |
| `require_user_permission(code)` | Décorateur de contrôle d'accès (Auth/User) |
| `PermissionDenied` | Exception levée en cas d'accès refusé (→ 403) |
| `Role`, `Permission` | Modèles de données sans ORM |
| `make_can()`, `get_request_permissions()` | Helpers de résolution |
| `user_has_permission()` | Resolver (requête SQL) |
| `make_auth_jinja_context()` | Helpers Jinja (can, is_authenticated) |
| SQL `roles.sql`, `user_roles.sql` | Schémas SQL des tables de rôles |

**Ce qui est absent** : le chargement de `mvc/security/rbac.json` au runtime.
Aujourd'hui les permissions sont résolues depuis la base de données (tables
`roles`, `user_roles`). Le contrat déclaratif `mvc/security/rbac.json` n'est
pas encore lu par le module au démarrage.

### Branchement CRUD interne

`make:crud` peut lire le champ `rbac` de la définition interne d'une entité
(format d'implémentation, pas le format canonique) et générer des décorateurs
`@require_permission(code)` dans les contrôleurs. Ce mécanisme est indépendant
de `mvc/security/rbac.json` et de ce module.

---

## 5. Problème à résoudre

Le contrat déclaratif `mvc/security/rbac.json` définit les permissions par entité
et les rôles. Mais aucun composant Forge ne le lit au runtime pour :

1. Valider dynamiquement qu'un utilisateur a une permission donnée selon ce contrat.
2. Fournir les codes de permission aux décorateurs sans les coder en dur.
3. Offrir une commande d'audit croisant le contrat déclaratif et l'état réel.

Le module `forge-mvc-rbac` doit combler ce chaînon.

---

## 6. Responsabilités du module RBAC

Le module opt-in `forge-mvc-rbac` doit fournir :

| Responsabilité | Décision |
|---|---|
| Chargement de `mvc/security/rbac.json` | **OUI** — nouveau chaînon à implémenter |
| Validation complémentaire du contrat à l'usage | **OUI** — cohérence codes ↔ rôles |
| Service `has_permission(request, code)` | **OUI** — déjà présent, à maintenir |
| Service `require_permission(code)` | **OUI** — déjà présent, à maintenir |
| Service `require_user_permission(code)` | **OUI** — déjà présent, à maintenir |
| Erreur 403 standardisée (`PermissionDenied`) | **OUI** — déjà présent, à maintenir |
| Helpers Jinja (`can`, `is_authenticated`) | **OUI** — déjà présents, à maintenir |
| Helpers pour routes ou contrôleurs (opt-in) | **OUI** — décorateurs existants |
| Commande d'audit `rbac:audit` | **OUI** — à créer dans RBAC-MODULE-006 |
| Documentation d'intégration | **OUI** — à créer dans RBAC-MODULE-007 |

---

## 7. Hors périmètre du module RBAC

Le module RBAC ne doit pas :

| Interdit | Raison |
|---|---|
| Modifier `make:crud` core | Le CRUD core reste neutre — principe 8 |
| Modifier `entity.schema.json` | Séparation schéma données / sécurité — ADR-014 |
| Imposer RBAC à tous les projets Forge | Module opt-in — principe 8 |
| Générer automatiquement des guards dans le CRUD core | Le core ne connaît pas le module |
| Dépendre d'un stockage SQL de rôles imposé dès le premier ticket | Progressivité |
| Imposer une table SQL `roles` dès le début | La résolution peut être configurable |
| Modifier `rbac:validate` (commande core) | Commande core indépendante du module |
| Modifier les starters | Hors périmètre module |

---

## 8. Options d'intégration étudiées

| Option | Description | Décision |
|---|---|---|
| A | Guards dans contrôleurs générés par `make:crud` core | Rejeté — couple core et module |
| B | Middleware global Forge Core vérifiant les permissions | Rejeté — Forge Core reste neutre |
| C | Helper `require_permission` dans `BaseController` | Rejeté — idem, core reste neutre |
| D | Module opt-in fournissant décorateurs et helpers | **Retenu** — déjà partiellement présent |
| E | Commande dédiée enrichissant les routes / contrôleurs | À étudier plus tard (RBAC-MODULE-006) |

**Option D retenue** : le module est installé séparément (`pip install forge-mvc-rbac`).
Il fournit des décorateurs (`@require_permission`, `@require_user_permission`) et
helpers (`has_permission`, `make_can`, Jinja) que le développeur applique dans ses
contrôleurs. Aucun guard n'est injecté automatiquement par le core ou le générateur.

---

## 9. Décision retenue

| Point | Décision |
|---|---|
| Module RBAC opt-in | `forge-mvc-rbac` — déjà dans `packages/` |
| Chaînon manquant | Lecture de `mvc/security/rbac.json` au runtime |
| `make:crud` core | Reste neutre — aucune modification |
| `entity.schema.json` | Non modifié |
| `rbac:validate` | Validation du contrat (déjà livrée) |
| `has_permission` | Présent, à maintenir et connecter au contrat |
| `require_permission` | Présent, à maintenir |
| `require_user_permission` | Présent, à maintenir |
| Erreurs 403 (`PermissionDenied`) | Présentes, à maintenir |
| Runtime branché maintenant | NON — ce ticket est une décision uniquement |

---

## 10. Tickets futurs proposés

| Ticket | Objectif |
|---|---|
| RBAC-MODULE-002 | Créer le squelette du module RBAC sans effet runtime — packaging, structure, tests |
| RBAC-MODULE-003 | Charger et valider `mvc/security/rbac.json` depuis le module |
| RBAC-MODULE-004 | Service de permissions : `has_permission()`, `require_permission()`, erreurs 403 |
| RBAC-MODULE-005 | Brancher les permissions sur routes / contrôleurs existants en opt-in |
| RBAC-MODULE-006 | Ajouter une commande d'audit RBAC : `forge rbac:audit` |
| RBAC-MODULE-007 | Documenter l'usage RBAC complet |
| RBAC-MODULE-CLOSE-001 | Clôturer le module RBAC opt-in |

`make:crud` n'est pas un point de branchement direct pour le module RBAC.
