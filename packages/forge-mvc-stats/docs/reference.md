# Les statistiques dans Forge (forge-mvc-stats)

Ce document explique ce que fait l'opt-in `forge-mvc-stats`, ce qu'il expose, et comment on s'en sert.

!!! note "Module extrait"
    Les statistiques ont été extraites du cœur vers le paquet `forge-mvc-stats` ; le cœur Forge n'en dépend pas.

`forge-mvc-stats` enregistre des événements applicatifs dans une table (`forge_stats_events`), puis permet de les lister et de les agréger par comptage.

Forge ne trace **rien** automatiquement : le développeur appelle `track_event()` quand il le décide, et injecte lui-même l'exécuteur SQL.
Aucun cookie visiteur, aucune IP.

??? note "1. Rôle du module"

    Compter des actions (connexions, exports, corrections de QCM) demande un socle d'événements explicite.

    L'opt-in définit un `StatsEvent` (nom, libellé, catégorie, métadonnées), le stocke via un exécuteur **injecté**, et fournit deux lectures : lister les événements, ou les compter par dimension.

    L'agrégation se fait par **comptage** (ADR-037) : `count_stats_events` renvoie des totaux groupés, pas des séries temporelles complexes.

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

    === "Depuis PyPI (stable)"

        La dernière version publiée :

        ```bash
        pip install --pre forge-mvc-stats
        ```

    === "Depuis Git (avant-garde)"

        Cœur puis opt-in depuis git, dans le venv du projet (l'opt-in trouve le cœur git déjà en place, sans version publiée sur PyPI) :

        ```bash
        source .venv/bin/activate
        pip install "git+https://github.com/caucrogeGit/Forge.git@main"
        pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-stats"
        ```

    Puis activez l'opt-in :

    ```bash
    forge opt-in:enable stats --apply
    ```


    `opt-in:enable` inscrit l'opt-in dans `optins/registry.py` (ADR-061) (l'opt-in s'importe et s'utilise directement, sans route).
    `forge opt-in:install stats` affiche la commande `pip` sans l'exécuter.

    Puis créez la table `forge_stats_events`, prérequis dur du module.

    Cet opt-in n'expose aucune commande CLI : appliquez une fois, comme migration applicative, le `CREATE TABLE` fourni par `get_stats_events_schema_sql()` :

    ```python
    import core.database.db as db
    from forge_mvc_stats import get_stats_events_schema_sql

    db.execute(get_stats_events_schema_sql())
    ```

    Sans cette table, `track_event` échoue au premier appel.

    Ces gestes ne suffisent pas à rendre l'opt-in **opérationnel** : il reste à l'épingler dans
    `requirements.txt`, à provisionner sa base s'il en a une, à le brancher là où il agit et à le
    prouver par un premier usage réel.
    Voir la procédure canonique, [Rendre un opt-in opérationnel : les cinq points](/docs/forge/install/opt-ins/#rendre-un-opt-in-operationnel-les-cinq-points).

??? note "3. Mise en service"

    Installer le paquet ne suffit pas à le rendre opérationnel.
    Voici les gestes propres à `forge-mvc-stats`, dans l'ordre.

    Ils déclinent la procédure canonique, [Rendre un opt-in opérationnel : les cinq
    points](/docs/forge/install/opt-ins/#rendre-un-opt-in-operationnel-les-cinq-points).

    #### 1. L'épingler

    ```text
    forge-mvc-stats==<version de forge-mvc>
    ```

    Dans `requirements.txt`, à la même version ou au même commit que `forge-mvc`.
    Sans cette ligne, l'opt-in n'existe que sur votre machine.

    #### 2. L'inscrire

    ```bash
    forge opt-in:enable stats --apply
    ```

    L'opt-in est inscrit dans `optins/registry.py` (ADR-061), ce qui le rend visible du
    projet.
    `--apply` est **obligatoire** : sans lui, la commande simule et n'écrit rien.

    #### 3. Poser sa base

    Rien à faire : cet opt-in n'apporte aucune table.

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
    forge opt-in:disable stats
    pip uninstall forge-mvc-stats
    ```

    `opt-in:disable` est l'inverse d'`enable` : il dé-inscrit du registre (le code n'était pas câblé), sans toucher au paquet.
    `forge opt-in:remove stats` affiche la commande `pip uninstall` sans l'exécuter.

??? note "5. Commandes"

    Cet opt-in n'expose aucune commande CLI : il s'utilise **par import** dans le code applicatif (voir l'API publique ci-dessous).

??? note "6. Vue d'ensemble rapide"

    | Élément | Valeur |
    |---|---|
    | Paquet | `forge-mvc-stats` |
    | Module | `forge_mvc_stats` |
    | Catégorie | Données et modélisation (ADR-055) |
    | Couche | opt-in (brique optionnelle) |
    | Dépend de | `forge-mvc` et un backend BDD (ADR-054) |
    | API publique | `StatsEvent`, `make_event`, `track_event`, `list_stats_events`, `count_stats_events` |
    | Table SQL | `forge_stats_events` (`STATS_EVENTS_TABLE`, `get_stats_events_schema_sql`) |
    | Exécuteur | injecté en **callable** (`execute`, `fetch_all`) |
    | Exceptions | `StatsEventError`, `StatsAdminError`, `StatsAggregateError` |
    | Principe | aucun tracking automatique, pas de cookie ni d'IP |
    | Décision d'architecture | ADR-037 (agrégation par comptage) |
    | Installation | `pip install --pre forge-mvc-stats` |

??? note "7. Schémas UML"

    Les deux schémas suivants montrent deux vues complémentaires de l'opt-in.

    Le diagramme de classe montre l'événement, les fonctions et l'exécuteur injecté.

    Le diagramme de séquence montre l'enregistrement puis l'agrégation.

    ### 5.1 Diagramme de classe

    Le diagramme de classe montre que toutes les fonctions reçoivent un exécuteur SQL (un callable), jamais une connexion ouverte par le module.

    ```mermaid
    classDiagram
        direction LR

        class stats {
            <<module>>
            +make_event(name, label, category, metadata) StatsEvent
            +track_event(execute, event_or_name, ...) StatsEvent
            +list_stats_events(fetch_all, name, category, limit) list
            +count_stats_events(fetch_all, group_by, ...) list
        }

        class StatsEvent {
            <<dataclass>>
            +str name
            +str label
            +str category
            +dict metadata
        }

        class forge_stats_events {
            <<table>>
            +name
            +label
            +category
            +metadata
            +created_at
        }

        class Executor {
            <<callable>>
            +execute(sql, params)
            +fetch_all(sql, params)
        }

        stats --> StatsEvent : valide / renvoie
        stats --> Executor : reçoit (injecté)
        Executor --> forge_stats_events : lit / écrit
        stats ..> StatsEventError : peut lever

    ```

    À retenir :

    - un `StatsEvent` est validé avant écriture (`make_event`) ;
    - les données vivent dans `forge_stats_events` ;
    - l'exécuteur SQL est passé en argument (`execute` / `fetch_all`) ;
    - rien n'est tracé sans un appel explicite à `track_event`.

    ### 5.2 Diagramme de séquence

    Le diagramme de séquence montre un suivi d'événement puis un comptage par dimension.

    ```mermaid
    sequenceDiagram
        participant App as Code applicatif
        participant Stats as forge_mvc_stats
        participant Exec as Exécuteur (execute/fetch_all)
        participant Table as forge_stats_events

        App->>Stats: track_event(db.execute, "export.pdf", category="export")
        Stats->>Stats: valide le nom et construit StatsEvent
        Stats->>Exec: execute(INSERT, params)
        Exec->>Table: insère la ligne
        App->>Stats: count_stats_events(db.fetch_all, group_by="category")
        Stats->>Exec: fetch_all(SELECT ... GROUP BY)
        Exec-->>Stats: totaux par catégorie
        Stats-->>App: liste de comptages

    ```

    À retenir :

    - `track_event` valide puis insère via l'exécuteur fourni ;
    - le nom d'événement est une chaîne `snake_case` applicative ;
    - `count_stats_events` agrège par la dimension demandée (`group_by`) ;
    - les lectures passent par `fetch_all`, fourni par l'application.

??? note "8. API publique"

    | Élément | Signature | Rôle |
    |---|---|---|
    | `make_event` | `make_event(name, label="", category="general", metadata=None) -> StatsEvent` | construit un événement validé |
    | `track_event` | `track_event(execute, event_or_name, label="", category="general", metadata=None) -> StatsEvent` | insère un événement |
    | `list_stats_events` | `list_stats_events(fetch_all, name=None, category=None, limit=...) -> list` | liste les événements |
    | `count_stats_events` | `count_stats_events(fetch_all, group_by, name=None, category=None, since=None) -> list` | compte par dimension |
    | `StatsEvent` | dataclass | `name`, `label`, `category`, `metadata` |
    | `STATS_EVENTS_TABLE` | `"forge_stats_events"` | nom de la table |
    | `get_stats_events_schema_sql` | fonction | SQL de création de la table |
    | `StatsEventError`, `StatsAdminError`, `StatsAggregateError` | exceptions | nom invalide, lecture invalide, agrégation invalide |

    `execute` et `fetch_all` sont des callables fournis par l'application (par exemple `db.execute`, `db.fetch_all`).

??? note "9. Contextes d'utilisation"

    | Besoin | Élément |
    |---|---|
    | Tracer une action | `track_event(execute, "nom")` |
    | Catégoriser | paramètre `category=...` |
    | Joindre des métadonnées | paramètre `metadata=...` |
    | Lister les événements | `list_stats_events(fetch_all)` |
    | Compter par dimension | `count_stats_events(fetch_all, group_by=...)` |
    | Créer la table | `get_stats_events_schema_sql()` |

??? note "10. Exemples d'utilisation"

    ### 8.1 Tracer un événement

    ```python
    import core.database.db as db
    from forge_mvc_stats import track_event

    track_event(db.execute, "export.pdf", category="export", metadata={"pages": 12})
    ```

    L'exécuteur (`db.execute`) est passé explicitement : le module n'ouvre pas de connexion.

    ### 8.2 Compter par catégorie

    ```python
    import core.database.db as db
    from forge_mvc_stats import count_stats_events

    totaux = count_stats_events(db.fetch_all, group_by="category")
    # [{"category": "export", "count": 42}, {"category": "login", "count": 130}, ...]
    ```

    !!! tip "Aide-mémoire"
        Un événement, deux lectures :

        - `track_event` pour écrire ;
        - `list_stats_events` (détail) et `count_stats_events` (agrégat).

??? note "11. Tracking explicite et exécuteur injecté"

    Forge ne trace rien de lui-même : pas de middleware caché, pas de cookie, pas d'IP.
    Le développeur décide quoi compter avec `track_event`.

    Les noms d'événements sont des chaînes `snake_case` définies par l'application (principe 1) ; un nom invalide lève `StatsEventError`.

    !!! note "SQL visible et exécuteur injecté"
        Les fonctions reçoivent `execute` / `fetch_all` en argument : le module ne crée jamais de connexion et le SQL reste visible.

        En test, injectez de faux callables pour vérifier les requêtes sans base.

    !!! note "Agrégation par comptage"
        `count_stats_events` agrège par `GROUP BY` sur la dimension demandée (ADR-037).

        C'est volontairement simple : des comptes, pas un moteur d'analytics.

    !!! note "Indépendance du cœur"
        Le cœur de Forge ne dépend pas de `forge-mvc-stats` : la dépendance va de l'opt-in vers le cœur.

## Voir aussi

- [Événements (events.py)](references/events.md) : `StatsEvent`, validation des noms.
- [Table SQL (schema.py)](references/schema.md) : `forge_stats_events`.
- [Tracking (tracking.py)](references/tracking.md) : `track_event`.
- [Affichage admin (admin.py)](references/admin.md) : lister et filtrer.
- [Agrégation (aggregate.py)](references/aggregate.md) : compter par dimension (ADR-037).
- [Welcome-Stats](welcome/debutant/stats-welcome.md) : parcours d'apprentissage.
