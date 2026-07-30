# Le backend SQLite dans Forge (forge-mvc-sqlite)

Ce document explique ce que fait l'opt-in `forge-mvc-sqlite`, ce qu'il expose, et comment on s'en sert.

`forge-mvc-sqlite` est un **backend de base de données** pour Forge : il fait fonctionner la couche BDD du cœur au-dessus de `sqlite3` (bibliothèque standard), sans serveur ni dépendance externe.

Le cœur de Forge est agnostique BDD (ADR-054) : il découvre le backend installé par un entry point, et n'en utilise **qu'un seul** par projet.

??? note "1. Rôle du module"

    Le cœur sait générer du SQL et piloter `db:init` / `db:apply` / `migration:*`, mais il ne parle à aucune base directement : c'est le rôle d'un backend.

    `forge-mvc-sqlite` fournit ce backend : une connexion `sqlite3` adaptée aux attentes du cœur (curseur lignes-dict, `lastrowid`, `autocommit`) et un dialecte SQL propre à SQLite.

    SQLite est **sans serveur** : la base est un simple fichier (`DB_NAME`).
    C'est le choix idéal en développement, en test et pour l'onboarding.

??? note "2. Installation"

    SQLite est **sans serveur** : la base est un simple fichier local, sans serveur à joindre ni comptes à créer.
    Le module `sqlite3` fait partie de la bibliothèque standard de Python, donc aucune dépendance externe.

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
    pip install --pre forge-mvc-sqlite
    ```

    </div>

    <div class="canal">

    #### B. Depuis Git (avant-garde)

    Cœur puis backend depuis git, dans le venv du projet, à la même version (le backend trouve le cœur git déjà en place, sans version publiée sur PyPI) :

    ```bash
    pip install "git+https://github.com/caucrogeGit/Forge.git@main"
    pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-sqlite"
    ```

    </div>

    Le cœur découvre le backend par son entry point `forge_mvc.db_backend` : aucune commande d'activation n'est nécessaire.

??? note "3. Mise en service"

    Installer le paquet ne suffit pas à le rendre opérationnel.
    Voici les gestes propres à `forge-mvc-sqlite`, dans l'ordre.

    Ils déclinent la procédure canonique, [Rendre un opt-in opérationnel : les cinq
    points](/docs/forge/install/opt-ins/#rendre-un-opt-in-operationnel-les-cinq-points),
    adaptée à un backend : il n'y a pas d'inscription au registre, le cœur le découvre par
    son entry point.

    #### 1. L'épingler

    ```text
    forge-mvc-sqlite==<version de forge-mvc>
    ```

    Dans `requirements.txt`, à la même version ou au même commit que `forge-mvc`.
    Sans cette ligne, le pilote n'existe que sur votre machine, et l'application démarre
    sans backend chez un collègue, sur un serveur ou en intégration continue.

    #### 2. Configurer, provisionner et vérifier

    `forge db:config` pose `DB_NAME` (le chemin du fichier de base) dans `env/example`, `env/dev` et `env/prod` (write-if-missing ; ADR-064) :

    ```bash
    forge db:config
    ```

    Ajustez au besoin le chemin dans `env/dev` :

    ```env
    DB_NAME=storage/mon_projet.db
    ```

    `forge doctor` confirme le backend résolu (`sqlite`) ; si plusieurs backends sont installés, fixez `DB_BACKEND=sqlite`.
    `forge db:init` crée alors le fichier et la table technique `forge_migrations` : aucun serveur n'est contacté.

    La progression guidée, pas à pas : [Installation de forge-mvc-sqlite](welcome/debutant/sqlite-welcome.md).

??? note "4. Désinstallation"

    Retirez d'abord la configuration des fichiers d'environnement, puis le paquet :

    ```bash
    forge db:config --remove
    pip uninstall forge-mvc-sqlite
    ```

    `db:config --remove` retire les clés `DB_*` posées par `db:config` des trois fichiers d'environnement (les valeurs renseignées sont perdues ; ADR-064).
    Un backend n'a pas de commande `disable` : découvert par entry point (ADR-054), retirer le paquet suffit ensuite à ce que le cœur ne le voie plus.
    Si besoin, supprimez aussi la base et le compte créés par `db:init`.

??? note "5. Commandes"

    Ce backend n'ajoute aucune commande : il est découvert par l'entry point `forge_mvc.db_backend` et fournit, au runtime, un dialecte SQL et un adaptateur de connexion.
    Les commandes de base de données que vous utilisez avec lui sont fournies par le moteur d'entités (`forge-mvc-entities`) :

    | Commande | Rôle | Exemple |
    |---|---|---|
    | `db:config` | Amorce les variables du backend dans `env/*` (write-if-missing). | `forge db:config` |
    | `db:init` | Affiche le SQL de provisioning ; `--run` l'exécute. | `forge db:init --run` |
    | `db:apply` | Applique le SQL des entités à la base. | `forge db:apply` |
    | `migration:make` | Génère une migration depuis l'écart de schéma. | `forge migration:make` |
    | `migration:apply` | Applique les migrations en attente. | `forge migration:apply` |

??? note "6. Vue d'ensemble rapide"

    | Élément | Valeur |
    |---|---|
    | Paquet | `forge-mvc-sqlite` |
    | Module | `forge_mvc_sqlite` |
    | Catégorie | Bases de données (ADR-055) |
    | Couche | backend BDD opt-in **exclusif** (un seul par projet) |
    | Dépend de | `forge-mvc` (et `sqlite3` de la bibliothèque standard) |
    | Découverte | entry point `forge_mvc.db_backend` nommé `sqlite` |
    | Sélection | automatique si seul installé ; sinon `DB_BACKEND=sqlite` |
    | Provisioning | **aucun** (sans serveur) : `db:init` crée le fichier |
    | Base | un fichier sur disque (chemin = `DB_NAME`) |
    | Décision d'architecture | ADR-054 (cœur agnostique BDD) |
    | Installation | `pip install --pre forge-mvc-sqlite` |

??? note "7. Schémas UML"

    Les deux schémas suivants montrent deux vues complémentaires du backend.

    Le diagramme de classe montre comment le cœur consomme le backend.

    Le diagramme de séquence montre la résolution du backend puis une requête.

    ### 5.1 Diagramme de classe

    Le diagramme de classe montre que le cœur résout un `DatabaseBackend` par entry point, et que `forge-mvc-sqlite` le fournit avec son dialecte.

    ```mermaid
    classDiagram
        direction LR

        class DatabaseBackend {
            <<protocol, cœur>>
            +name
            +dialect
            +requires_provisioning
            +get_connection()
        }

        class SQLiteBackend {
            +name = "sqlite"
            +requires_provisioning = false
            +get_connection() connexion
        }

        class SQLiteDialect {
            +types SQLite
            +AUTOINCREMENT
            +CREATE INDEX séparés
        }

        class fichier {
            <<base>>
            +DB_NAME (fichier)
        }

        SQLiteBackend ..|> DatabaseBackend : implémente
        SQLiteBackend --> SQLiteDialect : dialecte
        SQLiteBackend --> fichier : ouvre

    ```

    À retenir :

    - le cœur ne connaît que le contrat `DatabaseBackend` ;
    - `forge-mvc-sqlite` l'implémente au-dessus de `sqlite3` ;
    - le dialecte traduit les types et la DDL en SQL SQLite ;
    - la base est un fichier, pas un service.

    ### 5.2 Diagramme de séquence

    Le diagramme de séquence montre la découverte du backend puis une requête applicative.

    ```mermaid
    sequenceDiagram
        participant App as Application / CLI
        participant Core as core.database
        participant Backend as forge-mvc-sqlite
        participant File as fichier SQLite

        App->>Core: première requête (ou db:init)
        Core->>Core: résout l'entry point forge_mvc.db_backend
        Core->>Backend: get_connection()
        Backend->>File: ouvre DB_NAME
        Backend-->>Core: connexion (lignes-dict, lastrowid)
        Core-->>App: résultat de la requête

    ```

    À retenir :

    - le backend est résolu une fois, par entry point ;
    - s'il y a plusieurs backends installés, `DB_BACKEND` tranche ;
    - la connexion est adaptée au format attendu par le cœur ;
    - aucune étape réseau : c'est un fichier local.

??? note "8. Ce que fournit le backend"

    | Élément | Rôle |
    |---|---|
    | `SQLiteBackend` | implémente le contrat `DatabaseBackend` du cœur |
    | Adaptateur de connexion | curseur `dictionary=`, `lastrowid`, `autocommit` au-dessus de `sqlite3` |
    | `SQLiteDialect` | types SQLite, `INTEGER PRIMARY KEY AUTOINCREMENT`, `CREATE INDEX` séparés |
    | Entry point | `forge_mvc.db_backend = sqlite` (découverte par le cœur) |

    L'API que vous utilisez reste celle du cœur : `db:init`, `db:apply`, `migration:*`, et `core.database.db` dans le code.

??? note "9. Contextes d'utilisation"

    | Besoin | Élément |
    |---|---|
    | Démarrer sans installer de serveur | installer `forge-mvc-sqlite` |
    | Forcer ce backend | `DB_BACKEND=sqlite` |
    | Créer la base | `forge db:init` (crée le fichier) |
    | Appliquer le schéma | `forge db:apply` |
    | Faire évoluer le schéma | `forge migration:make` / `migration:apply` |
    | Lire/écrire en code | `core.database.db` |

??? note "10. Exemple d'utilisation"

    ```bash
    pip install --pre forge-mvc-sqlite     # seul backend installé
    forge db:init                          # crée le fichier SQLite + forge_migrations
    forge db:apply                         # applique le schéma des entités
    ```

    ```python
    import core.database.db as db
    rows = db.fetch_all("SELECT * FROM article", ())
    ```

    Le code applicatif ne sait pas qu'il parle à SQLite : il utilise la couche BDD du cœur.

    !!! tip "Aide-mémoire"
        Installer suffit :

        - un seul backend installé est choisi automatiquement ;
        - `db:init` crée le fichier, `db:apply` applique le schéma ;
        - le code utilise `core.database.db`, pas `sqlite3`.

??? note "11. Sans serveur, exclusif, et dialecte"

    SQLite n'a pas de serveur : `requires_provisioning=False`, donc `db:init` ne crée ni compte ni base distante, il prépare le fichier et la table `forge_migrations`.

    Un seul backend BDD par projet : si plusieurs sont installés, fixez `DB_BACKEND` pour lever l'ambiguïté.

    !!! note "Idéal en développement et en test"
        Pas d'installation de serveur, une base = un fichier : on démarre en une commande.

        Pour la production multi-utilisateurs, un backend serveur (MariaDB, PostgreSQL) est généralement préférable.

    !!! note "Dialecte SQLite"
        Le dialecte gère les spécificités : `INTEGER PRIMARY KEY AUTOINCREMENT`, `CREATE INDEX` en instructions séparées, affinités de types.

        Le SQL généré reste lisible (principe 5).

    !!! note "Clés étrangères armées à chaque connexion"
        SQLite laisse `PRAGMA foreign_keys` inactif par défaut, par compatibilité ascendante, et le réglage vaut pour une connexion seulement.
        Le backend l'arme donc à chaque emprunt.
        Sans lui, les contraintes écrites par `make:relation` ne contraignaient rien.
        Un enfant orphelin entrait, et `ON DELETE CASCADE` ne cascadait pas.

        La conséquence portait loin, car SQLite sert en développement et un SGBD serveur en production.
        Le défaut ne se voyait jamais chez le développeur, toujours chez l'utilisateur, sur des données déjà incohérentes.

        Une base SQLite créée avant cette version peut contenir des lignes orphelines.
        Elles ne bloquent pas la lecture, mais toute écriture qui les toucherait sera désormais refusée.

    !!! note "Fichier verrouillé, réponse 503"
        SQLite n'admet qu'un écrivain à la fois.
        Une sauvegarde, un `fixtures:load` ou un second processus qui tient une transaction fait attendre, puis échouer au delà du délai.
        En mode journal par défaut, le verrou exclusif tient aussi les lecteurs à distance, donc c'est le site entier qui patiente.

        Forge y voit une indisponibilité passagère et répond `503` avec `Retry-After`, comme devant un pool saturé.
        Un `500` aurait envoyé chercher un bug dans le code applicatif, alors que le remède est d'attendre ou de raccourcir la transaction voisine.

        Le temps d'attente se règle par `DB_POOL_TIMEOUT`, la variable que MariaDB emploie déjà pour patienter devant son pool.
        Sa valeur par défaut est de cinq secondes.

    !!! note "Indépendance du cœur"
        Le cœur de Forge ne dépend pas de `forge-mvc-sqlite` : il le découvre par entry point (ADR-054).

## Voir aussi

- [Welcome-SQLite](welcome/debutant/sqlite-welcome.md) : apprendre le backend pas à pas.
- [ADR-054](https://forgemvc.com/docs/forge/adr/054-database-backend-optins/) : cœur agnostique BDD.
