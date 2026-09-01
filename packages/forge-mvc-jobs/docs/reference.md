# La file de tâches de fond dans Forge (forge-mvc-jobs)

Ce document explique ce que fait l'opt-in `forge-mvc-jobs`, ce qu'il expose, et comment on s'en sert.

`forge-mvc-jobs` déporte un travail lourd hors de la requête HTTP, via une file adossée à la base et un worker explicite.

Le cœur de Forge ignore tout des tâches de fond : ce paquet fournit la file et le worker, l'application fournit les gestionnaires.

??? note "1. Rôle du module"

    Certaines actions sont trop lentes pour une requête HTTP : envoyer 200 emails, transcoder une vidéo, générer un export.

    L'opt-in enfile ces actions avec `enqueue` (depuis un contrôleur) et les traite dans un **process séparé** avec `drain` ou `run_worker`, qui appellent les gestionnaires enregistrés par l'application.

    Il reste fidèle au modèle WSGI synchrone : **pas de broker, pas de Celery/Redis, pas d'async**.
    La file est une table SQL ; le worker est un simple process Python.

??? note "2. Installation"

    !!! warning "Prérequis : activez le venv du projet"

        Quelle que soit la source, installez **dans le venv du projet** :

        ```bash
        source .venv/bin/activate
        ```

        Lancé hors d'un venv, `pip` vise le Python **système** (Debian 12+, Ubuntu 23.04+),
        protégé par PEP 668. Il refuse alors d'installer, pour ne pas écraser les paquets
        gérés par `apt`, et affiche `externally-managed-environment`.
        Le venv de projet créé par `forge new` n'a pas ce verrou.

    #### Installer le paquet

    <div class="canal">

    #### A. Depuis PyPI (stable)

    La dernière version publiée :

    ```bash
    pip install --pre forge-mvc-jobs
    ```

    </div>

    <div class="canal">

    #### B. Depuis Git (avant-garde)

    Cœur puis opt-in depuis git, dans le venv du projet (l'opt-in trouve le cœur git déjà en place, sans version publiée sur PyPI) :

    ```bash
    pip install "git+https://github.com/caucrogeGit/Forge.git@main"
    pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-jobs"
    ```

    </div>

??? note "3. Mise en service"

    Installer le paquet ne suffit pas à le rendre opérationnel.
    Voici les gestes propres à `forge-mvc-jobs`, dans l'ordre.

    Ils déclinent la procédure canonique, [Rendre un opt-in opérationnel : les cinq
    points](/docs/forge/install/opt-ins/#rendre-un-opt-in-operationnel-les-cinq-points).

    #### 1. L'épingler

    ```text
    forge-mvc-jobs==<version de forge-mvc>
    ```

    Dans `requirements.txt`, à la même version ou au même commit que `forge-mvc`.
    Sans cette ligne, l'opt-in n'existe que sur votre machine.

    #### 2. L'inscrire

    ```bash
    forge opt-in:enable jobs --apply
    ```

    L'opt-in est inscrit dans `optins/registry.py` (ADR-061), ce qui le rend visible du
    projet.
    `--apply` est **obligatoire** : sans lui, la commande simule et n'écrit rien.

    #### 3. Poser ce dont il a besoin

    ```bash
    forge jobs:init
    forge migration:apply
    ```

    `jobs:init` copie la migration embarquée dans `mvc/migrations/` ;
    `migration:apply` l'exécute et la trace (ADR-071).
    Sans cette étape, le premier appel échoue sur une table absente.

    #### 4. Le brancher là où il agit

    Il s'importe dans le code qui s'en sert. Il n'y a ni route à monter ni middleware
    à poser.

    #### 5. Le prouver

    ```bash
    make check
    forge doctor
    ```

    Puis un premier usage réel.
    Un opt-in installé, inscrit et provisionné qu'aucun code n'appelle n'est pas
    opérationnel : il est seulement présent.


??? note "4. Désinstallation"

    ```bash
    forge opt-in:disable jobs
    pip uninstall forge-mvc-jobs
    ```

    `opt-in:disable` est l'inverse d'`enable` : il dé-inscrit du registre (le code n'était pas câblé), sans toucher au paquet.
    `forge opt-in:remove jobs` affiche la commande `pip uninstall` sans l'exécuter.

??? note "5. Commandes"

    `forge-mvc-jobs` ajoute deux commandes :

    | Commande | Rôle | Exemple |
    |---|---|---|
    | `jobs:init` | Crée la table `jobs` (DDL fournie). | `forge jobs:init` |
    | `jobs:reclaim` | Reprend les tâches orphelines d'un worker planté. | `forge jobs:reclaim --lease 1800` |
    | `jobs:status` | Affiche l'état des files, lecture seule. | `forge jobs:status --queue mails` |

    !!! danger "Un worker qui meurt laisse sa tâche bloquée"
        Le worker réserve une tâche en la passant à `running`, puis rend son verdict.
        S'il est tué entre les deux, personne ne rend ce verdict à sa place, et la tâche reste `running` indéfiniment.
        La file se remplit alors de lignes mortes que rien ne signale.

        `forge jobs:reclaim` remet en file les tâches dont le **bail** de réservation a expiré.
        Celles qui ont épuisé leurs tentatives sont marquées `failed`, avec un message qui les distingue d'une exception du gestionnaire.
        La distinction compte pour le diagnostic, un worker tué n'ayant rendu aucun verdict.

        ```bash
        forge jobs:reclaim                # bail par défaut, 900 secondes
        forge jobs:reclaim --lease 1800   # bail de 30 minutes
        ```

        Forge ne fournit pas d'ordonnanceur, cette commande est le point d'entrée à brancher sur cron ou un minuteur systemd.

    !!! warning "Le bail est une durée fixe"
        Une tâche légitimement plus longue que le bail sera reprise **alors qu'elle tourne encore**, donc exécutée deux fois.

        Deux conséquences pratiques.
        Réglez le bail au-dessus de votre tâche la plus longue.
        Écrivez des gestionnaires **idempotents**, car la reprise ne promet pas l'exécution unique, elle promet qu'aucune tâche ne reste bloquée.

        Le worker ne prolonge pas son bail pendant qu'il travaille, ce qui lèverait cette limite. C'est hors périmètre pour l'instant.

    !!! note "Le réessai attend, désormais"
        Une tâche dont le gestionnaire lève une exception repart en file après un délai croissant, et non plus immédiatement.
        Le délai double à chaque tentative et se plafonne, soit 10, 20, 40, 80, 160, 320, puis 600 secondes.

        Sans lui, une tâche qui échoue vite consommait toutes ses tentatives en une fraction de seconde, ce qui ne laissait aucune chance à une panne passagère de se résorber.

??? note "6. Vue d'ensemble rapide"

    | Élément | Valeur |
    |---|---|
    | Paquet | `forge-mvc-jobs` |
    | Module | `forge_mvc_jobs` |
    | Catégorie | Exploitation et outillage (ADR-055) |
    | Couche | opt-in (brique optionnelle) |
    | Dépend de | `forge-mvc` et un backend BDD installé (ADR-054) |
    | API publique | `enqueue`, `process_one`, `drain`, `run_worker`, `pending_count`, `get_job`, `Job`, `JobHandler`, `PRIORITY_LOW`, `PRIORITY_NORMAL`, `PRIORITY_HIGH`, `status_counts`, `QueueStatus`, `heartbeat` |
    | Table SQL | `jobs` (`TABLE_NAME`) |
    | Exception liée | `JobError` si la tâche est invalide |
    | Contrainte | runtime synchrone (WSGI), sans broker ni async |
    | Installation | `pip install --pre forge-mvc-jobs` |

??? note "7. Schémas UML"

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
            +enqueue(task, payload, queue, max_attempts, available_in, priority, db) int
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

??? note "8. API publique"

    | Élément | Signature | Rôle |
    |---|---|---|
    | `enqueue` | `enqueue(task, payload=None, *, queue="default", max_attempts=1, available_in=0, priority=PRIORITY_NORMAL, db=None) -> int` | enfile une tâche, renvoie son id |
    | `PRIORITY_LOW`, `PRIORITY_NORMAL`, `PRIORITY_HIGH` | `-10`, `0`, `10` | niveaux nommés, le plus grand pris d'abord |
    | `status_counts` | `status_counts(*, queue=None, db=None) -> list[QueueStatus]` | état des files, toutes par défaut |
    | `QueueStatus` | `queue`, `counts`, `ready`, `total` | compteurs d'une file |
    | `process_one` | `process_one(handlers, *, queue="default", db=None) -> bool` | traite une tâche, `False` si file vide |
    | `drain` | `drain(handlers, *, queue="default", max_jobs=None, db=None) -> int` | traite jusqu'à vider la file, renvoie le nombre traité |
    | `run_worker` | `run_worker(handlers, *, queue="default", poll_interval=1.0, db=None, stop=None) -> None` | boucle de traitement (process worker) |
    | `pending_count` | `pending_count(*, queue="default", db=None) -> int` | nombre de tâches en attente |
    | `get_job` | `get_job(job_id, *, db=None) -> Job \| None` | état d'une tâche |
    | `Job` | dataclass | `id`, `queue`, `task`, `status`, `attempts`, `max_attempts`, `last_error` |
    | `JobHandler` | `Callable[[dict], object]` | gestionnaire d'une tâche |
    | `JobError` | exception (`ValueError`) | tâche invalide |
    | `TABLE_NAME` | `"jobs"` | nom de la table |

    `handlers` associe un nom de tâche à un `JobHandler` (`{"send_emails": envoyer_emails}`).

    `db` est l'exécuteur ; omis, il utilise le backend BDD actif.

??? note "9. Contextes d'utilisation"

    | Besoin | Élément |
    |---|---|
    | Enfiler un travail depuis un contrôleur | `enqueue("task", payload)` |
    | Différer l'exécution | paramètre `available_in=...` (secondes) |
    | Autoriser des ré-essais | paramètre `max_attempts=...` |
    | Traiter une tâche | `process_one(handlers)` |
    | Vider la file (cron) | `drain(handlers)` |
    | Worker persistant | `run_worker(handlers)` |
    | Superviser | `pending_count()`, `get_job(id)` |
    | Créer la table | `forge jobs:init` puis `forge migration:apply` |

??? note "10. Exemples d'utilisation"

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

??? note "10 ter. Voir l'état des files"

    Le paquet n'offrait aucun moyen de voir sa file.
    Un exploitant qui se demandait si le travail avançait devait interroger la base à la main, sans que rien ne lui dise quelle requête écrire : une file bloquée ressemblait exactement à une file vide (`JOBS-STATUS-CLI-001`).

    ```bash
    forge jobs:status                 # toutes les files
    forge jobs:status --queue mails   # une seule
    ```

    | Colonne | Ce qu'elle compte |
    |---|---|
    | `PENDING` | tâches en attente, différées comprises |
    | `RUNNING` | tâches réservées par un ouvrier |
    | `FAILED` | tâches ayant épuisé leurs tentatives |
    | `DONE` | tâches terminées |
    | `PRÊTES` | tâches en attente **et** disponibles maintenant |

    !!! warning "« En attente » ne veut pas dire « à faire maintenant »"
        Une tâche `pending` peut être différée, par `available_in` ou par le délai croissant d'un réessai.

        Confondre les deux ferait chercher un ouvrier en panne là où tout se déroule normalement.
        La colonne `PRÊTES` existe pour cette raison, et c'est elle qu'il faut lire pour savoir s'il reste du travail immédiat.

    !!! info "Lecture seule"
        La commande ne relance ni ne reprend aucune tâche, et ne purge rien.

        `forge jobs:reclaim` fait la reprise des orphelines.
        Confondre les deux donnerait à une commande de diagnostic un effet de bord que personne n'attend, et un test vérifie sur la source qu'aucune écriture ne s'y trouve.

    Le même état est lisible depuis le code, pour une page d'administration par exemple.

    ```python
    from forge_mvc_jobs import status_counts

    for etat in status_counts():
        print(etat.queue, etat.counts, etat.ready, etat.total)
    ```

??? note "10 bis. Priorité des tâches"

    La file prenait les tâches par ordre d'insertion, sans exception.
    Une tâche urgente déposée derrière mille envois d'emails attendait mille envois, et rien ne permettait de la faire passer devant (`JOBS-PRIORITY-001`).

    ```python
    from forge_mvc_jobs import PRIORITY_HIGH, PRIORITY_LOW, enqueue

    enqueue("envoyer_alerte", {"id": 42}, priority=PRIORITY_HIGH)
    enqueue("nettoyer_cache", priority=PRIORITY_LOW)
    enqueue("envoyer_facture", {"id": 7})            # normale, par défaut
    ```

    L'ordre de prise est `priority DESC, id`.
    La plus prioritaire d'abord, et l'ancienneté départage à égalité : sans ce second critère, deux tâches de même priorité se prendraient dans un ordre que rien ne garantit.

    !!! info "Un entier, pas une énumération fermée"
        `PRIORITY_LOW`, `PRIORITY_NORMAL` et `PRIORITY_HIGH` valent `-10`, `0` et `10`.

        Le défaut `0` rend « normales » les tâches déjà en file, sans migration de données.
        Une application peut nuancer entre deux niveaux, Forge n'ayant pas à trancher pour elle.

    !!! warning "La priorité ordonne, elle n'interrompt pas"
        Une tâche déjà réservée par un ouvrier va au bout, quelle que soit la priorité de ce qui arrive ensuite.

        Il n'y a pas de préemption : la file n'a aucun moyen d'arrêter un gestionnaire en cours, et prétendre le contraire serait mentir sur ce que le paquet fait.

    !!! info "Un projet existant applique une migration"
        La colonne est ajoutée par sa propre migration, la création ne se rejouant pas.

        ```bash
        forge jobs:init && forge migration:apply
        ```

        L'index `idx_jobs_priority` couvre le filtre `queue, status` du choix de la prochaine tâche.

??? note "11. Ré-essais, files et injection"

    Une tâche échouée est ré-essayée tant que `attempts < max_attempts`, sinon marquée `failed` (avec `last_error`).

    Plusieurs files nommées coexistent via le paramètre `queue` (par exemple `"emails"`, `"exports"`).

    !!! warning "Création de la table"
        Les fonctions supposent la table `jobs` présente.

        Créez-la avec `forge jobs:init` puis `forge migration:apply`, avant le premier appel.

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

## Déclaration de table

Le paquet ne livre plus de fichier SQL figé : il **déclare** sa table dans `tables.py`
(`JOBS`, plus la liste `MIGRATIONS`).
Le DDL est rendu pour le backend installé par `core.database.table_ddl`, puis écrit
dans `mvc/migrations/` par `forge jobs:init` (chantier `OPTIN-DDL-DIALECTAL`).
Le SQL reste donc relisible avant `forge migration:apply`, mais il est correct pour
MariaDB, SQLite, PostgreSQL comme SQL Server.

## Ne pas faire deux fois

### Clé d'idempotence

Un utilisateur qui double-clique, un webhook rejoué, une requête relancée après un délai d'attente : la tâche partait deux fois, et l'email aussi (`JOBS-IDEMPOTENCY-KEY-001`).

```python
enqueue("envoyer_facture", {"id": 12}, idempotency_key=f"facture-{facture.id}")
```

Deux mises en file de la même clé ne donnent qu'une tâche, et la seconde rend l'identifiant de la première.
Une clé vide vaut une absence de clé : la plupart des tâches n'ont pas besoin d'idempotence.

!!! danger "Pourquoi la colonne n'a pas de contrainte `UNIQUE` ordinaire"
    Une contrainte unique sur colonne nullable n'accepte **qu'un seul NULL sur SQL Server**, là où MariaDB, PostgreSQL et SQLite en acceptent autant qu'on veut.

    La deuxième tâche **sans** clé y aurait donc été refusée, c'est-à-dire presque toutes : la file entière serait tombée sur ce backend.
    L'unicité passe par un index dialectal, filtré sur SQL Server, mesuré contre les serveurs et non déduit.

!!! info "La course est fermée par la base"
    Deux appels simultanés ne peuvent pas insérer tous les deux.

    Le perdant relit la ligne gagnante et rend son identifiant, sans lever : c'est le même motif que l'upsert de `forge-mvc-settings`.

### Prolonger le bail d'une tâche longue

Une tâche plus longue que le bail se faisait reprendre par `jobs:reclaim`, donc **exécutée une seconde fois** pendant que la première tournait encore (`JOBS-HEARTBEAT-001`).

Le remède était d'allonger le bail pour tout le monde, au prix d'une reprise tardive des vraies pannes.

```python
def transcoder(payload, *, claim_token):
    for etape in etapes:
        traiter(etape)
        heartbeat(claim_token)   # « je travaille encore »
```

`heartbeat` rend `False` quand le jeton ne désigne aucune tâche en cours.
C'est une information utile : le travail est peut-être en train d'être refait ailleurs.

!!! info "Seul l'ouvrier qui détient la tâche la prolonge"
    La requête est gardée par `claim_token`.

    Sans cette garde, n'importe qui pourrait retenir une tâche qu'il ne traite pas.

## Composer avec les autres opt-ins

La file est le point de passage de tout ce qui ne doit pas faire attendre une requête.

| Besoin | Motif | Où il est décrit |
|---|---|---|
| Envoyer un email | `enqueue(MAIL_JOB_TASK, message_to_payload(...))` | référence de `forge-mvc-mail` |
| Importer un gros fichier | `enqueue(IMPORT_JOB_TASK, import_payload(...))` | référence de `forge-mvc-import-export` |
| Doubler une notification | `on_notification_created` puis `enqueue` | référence de `forge-mvc-notifications` |
| Transcoder une vidéo | commande `video:process`, hors file | référence de `forge-mvc-video` |

!!! info "Aucun de ces paquets ne connaît les autres"
    Chacun fournit une sérialisation et un gestionnaire, ou un point d'accroche ; c'est l'application qui les met en présence.

    Un opt-in qui importerait un autre opt-in créerait une dépendance que Forge refuse, et un test le vérifie sur l'arbre syntaxique de chaque module concerné.

!!! warning "Une tâche qui échoue rejoue, une donnée invalide non"
    Le gestionnaire lève sur ce qu'un réessai peut résoudre : relais injoignable, fichier illisible, importeur inconnu.

    Il ne lève pas sur des lignes de CSV invalides, qu'un réessai ne corrigerait jamais et qui feraient rejouer la tâche jusqu'à épuisement de ses tentatives.
