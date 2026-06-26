# Le journal d'audit

Ce document décrit l'écriture et la lecture des traces d'audit applicatif.

Le fichier de code correspondant est `forge_mvc_audit/store.py`.

## 1. Le modèle

Une trace est une ligne de la table `audit_log` : un acteur (`actor`), une action
(`action`), une cible (`target_type`, `target_id`), un complément libre
(`details`) et une date (`created_at`).
Le périmètre est borné : c'est un audit applicatif, pas un SIEM de cybersécurité
(cohérent avec ADR-008).

## 2. Écrire (`record_audit`)

```python
def record_audit(action, *, actor=None, target_type=None, target_id=None, details=None, db=None) -> int
```

`record_audit` enregistre une action et renvoie l'identifiant de la ligne créée.
`action` est obligatoire (par exemple `"eleve.cree"` ou `"note.modifiee"`).
Lève `AuditError` si `action` est vide.

```python
from forge_mvc_audit import record_audit

record_audit("eleve.cree", actor="prof.dupont", target_type="eleve", target_id=42)
record_audit("note.modifiee", actor="prof.dupont", target_type="note", target_id=7, details="12 -> 15")
```

## 3. Lire (`get_audit_log`)

```python
def get_audit_log(*, limit=100, actor=None, action=None, target_type=None, target_id=None, db=None) -> list[AuditEntry]
```

`get_audit_log` renvoie les entrées les plus récentes (ordre décroissant par
identifiant), filtrables.
Les filtres fournis sont combinés en `AND` sur des colonnes en liste blanche.
`limit` est borné à `MAX_LIMIT` (1000) ; un `limit` inférieur à 1 lève
`AuditError`.

```python
from forge_mvc_audit import get_audit_log

for entree in get_audit_log(limit=20, actor="prof.dupont"):
    print(entree.created_at, entree.action, entree.target_type, entree.target_id)
```

## 4. L'entrée (`AuditEntry`)

```python
@dataclass(frozen=True)
class AuditEntry:
    id: int
    actor: str | None
    action: str
    target_type: str | None
    target_id: str | None
    details: str | None
    created_at: str
```

## 5. Le paramètre `db`

Les deux fonctions acceptent un paramètre `db` injectable.
Par défaut, l'accès passe par `core.database.db`.
En test, on peut injecter un adapter qui expose `insert` et `fetch_all`, ce qui
rend le store vérifiable sans base réelle.

## 6. Voir aussi

- [L'initialisation](cli.md) : créer la table via `forge audit:init`.
- [Les erreurs](errors.md) : `AuditError`.
