# La file de tâches

Ce document décrit l'enfilement et le traitement des tâches de fond.

Le fichier de code correspondant est `forge_mvc_jobs/queue.py`.

## 1. Le modèle

La file est une table `jobs`.
On enfile une tâche depuis le code web, un process worker séparé la traite.
Pas de broker, pas de runtime async : le serveur reste synchrone (WSGI).
La réservation d'une tâche est atomique : le worker choisit une candidate, puis la réserve sous garde `status='pending'`.
Deux workers qui visent la même ligne ne peuvent pas gagner tous les deux, le second voyant zéro ligne affectée.
Plusieurs workers peuvent donc tourner en parallèle.

## 2. Enfiler (`enqueue`)

```python
def enqueue(task, payload=None, *, queue="default", max_attempts=1, available_in=0, db=None) -> int
```

`enqueue` ajoute une tâche `task` avec sa charge utile (sérialisée en JSON) et renvoie son identifiant.
`max_attempts` borne les tentatives, `available_in` retarde la disponibilité de N secondes.
Lève `JobError` si `task` est vide, `max_attempts < 1`, ou si `payload` n'est pas sérialisable en JSON.

```python
from forge_mvc_jobs import enqueue

enqueue("email.envoi", {"to": "eleve@exemple.fr"}, max_attempts=3)
```

## 3. Traiter (`drain`, `run_worker`, `process_one`)

```python
def process_one(handlers, *, queue="default", db=None) -> bool
def drain(handlers, *, queue="default", max_jobs=None, db=None) -> int
def run_worker(handlers, *, queue="default", poll_interval=1.0, db=None, stop=None) -> None
```

`handlers` est un dictionnaire `{nom_de_tache: fonction}` que l'application construit explicitement.
Chaque fonction reçoit la charge utile (un dict).

- `process_one` réserve et exécute une tâche ; renvoie `True` si une tâche a été traitée.
- `drain` traite toutes les tâches disponibles en une passe et renvoie le nombre traité.
- `run_worker` boucle (vide la file, puis attend si vide).
  L'application la lance depuis son propre script worker, jamais depuis la requête HTTP.

```python
from forge_mvc_jobs import run_worker

def envoyer_email(payload):
    ...

run_worker({"email.envoi": envoyer_email})
```

## 4. Reprise sur échec

Si un gestionnaire lève une exception, la tâche est re-mise en file tant que `attempts < max_attempts`, sinon marquée `failed` avec `last_error`.
Une tâche dont le nom n'a aucun gestionnaire enregistré est marquée `failed`.

## 5. Inspecter (`pending_count`, `get_job`)

```python
def pending_count(*, queue="default", db=None) -> int
def get_job(job_id, *, db=None) -> Job | None
```

`Job` expose `id`, `queue`, `task`, `status` (`pending`/`running`/`done`/`failed`), `attempts`, `max_attempts`, `last_error`.

## 6. Limite V1

Une tâche réservée (`running`) dont le worker meurt reste `running` : il n'y a pas de reprise automatique par délai de visibilité dans cette version.

## 7. Voir aussi

- [L'initialisation](cli.md) : créer la table via `forge jobs:init`.
- [Les erreurs](errors.md) : `JobError`.
