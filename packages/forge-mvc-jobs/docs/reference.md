# La file de tâches de fond dans Forge (forge-mvc-jobs)

Ce document explique ce que fait l'opt-in `forge-mvc-jobs`, ce qu'il expose, et comment on s'en sert.

`forge-mvc-jobs` déporte un travail lourd hors de la requête HTTP, via une file adossée à la base et un worker explicite.

Le cœur de Forge ignore tout des tâches de fond : ce paquet fournit la file et le worker, l'application fournit les gestionnaires.

??? note "1. Rôle du module"

    Certaines actions sont trop lentes pour une requête HTTP : envoyer 200 emails, transcoder une vidéo, générer un export.

    L'opt-in enfile ces actions avec `enqueue` (depuis un contrôleur) et les traite dans un **process séparé** avec `drain` ou `run_worker`, qui appellent les gestionnaires enregistrés par l'application.

    Il reste fidèle au modèle WSGI synchrone : **pas de broker, pas de Celery/Redis, pas d'async**.
    La file est une table SQL ; le worker est un simple process Python.

??? note "2. Installation et désinstallation"

    ### Installation

    === "Depuis PyPI (stable)"

        La dernière version publiée :

        ```bash
        pip install --pre forge-mvc-jobs
        ```

    === "Depuis Git (avant-garde)"

        Cœur puis opt-in depuis git, dans le venv du projet (l'opt-in trouve le cœur git déjà en place, sans version publiée sur PyPI) :

        ```bash
        source .venv/bin/activate
        pip install "git+https://github.com/caucrogeGit/Forge.git@main"
        pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-jobs"
        ```

        !!! warning "Erreur « externally-managed-environment » ?"

            Lancées hors d'un venv, ces commandes visent le Python **système** (Debian 12+, Ubuntu 23.04+), protégé par PEP 668.
            La cible correcte est le venv du projet (`source .venv/bin/activate`), jamais le Python système.

    Puis activez l'opt-in :

    ```bash
    forge opt-in:enable jobs
    ```


    `opt-in:enable` inscrit l'opt-in dans `optins/registry.py` (ADR-061) (l'opt-in s'importe et s'utilise directement, sans route).
    `forge opt-in:install jobs` affiche la commande `pip` sans l'exécuter.

    Puis créez la table `jobs`, prérequis dur du module :

    ```bash
    forge jobs:init
    forge migration:apply
    ```

    `jobs:init` copie la migration embarquée dans `mvc/migrations/` ; `migration:apply` l'exécute.
    Sans cette table, `enqueue` et le worker échouent au premier appel.

    ### Désinstallation

    ```bash
    forge opt-in:disable jobs
    pip uninstall forge-mvc-jobs
    ```

    `opt-in:disable` est l'inverse d'`enable` : il dé-inscrit du registre (le code n'était pas câblé), sans toucher au paquet.
    `forge opt-in:remove jobs` affiche la commande `pip uninstall` sans l'exécuter.

??? note "3. Commandes"

    `forge-mvc-jobs` ajoute une commande :

    | Commande | Rôle | Exemple |
    |---|---|---|
    | `jobs:init` | Crée la table `jobs` (DDL fournie). | `forge jobs:init` |

??? note "4. Vue d'ensemble rapide"

    | Élément | Valeur |
    |---|---|
    | Paquet | `forge-mvc-jobs` |
    | Module | `forge_mvc_jobs` |
    | Catégorie | Exploitation et outillage (ADR-055) |
    | Couche | opt-in (brique optionnelle) |
    | Dépend de | `forge-mvc` et un backend BDD installé (ADR-054) |
    | API publique | `enqueue`, `process_one`, `drain`, `run_worker`, `pending_count`, `get_job`, `Job`, `JobHandler` |
    | Table SQL | `jobs` (`TABLE_NAME`, `CREATE_TABLE_SQL`) |
    | Exception liée | `JobError` si la tâche est invalide |
    | Contrainte | runtime synchrone (WSGI), sans broker ni async |
    | Installation | `pip install --pre forge-mvc-jobs` |

??? note "5. Schémas UML"

    Les deux schémas suivants montrent deux vues complémentaires de l'opt-in.

    Le diagramme de classe montre l'API, l'état d'une tâche et la table.

    Le diagramme de séquence montre les deux côtés : l'enfilage dans la requête, le traitement dans le worker.

    ### 5.1 Diagramme de classe

    Le diagramme de classe montre que le module agit sur la table `jobs` au travers d'un exécuteur **injecté**, et que le worker appelle des `JobHandler` fournis par l'application.

    ```mermaid
    classDiagram
        direction LR

        class jobs {
            <<module>>
            +enqueue(task, payload, queue, max_attempts, available_in, db) int
            +process_one(handlers, queue, db) bool
            +drain(handlers, queue, max_jobs, db) int
            +run_worker(handlers, queue, poll_interval, db, stop) None
            +pending_count(queue, db) int
            +get_job(job_id, db) Job
        }

        class Job {
            <<dataclass>>
            +int id
            +str queue
            +str task
            +str status
            +int attempts
            +int max_attempts
            +str last_error
        }

        class jobs_table {
            <<table>>
            +id
            +queue
            +task
            +payload
            +status
            +attempts
        }

        class JobHandler {
            <<type>>
            +call(payload) object
        }

        class DBExecutor {
            +execute(sql, params)
            +fetch_one(sql, params)
        }

        jobs --> DBExecutor : exécuteur injecté
        DBExecutor --> jobs_table : lit / écrit
        jobs --> Job : renvoie
        jobs ..> JobHandler : appelle (au traitement)
    ```

    À retenir :

    - on **enfile** une tâche (nom + payload) ; on ne l'exécute pas tout de suite ;
    - les tâches vivent dans la table `jobs` avec un statut ;
    - le traitement appelle un `JobHandler` que l'application a enregistré ;
    - une tâche échouée est ré-essayée jusqu'à `max_attempts`, sinon marquée `failed`.

    ### 5.2 Diagramme de séquence

    Le diagramme de séquence montre l'enfilage côté requête, puis le traitement côté worker.

    ```mermaid
    sequenceDiagram
        actor Navigateur
        participant Ctrl as Contrôleur (requête)
        participant Jobs as forge_mvc_jobs
        participant Table as jobs
        participant Worker as Process worker

        Navigateur->>Ctrl: action lente demandée
        Ctrl->>Jobs: enqueue("send_emails", payload)
        Jobs->>Table: insère la tâche (status = pending)
        Jobs-->>Ctrl: id de la tâche
        Ctrl-->>Navigateur: réponse immédiate

        loop dans un process séparé
            Worker->>Jobs: process_one(handlers) / drain / run_worker
            Jobs->>Table: réserve une tâche disponible
            Jobs->>Jobs: appelle handler(payload)
            Jobs->>Table: marque done, ou re-file / failed
        end
    ```

    À retenir :

    - la requête répond **immédiatement** après `enqueue` ;
    - le worker tourne dans un **process distinct** (pas dans le serveur web) ;
    - `process_one` traite une tâche, `drain` vide la file, `run_worker` boucle ;
    - un gestionnaire manquant marque la tâche `failed`.

??? note "6. API publique"

    | Élément | Signature | Rôle |
    |---|---|---|
    | `enqueue` | `enqueue(task, payload=None, *, queue="default", max_attempts=1, available_in=0, db=None) -> int` | enfile une tâche, renvoie son id |
    | `process_one` | `process_one(handlers, *, queue="default", db=None) -> bool` | traite une tâche, `False` si file vide |
    | `drain` | `drain(handlers, *, queue="default", max_jobs=None, db=None) -> int` | traite jusqu'à vider la file, renvoie le nombre traité |
    | `run_worker` | `run_worker(handlers, *, queue="default", poll_interval=1.0, db=None, stop=None) -> None` | boucle de traitement (process worker) |
    | `pending_count` | `pending_count(*, queue="default", db=None) -> int` | nombre de tâches en attente |
    | `get_job` | `get_job(job_id, *, db=None) -> Job \| None` | état d'une tâche |
    | `Job` | dataclass | `id`, `queue`, `task`, `status`, `attempts`, `max_attempts`, `last_error` |
    | `JobHandler` | `Callable[[dict], object]` | gestionnaire d'une tâche |
    | `JobError` | exception (`ValueError`) | tâche invalide |
    | `TABLE_NAME` | `"jobs"` | nom de la table |
    | `CREATE_TABLE_SQL` | constante SQL | création de la table |

    `handlers` associe un nom de tâche à un `JobHandler` (`{"send_emails": envoyer_emails}`).

    `db` est l'exécuteur ; omis, il utilise le backend BDD actif.

??? note "7. Contextes d'utilisation"

    | Besoin | Élément |
    |---|---|
    | Enfiler un travail depuis un contrôleur | `enqueue("task", payload)` |
    | Différer l'exécution | paramètre `available_in=...` (secondes) |
    | Autoriser des ré-essais | paramètre `max_attempts=...` |
    | Traiter une tâche | `process_one(handlers)` |
    | Vider la file (cron) | `drain(handlers)` |
    | Worker persistant | `run_worker(handlers)` |
    | Superviser | `pending_count()`, `get_job(id)` |
    | Créer la table | `CREATE_TABLE_SQL` ou `forge jobs:init` |

??? note "8. Exemples d'utilisation"

    ### 8.1 Enfiler depuis un contrôleur

    ```python
    from core.http.request import Request
    from core.http.response import Response
    from forge_mvc_jobs import enqueue


    def send(request: Request) -> Response:
        enqueue("send_emails", {"campaign_id": 7})
        return Response.text("Envoi programmé.")
    ```

    La requête répond tout de suite ; le travail se fera dans le worker.

    ### 8.2 Le worker (process séparé)

    ```python
    from forge_mvc_jobs import run_worker

    def envoyer_emails(payload: dict) -> None:
        ...

    HANDLERS = {"send_emails": envoyer_emails}

    if __name__ == "__main__":
        run_worker(HANDLERS)          # boucle ; ou drain(HANDLERS) en cron
    ```

    !!! tip "Aide-mémoire"
        Deux côtés, une table :

        - côté requête : `enqueue` ;
        - côté worker : `drain` (cron) ou `run_worker` (persistant), avec vos `handlers`.

??? note "9. Ré-essais, files et injection"

    Une tâche échouée est ré-essayée tant que `attempts < max_attempts`, sinon marquée `failed` (avec `last_error`).

    Plusieurs files nommées coexistent via le paramètre `queue` (par exemple `"emails"`, `"exports"`).

    !!! warning "Création de la table"
        Les fonctions supposent la table `jobs` présente.

        Créez-la avec `forge jobs:init` (ou exécutez `CREATE_TABLE_SQL`) avant le premier appel.

    !!! warning "Le worker tourne à part"
        `run_worker` et `drain` s'exécutent dans un **process distinct** du serveur web (service systemd, cron).

        Ne lancez pas le worker dans le process WSGI : le serveur doit rester disponible pour les requêtes.

    !!! note "Sans broker, par choix"
        La file est une table SQL et le worker un process Python : pas de Redis, pas de Celery, pas d'async.

        C'est cohérent avec le runtime synchrone de Forge ; le cœur ne dépend pas de `forge-mvc-jobs`.

## Voir aussi

- [La file (queue.py)](references/queue.md) : détail des fonctions et du SQL.
- [Initialisation (jobs:init)](references/cli.md) : création de la table.
- [Les erreurs (errors.py)](references/errors.md) : détail de `JobError`.
- [Welcome-Jobs](welcome/debutant/jobs-welcome.md) : parcours d'apprentissage.
