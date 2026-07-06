# Le process worker

Objectif : traiter la file en continu depuis un process séparé du serveur web.

**Ce que vous allez apprendre :** `run_worker` est une boucle qui vide la file, puis attend si elle est vide, et recommence.
On la lance depuis un petit script de l'application, un process distinct du serveur web.
La requête HTTP enfile ; le worker traite : ce sont deux processus différents.

Premier palier du **niveau intermédiaire** de la progression Jobs.

!!! note "Module opt-in"
    Si `forge-mvc-jobs` n'est pas installé, l'import échoue.
    Le cœur de Forge, lui, ne dépend jamais de ce paquet.

## Ce que ce starter montre

- écrire un script worker qui appelle `run_worker(handlers)` ;
- comprendre que ce script tourne en dehors de la requête HTTP.

## Fonctions Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `run_worker(handlers)` | Boucle de worker : vide la file, attend si vide, recommence. | Opt-ins |

## 1. Le script worker

```python
# worker.py, à la racine de l'application
from forge_mvc_jobs import run_worker


def envoyer_email(payload):
    print(f"Envoi d'un email à {payload['to']}")


handlers = {
    "email.envoi": envoyer_email,
}

if __name__ == "__main__":
    run_worker(handlers)
```

On le lance dans un terminal dédié :

```bash
python worker.py
```

### Comprendre ce code

- `run_worker(handlers)` traite les tâches disponibles, puis attend (`poll_interval`) quand la file est vide.
- C'est une boucle : elle ne rend pas la main, le process reste en vie pour traiter les tâches à mesure.
- Le serveur web, lui, continue d'enfiler avec `enqueue` : il n'attend jamais le worker.
- Le worker et le serveur web sont deux processus séparés, qui partagent la même table `jobs`.
- Pour arrêter proprement, on peut passer une condition `stop` (un `Callable[[], bool]`).

## Le modèle web et worker

```text
Serveur web   ->  enqueue(task, payload)   ->  table jobs (MariaDB)
Process worker <- run_worker(handlers)      <-  table jobs (MariaDB)
```

Le serveur web reste synchrone (WSGI).
Aucun travail lourd ne s'exécute pendant la requête : il part dans la file.

## À retenir

- `run_worker(handlers)` est la boucle de traitement, lancée par un script de l'application.
- Enfiler se fait côté web ; traiter se fait côté worker, dans un autre process.
- Les deux processus communiquent par la table `jobs`, sans broker.

## Après ce starter

Vous avez un worker qui tourne.
Voyons comment gérer un échec et réessayer une tâche.

[Réessais et inspection](jobs-retry.md)
