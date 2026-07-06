# Réessais et inspection

Objectif : réessayer une tâche qui échoue et suivre son état.

**Ce que vous allez apprendre :** `max_attempts` fixe le nombre d'essais d'une tâche.
Si le gestionnaire lève une erreur et qu'il reste des essais, la tâche est remise en file ; sinon elle passe en `failed`.
On inspecte l'état d'une tâche avec `get_job` et le nombre de tâches en attente avec `pending_count`.

Deuxième palier du **niveau intermédiaire** de la progression Jobs.

## Ce que ce starter montre

- enfiler une tâche avec plusieurs essais via `max_attempts` ;
- inspecter l'état d'une tâche avec `get_job` et la file avec `pending_count`.

## Fonctions Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `enqueue(task, payload, max_attempts=...)` | Enfile une tâche avec un nombre d'essais. | Opt-ins |
| `get_job(job_id)` | Renvoie l'état d'une tâche (`Job`) ou `None`. | Opt-ins |
| `pending_count()` | Nombre de tâches en attente. | Opt-ins |

## 1. Enfiler avec des réessais

```python
from forge_mvc_jobs import enqueue, get_job, pending_count

job_id = enqueue("rapport.genere", {"client": 42}, max_attempts=3)

print("en attente :", pending_count())
```

### Comprendre ce code

- `max_attempts=3` autorise jusqu'à trois essais pour cette tâche.
- Si le gestionnaire lève une erreur et qu'il reste des essais, la tâche est remise en file.
- Une fois les essais épuisés, la tâche passe en statut `failed`.
- Une tâche sans gestionnaire associé est directement marquée `failed`.
- `pending_count()` indique combien de tâches attendent encore d'être traitées.

## 2. Suivre l'état d'une tâche

```python
job = get_job(job_id)
if job is not None:
    print(job.status, job.attempts, "/", job.max_attempts)
    if job.status == "failed":
        print("dernière erreur :", job.last_error)
```

### Comprendre ce code

- `get_job(job_id)` renvoie un objet `Job` figé, ou `None` si l'identifiant est inconnu.
- `job.status` vaut `pending`, `running`, `done` ou `failed`.
- `job.attempts` compte les essais déjà consommés ; `job.max_attempts` est la limite.
- `job.last_error` contient le message du dernier échec, utile pour diagnostiquer.

## À retenir

- `max_attempts` fixe le nombre d'essais ; l'échec remet en file tant qu'il en reste.
- `get_job(id)` donne l'état complet d'une tâche (`status`, `attempts`, `last_error`).
- `pending_count()` mesure la charge restante de la file.

## Après ce starter

Vous savez gérer les échecs et suivre les tâches.
Faisons le point sur le niveau intermédiaire.

[Bilan intermédiaire](bilan.md)
