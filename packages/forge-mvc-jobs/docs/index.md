# Forge Jobs

`forge-mvc-jobs` est l'opt-in de file de tâches de fond de Forge.

Il permet de déporter un travail lourd hors de la requête HTTP (envoi d'emails en
nombre, transcodage, import massif), via une file adossée à MariaDB et un worker
explicite.

## Le modèle, sans broker ni async

La file est une simple table `jobs` : le SQL reste visible.
On enfile une tâche depuis un contrôleur (`enqueue`), la requête répond tout de
suite.
Un process worker séparé traite la file (`drain` ou `run_worker`), en appelant
les gestionnaires que l'application a enregistrés.

Pas de Celery ni de Redis, pas de boucle async : le serveur web reste synchrone
(WSGI).
La dépendance va de l'opt-in vers le cœur, jamais l'inverse.

## Mise en route

```bash
pip install --pre forge-mvc-jobs
forge jobs:init         # copie la migration dans mvc/migrations/
forge migration:apply   # crée la table jobs
```

## Premier usage

```python
# Côté web (contrôleur) : enfiler.
from forge_mvc_jobs import enqueue
enqueue("email.envoi", {"to": "eleve@exemple.fr"})

# Côté worker (script séparé) : traiter.
from forge_mvc_jobs import run_worker
run_worker({"email.envoi": envoyer_email})
```

## Pour aller plus loin

- [La file de tâches](references/queue.md) : `enqueue`, `drain`, `run_worker`, `get_job`.
- [L'initialisation](references/cli.md) : `forge jobs:init`.
- [Les erreurs](references/errors.md) : `JobError`.
