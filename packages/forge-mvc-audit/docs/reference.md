# Le journal d'audit dans Forge (forge-mvc-audit)

Ce document explique ce que fait l'opt-in `forge-mvc-audit`, ce qu'il expose, et comment on s'en sert.

`forge-mvc-audit` trace les actions importantes d'une application dans une table `audit_log`, avec une API explicite `record_audit` / `get_audit_log`.

Le cœur de Forge ignore tout de l'audit applicatif : ce paquet fournit la table et les helpers, l'application décide de ce qu'elle trace.

## 1. Rôle du module

Une application a besoin de garder une trace des actions sensibles : élève créé, note modifiée, rôle changé, fichier supprimé.

L'opt-in stocke ces traces dans une table SQL (`audit_log`) et expose deux fonctions : une pour écrire une trace, une pour relire le journal.

Son périmètre est **borné** : c'est un audit applicatif, pas un SIEM de cybersécurité (cohérent avec ADR-008, la décision de tracer reste applicative).

## 2. Installation et désinstallation

### Installation

```bash
pip install --pre forge-mvc-audit
forge opt-in:enable audit
```

`opt-in:enable` inscrit l'opt-in dans `optins/registry.py` (ADR-061) (l'opt-in s'importe et s'utilise directement, sans route).
`forge opt-in:install audit` affiche la commande `pip` sans l'exécuter.

### Désinstallation

```bash
forge opt-in:disable audit
pip uninstall forge-mvc-audit
```

