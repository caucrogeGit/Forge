# Les erreurs

Ce document décrit l'erreur levée par `forge_mvc_audit` en cas d'entrée invalide.

Le fichier de code correspondant est `forge_mvc_audit/errors.py`.

## 1. `AuditError`

```python
class AuditError(ValueError):
    ...
```

`AuditError` signale une entrée invalide pour une trace d'audit.
Elle hérite de `ValueError` : un appelant peut la rattraper comme une erreur d'entrée ordinaire.

## 2. Quand est-elle levée ?

| Cause | Origine |
|---|---|
| Action vide ou composée uniquement d'espaces | `record_audit` |
| `limit` inférieur à 1 | `get_audit_log` |
| Colonne de filtre hors liste blanche | `get_audit_log` (garde-fou interne) |

## 3. Rattraper l'erreur

```python
from forge_mvc_audit import record_audit, AuditError

try:
    record_audit(action_saisie, actor=login)
except AuditError as exc:
    print(f"Trace refusée : {exc}")
```

## 4. Voir aussi

- [Le journal d'audit](store.md) : `record_audit`, `get_audit_log`.
