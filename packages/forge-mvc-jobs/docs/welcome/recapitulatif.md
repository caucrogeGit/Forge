# Aide-mémoire Jobs

Synthèse de l'API de `forge-mvc-jobs`, à garder sous la main.

## Mise en place de la table

| Étape | Commande |
|-------|----------|
| Déposer la migration de la table `jobs` | `forge jobs:init` |
| Appliquer la migration sur la base | `forge migration:apply` |

## Enfiler (côté web)

| Appel | Résultat |
|-------|----------|
| `enqueue(task, payload)` | Enfile une tâche ; renvoie son identifiant (`int`). |
| `enqueue(task, payload, max_attempts=3)` | Enfile avec un nombre d'essais. |
| `enqueue(task, payload, available_in=60)` | Diffère la disponibilité (en secondes). |
| `enqueue(task, payload, queue="emails")` | Choisit une file nommée. |

`task` vide, `max_attempts < 1` ou `payload` non sérialisable en JSON lèvent `JobError`.

## Traiter (côté worker)

| Appel | Résultat |
|-------|----------|
| `process_one(handlers)` | Traite une tâche ; `True` si traitée, `False` si file vide. |
| `drain(handlers)` | Traite toutes les tâches disponibles (passe unique) ; renvoie le nombre traité. |
| `run_worker(handlers)` | Boucle de worker : vide la file, attend si vide, recommence. |

`handlers` est un dict `{"nom.de.tache": fonction}`, chaque fonction recevant la charge utile (dict).

## Inspecter

| Appel | Résultat |
|-------|----------|
| `pending_count()` | Nombre de tâches en attente. |
| `get_job(job_id)` | État d'une tâche (`Job`) ou `None`. |

`Job` (figé) expose `id`, `queue`, `task`, `status`, `attempts`, `max_attempts`, `last_error`.
`status` vaut `pending`, `running`, `done` ou `failed`.

## Constantes

| Nom | Valeur ou rôle |
|-----|----------------|
| `TABLE_NAME` | `"jobs"` |
| `JobError` | Levée sur tâche invalide (texte vide, essais négatifs, charge non-JSON). |

## Le modèle web et worker

```text
Serveur web    ->  enqueue(task, payload)  ->  table jobs (MariaDB)
Process worker <-  run_worker(handlers)     <-  table jobs (MariaDB)
```

## Rappel

Forge Core ne dépend pas du paquet.
Il n'y a ni broker, ni async : une table MariaDB et un worker explicite.
Le paramètre `db=` rend la file injectable pour les tests.