`opt-in:disable` est l'inverse d'`enable` : il dé-inscrit du registre (le code n'était pas câblé), sans toucher au paquet.
`forge opt-in:remove audit` affiche la commande `pip uninstall` sans l'exécuter.

## 3. Vue d'ensemble rapide

| Élément | Valeur |
|---|---|
| Paquet | `forge-mvc-audit` |
| Module | `forge_mvc_audit` |
| Catégorie | Sécurité et accès (ADR-055) |
| Couche | opt-in (brique optionnelle) |
| Dépend de | `forge-mvc` et un backend BDD installé (ADR-054) |
| API publique | `record_audit`, `get_audit_log`, `AuditEntry` |
| Table SQL | `audit_log` (`TABLE_NAME`, `CREATE_TABLE_SQL`) |
| Limite de lecture | `MAX_LIMIT` = 1000 entrées |
| Exception liée | `AuditError` si l'action est vide ou la limite invalide |
| Cadre | ADR-008 (Forge fournit la table et le helper) |
| Installation | `pip install --pre forge-mvc-audit` |

## 4. Schémas UML

Les deux schémas suivants montrent deux vues complémentaires de l'opt-in.

Le diagramme de classe montre l'API, l'entrée renvoyée et la table.

Le diagramme de séquence montre l'écriture puis la relecture d'une trace.

### 4.1 Diagramme de classe

Le diagramme de classe montre que le module écrit dans la table `audit_log` au travers d'un exécuteur **injecté** et renvoie des `AuditEntry` typés.

```mermaid
classDiagram
    direction LR

    class audit {
        <<module>>
        +record_audit(action, actor, target_type, target_id, details, db) int
        +get_audit_log(limit, actor, action, target_type, target_id, db) list
    }

    class AuditEntry {
        <<dataclass>>
        +int id
        +str actor
        +str action
        +str target_type
        +str target_id
        +str details
        +str created_at
    }

    class audit_log {
        <<table>>
        +id
        +actor
        +action
        +target_type
        +target_id
        +details
        +created_at
    }

    class DBExecutor {
        +execute(sql, params)
        +fetch_all(sql, params)
    }

    class AuditError {
        <<exception>>
    }

    audit --> DBExecutor : exécuteur injecté
    DBExecutor --> audit_log : lit / écrit
    audit --> AuditEntry : renvoie 0..*
    audit ..> AuditError : peut lever
```

À retenir :

- le module expose deux fonctions, pas de classe à instancier ;
- les traces vivent dans la table `audit_log` ;
- `get_audit_log` renvoie des `AuditEntry` typés ;
- le module n'ouvre jamais de connexion : il reçoit un exécuteur.

### 4.2 Diagramme de séquence

Le diagramme de séquence montre un `record_audit` suivi d'un `get_audit_log` filtré.

```mermaid
sequenceDiagram
    participant App as Code applicatif
    participant Audit as forge_mvc_audit
    participant DB as Exécuteur BDD
    participant Table as audit_log

    App->>Audit: record_audit("note.update", actor="prof", target_id=42)
    Audit->>Audit: valide l'action
    Audit->>DB: execute(INSERT, params)
    DB->>Table: insère la ligne
    Audit-->>App: id de la trace
    App->>Audit: get_audit_log(action="note.update", limit=20)
    Audit->>DB: fetch_all(SELECT filtré, params)
    DB-->>Audit: lignes
    Audit-->>App: list[AuditEntry] (plus récentes d'abord)
```

À retenir :

- `record_audit` valide l'action puis insère, et renvoie l'identifiant ;
- `get_audit_log` renvoie les entrées les plus récentes d'abord ;
- les filtres (`actor`, `action`, `target_type`, `target_id`) sont optionnels ;
- `limit` est plafonné à `MAX_LIMIT`.

## 5. API publique

| Élément | Signature | Rôle |
|---|---|---|
| `record_audit` | `record_audit(action, *, actor=None, target_type=None, target_id=None, details=None, db=None) -> int` | écrit une trace, renvoie son id |
| `get_audit_log` | `get_audit_log(*, limit=100, actor=None, action=None, target_type=None, target_id=None, db=None) -> list[AuditEntry]` | relit le journal, filtrable |
| `AuditEntry` | dataclass | une entrée : `id`, `actor`, `action`, `target_type`, `target_id`, `details`, `created_at` |
| `AuditError` | exception (`ValueError`) | action vide ou limite invalide |
| `TABLE_NAME` | `"audit_log"` | nom de la table |
| `CREATE_TABLE_SQL` | constante SQL | création de la table |
| `MAX_LIMIT` | `1000` | plafond du paramètre `limit` |

Le paramètre `action` est obligatoire : c'est une chaîne applicative (par exemple `"eleve.create"`, `"note.update"`).

Le paramètre `db` est l'exécuteur de base de données ; omis, il utilise le backend BDD actif.

## 6. Contextes d'utilisation

| Besoin | Élément |
|---|---|
| Tracer une action | `record_audit("action", ...)` |
| Associer un acteur | paramètre `actor=...` |
| Désigner la cible | `target_type=...`, `target_id=...` |
| Ajouter un détail libre | paramètre `details=...` |
| Relire les dernières traces | `get_audit_log(limit=...)` |
| Filtrer le journal | `actor=`, `action=`, `target_type=`, `target_id=` |
| Créer la table | `CREATE_TABLE_SQL` ou `forge audit:init` |

## 7. Exemples d'utilisation

### 7.1 Tracer une action

```python
from forge_mvc_audit import record_audit

record_audit(
    "note.update",
    actor="prof.martin",
    target_type="note",
    target_id=42,
    details="note passée de 12 à 14",
)
```

### 7.2 Relire et filtrer le journal

```python
from forge_mvc_audit import get_audit_log

dernieres = get_audit_log(limit=20)
sur_les_notes = get_audit_log(action="note.update", limit=50)

for entry in sur_les_notes:
    print(entry.created_at, entry.actor, entry.details)
```

`get_audit_log` renvoie des `AuditEntry`, les plus récents d'abord.

!!! tip "Aide-mémoire"
    Deux fonctions, une table :

    - `record_audit` pour écrire une trace ;
    - `get_audit_log` pour relire, avec des filtres optionnels.

## 8. Périmètre, validation et injection

L'action est obligatoire et non vide ; sinon `record_audit` lève `AuditError`.

`limit` est plafonné à `MAX_LIMIT` (1000) pour éviter de charger un journal entier par mégarde.

!!! warning "Création de la table"
    Les fonctions supposent la table `audit_log` présente.

    Créez-la avec `forge audit:init` (ou exécutez `CREATE_TABLE_SQL`) avant le premier appel.

!!! note "Périmètre borné"
    `forge-mvc-audit` est un journal d'audit **applicatif**, pas un SIEM de cybersécurité.

    Il trace ce que l'application décide de tracer (ADR-008) ; il ne surveille pas le système ni le réseau.

!!! note "SQL visible et indépendance du cœur"
    Le module ne crée jamais de connexion : il reçoit un exécuteur (`execute`, `fetch_all`).

    Le cœur de Forge ne dépend pas de `forge-mvc-audit` : la dépendance va de l'opt-in vers le cœur.

## Voir aussi

- [Le journal d'audit (store.py)](references/store.md) : détail des fonctions et du SQL.
- [Initialisation (audit:init)](references/cli.md) : création de la table.
- [Les erreurs (errors.py)](references/errors.md) : détail de `AuditError`.
- [Progression Audit](welcome/installation.md) : apprendre l'opt-in pas à pas.
