# forge-mvc-jobs

File de tâches de fond opt-in pour Forge : déporter un travail lourd hors de la
requête HTTP (envoi d'emails en nombre, transcodage, import massif), via une file
adossée à MariaDB et un worker explicite.

Pas de broker, pas de Celery ni de Redis, pas de runtime async : la file est une
simple table `jobs`, le serveur web reste synchrone (WSGI). On enfile une tâche
depuis un contrôleur, un process worker séparé la traite.

## Installation

```bash
pip install --pre forge-mvc-jobs
```

En développement : `pip install -e ./packages/forge-mvc-jobs`.

## Mise en place de la table

```bash
forge jobs:init         # copie la migration dans mvc/migrations/
forge migration:apply   # crée la table jobs
```

## Côté web : enfiler

```python
from forge_mvc_jobs import enqueue

# Dans un contrôleur : la requête répond tout de suite, le travail part en file.
enqueue("email.envoi", {"to": "eleve@exemple.fr", "sujet": "Bienvenue"})
```

## Côté worker : traiter

```python
from forge_mvc_jobs import run_worker

def envoyer_email(payload):
    ...  # le vrai envoi

handlers = {"email.envoi": envoyer_email}

# Dans un script worker lancé séparément (pas dans le serveur web) :
run_worker(handlers)
```

`drain(handlers)` traite la file en une passe (utile en test ou en tâche
planifiée) ; `run_worker(handlers)` boucle. `enqueue` accepte `queue`,
`max_attempts` (reprise sur échec) et `available_in` (délai en secondes).
`get_job(id)` et `pending_count()` donnent de la visibilité.

## Périmètre

- File en base, réservation atomique (candidate choisie, puis réservée sous garde `status='pending'`).
- Worker explicite lancé par l'application, jamais par la requête.
- Reprise après plantage d'un worker : `reclaim_stale()` et `forge jobs:reclaim`
  rendent à la file les tâches `running` dont le bail a expiré.
- Hors périmètre : ordonnancement cron, priorités fines, broker distribué.

Documentation complète : <https://forgemvc.com/docs/forge/>.
