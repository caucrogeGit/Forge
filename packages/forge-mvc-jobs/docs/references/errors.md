# Les erreurs

Ce document décrit l'erreur levée par `forge_mvc_jobs` en cas d'entrée invalide.

Le fichier de code correspondant est `forge_mvc_jobs/errors.py`.

## 1. `JobError`

```python
class JobError(ValueError):
    ...
```

`JobError` signale une entrée invalide à l'enfilement d'une tâche.
Elle hérite de `ValueError`.

## 2. Quand est-elle levée ?

| Cause | Origine |
|---|---|
| Nom de tâche vide ou composé uniquement d'espaces | `enqueue` |
| `max_attempts` inférieur à 1 | `enqueue` |
| Charge utile non sérialisable en JSON | `enqueue` |

Les échecs **pendant l'exécution** d'une tâche ne lèvent pas `JobError` : ils
sont gérés par la file (reprise ou statut `failed`, avec `last_error`).

## 3. Rattraper l'erreur

```python
from forge_mvc_jobs import enqueue, JobError

try:
    enqueue(nom_tache, charge_utile)
except JobError as exc:
    print(f"Tâche refusée : {exc}")
```

## 4. Voir aussi

- [La file de tâches](queue.md) : `enqueue`, `drain`, `run_worker`.
