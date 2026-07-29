# Le backend MariaDB dans Forge (forge-mvc-mariadb)

Ce document explique ce que fait l'opt-in `forge-mvc-mariadb`, ce qu'il expose, et comment on s'en sert.

`forge-mvc-mariadb` est **un** backend de base de données **de production** pour Forge : il fait fonctionner la couche BDD du cœur au-dessus d'un serveur MariaDB, via un pool de connexions.

Le cœur de Forge est agnostique BDD ([ADR-054](/docs/forge/adr/054-database-backend-optins/)) : il découvre le backend installé par un entry point, et n'en utilise **qu'un seul** par projet, au choix du développeur (MariaDB, SQLite, PostgreSQL ou SQL Server).
Forge n'impose aucun backend de référence.

??? note "1. Rôle du module"
    Le cœur génère le SQL et pilote `db:init` / `db:apply` / `migration:*`, mais ne parle à aucune base directement : c'est le rôle d'un backend.

    `forge-mvc-mariadb` fournit ce backend : un pool de connexions MariaDB adapté aux attentes du cœur (curseur lignes-dict, `lastrowid`, `autocommit`), un dialecte SQL MariaDB, et le **provisioning** de la base et des comptes par `db:init`.

    MariaDB est **client-serveur** : un serveur doit être joignable.
    C'est un choix éprouvé pour la production.

??? note "2. Installation"
    MariaDB est client-serveur : un serveur doit être joignable (local, conteneur ou distant).
    Le pilote `mariadb` est installé avec l'opt-in.
    L'installation pose le paquet ; la **mise en service** fait l'objet du chapitre suivant.

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
    pip install --pre forge-mvc-mariadb
    ```

    </div>

    <div class="canal">

    #### B. Depuis Git (avant-garde)

    Les nouveautés pas encore publiées, ou si votre projet a été créé depuis `main`.
    Installez le CLI `forge-mvc` **et** le backend à la même version : sinon `db:config` et `db:init` se désynchronisent du backend.
    On installe le **cœur d'abord** (depuis git, avec ses dépendances), puis le backend : celui-ci trouve alors le cœur git déjà en place et n'a pas besoin d'une version publiée sur PyPI.

    ```bash
    pip install "git+https://github.com/caucrogeGit/Forge.git@main"
    pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-mariadb"
    ```

    </div>

    Le cœur découvre le backend par son entry point `forge_mvc.db_backend` : aucune commande d'activation n'est nécessaire, contrairement aux opt-ins de route.

??? note "3. Mise en service"

    Installer le paquet ne suffit pas à le rendre opérationnel.
    Voici les gestes propres à `forge-mvc-mariadb`, dans l'ordre.

    Ils déclinent la procédure canonique, [Rendre un opt-in opérationnel : les cinq
    points](/docs/forge/install/opt-ins/#rendre-un-opt-in-operationnel-les-cinq-points),
    adaptée à un backend : il n'y a pas d'inscription au registre, le cœur le découvre par
    son entry point.

    #### 1. L'épingler

    ```text
    forge-mvc-mariadb==<version de forge-mvc>
    ```

    Dans `requirements.txt`, à la même version ou au même commit que `forge-mvc`.
    Sans cette ligne, le pilote n'existe que sur votre machine, et l'application démarre
    sans backend chez un collègue, sur un serveur ou en intégration continue.

    #### 2. Amorcer l'environnement

    `forge db:config` amorce les variables du backend dans `env/example`, `env/dev` et `env/prod` (write-if-missing, annoncé, sans secret ; [ADR-064](/docs/forge/adr/064-db-config-env-scaffold/)) :

    ```bash
    forge db:config
    ```

    #### 3. Renseigner les accès

    Renseignez les valeurs dans `env/dev` (et `env/prod`).
    Vous choisissez librement les deux comptes que le script de l'étape 4 créera :

    ```env
    DB_NAME=mon_projet
    DB_HOST=127.0.0.1
    DB_PORT=3306
    DB_ADMIN_LOGIN=mon_projet_admin
    DB_ADMIN_PWD=...
    DB_APP_LOGIN=mon_projet_app
    DB_APP_PWD=...
    ```

    `DB_ADMIN_*` est le compte **propriétaire de la base du projet** (DDL : `db:apply`, migrations), pas le root du serveur.
    `DB_APP_*` est le compte de **runtime** (DML strict).
    Les deux sont créés par le script de l'étape 4.

    ##### Dimensionner le pool

    Deux clés facultatives règlent le pool de connexions.

    | Clé | Défaut | Rôle |
    |---|---|---|
    | `DB_POOL_SIZE` | `5` | connexions **simultanées** au serveur |
    | `DB_POOL_TIMEOUT` | `5` | secondes d'attente avant d'abandonner |

    `DB_POOL_SIZE` ne borne pas le **volume** de requêtes, seulement le nombre en vol au même instant.
    Mesuré sur une lecture indexée de 0,26 ms, cinq connexions servent près de 19 000 requêtes par seconde.

    Une requête qui arrive alors que toutes les connexions sont prises **patiente** dans une file d'attente, elle n'échoue pas.
    Ce n'est qu'au bout de `DB_POOL_TIMEOUT` que Forge renonce, avec une réponse `503` et un en-tête `Retry-After` : une saturation est passagère, elle ne mérite pas la page d'erreur 500 qui annoncerait un défaut de l'application.

    Une seconde situation rend le même `503` : la connexion empruntée avait été fermée par le serveur, sans que le pool le sache.
    C'est le cas après un redémarrage ou une bascule, et après une longue inactivité (`wait_timeout`).
    Le pilote revalide au delà d'une demi-seconde d'inactivité, mais en deçà il livre la connexion morte.
    Le journal distingue les deux causes, ce qui évite d'élargir un pool qui n'était pas en cause.

    Règle de dimensionnement : au moins autant de connexions que de requêtes réellement concurrentes par processus.
    Gunicorn en mode threadé donne un ordre de grandeur avec son nombre de threads par worker ; **chaque worker a son propre pool**, la charge du serveur est donc le produit des deux.
    Élargir le pool coûte des connexions côté serveur (`max_connections`), pas de la mémoire côté application.

    #### 4. Provisionner la base

    `forge db:init` **affiche** le SQL de provisioning (création de la base et des deux comptes, scellés à `DB_NAME`), dérivé de `env/`, sans se connecter ([ADR-067](/docs/forge/adr/067-db-init-provisioning-sql/)) :

    ```bash
    forge db:init
    ```

    Collez le script affiché dans une session d'administration MariaDB (Forge ne demande jamais le root du serveur) :

    ```bash
    sudo mariadb
    ```

    Si vous disposez d'un compte d'administration serveur et préférez que Forge exécute le provisioning lui-même, utilisez `forge db:init --run`.

    #### 5. Vérifier et appliquer

    La base et les comptes créés, vérifiez la connexion puis créez le schéma des entités :

    ```bash
    forge doctor
    forge db:apply
    ```

    `forge doctor` indique le backend résolu et l'état de la connexion (la ligne `Base de données` doit passer `[OK]`) ; si plusieurs backends sont installés, fixez `DB_BACKEND=mariadb`.


??? note "4. Désinstallation"

    Retirez d'abord la configuration des fichiers d'environnement, puis le paquet :

    ```bash
    forge db:config --remove
    pip uninstall forge-mvc-mariadb
    ```

    `db:config --remove` retire les clés `DB_*` posées par `db:config` des trois fichiers d'environnement (les valeurs renseignées sont perdues ; [ADR-064](/docs/forge/adr/064-db-config-env-scaffold/)).
    Un backend n'a pas de commande `disable` : découvert par entry point ([ADR-054](/docs/forge/adr/054-database-backend-optins/)), retirer le paquet suffit ensuite à ce que le cœur ne le voie plus.
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
    | Paquet | `forge-mvc-mariadb` |
    | Module | `forge_mvc_mariadb` |
    | Catégorie | Bases de données ([ADR-055](/docs/forge/adr/055-optin-categories/)) |
    | Couche | backend BDD opt-in **exclusif** (un seul par projet) |
    | Dépend de | `forge-mvc`, `mariadb` (pilote), un serveur MariaDB |
    | Découverte | entry point `forge_mvc.db_backend` nommé `mariadb` |
    | Sélection | automatique si seul installé ; sinon `DB_BACKEND=mariadb` |
    | Provisioning | **oui** : `db:init` crée base + compte via `DB_ADMIN_*` |
    | Comptes | `DB_ADMIN_*` (DDL, migrations) et `DB_APP_*` (runtime, DML) ([ADR-033](/docs/forge/adr/033-migrations-admin-credentials/)) |
    | Connexions | pool thread-safe |
    | Décision d'architecture | [ADR-054](/docs/forge/adr/054-database-backend-optins/) (cœur agnostique BDD) |
    | Installation | `pip install --pre forge-mvc-mariadb` |

??? note "7. Schémas UML"
    Les deux schémas suivants montrent deux vues complémentaires du backend.

    Le diagramme de classe montre comment le cœur consomme le backend.

    Le diagramme de séquence montre le provisioning puis une requête runtime.

    #### Diagramme de classe

    Le diagramme de classe montre que le cœur résout un `DatabaseBackend` par entry point, et que `forge-mvc-mariadb` le fournit avec son pool et son dialecte.

    ```mermaid
    classDiagram
        direction LR

        class DatabaseBackend {
            <<protocol, cœur>>
            +name
            +dialect
            +requires_provisioning
            +get_connection()
            +get_admin_connection()
        }

        class MariaDBBackend {
            +name = "mariadb"
            +requires_provisioning = true
            +get_connection() pool
            +get_admin_connection(...)
        }

        class MariaDBDialect {
            +types MariaDB
            +AUTO_INCREMENT
            +ENGINE=InnoDB
            +INDEX inline
        }

        class Serveur {
            <<service>>
            +MariaDB
        }

        MariaDBBackend ..|> DatabaseBackend : implémente
        MariaDBBackend --> MariaDBDialect : dialecte
        MariaDBBackend --> Serveur : pool / admin

    ```

    À retenir :

    - le cœur ne connaît que le contrat `DatabaseBackend` ;
    - `forge-mvc-mariadb` l'implémente avec un pool de connexions ;
    - la connexion d'administration (`DB_ADMIN_*`) sert le provisioning et la DDL ;
    - le dialecte traduit types et DDL en SQL MariaDB.

    #### Diagramme de séquence

    Le diagramme de séquence montre le provisioning par `db:init`, puis une requête runtime.

    ```mermaid
    sequenceDiagram
        participant Op as Opérateur (CLI)
        participant Core as core.database
        participant Backend as forge-mvc-mariadb
        participant Server as Serveur MariaDB

        Op->>Core: forge db:init
        Core->>Backend: get_admin_connection(DB_ADMIN_*)
        Backend->>Server: CREATE DATABASE / USER / GRANT
        Op->>Core: forge db:apply
        Core->>Backend: connexion admin (DDL)
        Backend->>Server: crée les tables

        Note over Core,Server: au runtime, l'application utilise DB_APP_*
        Core->>Backend: get_connection() (pool, DB_APP_*)
        Backend->>Server: requête DML

    ```

    À retenir :

    - `db:init` provisionne base et compte avec `DB_ADMIN_*` ;
    - `db:apply` et les migrations utilisent aussi le compte admin (DDL) ;
    - le runtime utilise le compte applicatif `DB_APP_*` (DML strict) ;
    - la séparation des comptes suit l'[ADR-033](/docs/forge/adr/033-migrations-admin-credentials/).

??? note "8. Ce que fournit le backend"
    | Élément | Rôle |
    |---|---|
    | `MariaDBBackend` | implémente le contrat `DatabaseBackend` (pool + connexion admin) |
    | Pool de connexions | connexions thread-safe pour le runtime |
    | `MariaDBDialect` | types MariaDB, `AUTO_INCREMENT`, `ENGINE=InnoDB`, index inline |
    | Provisioning | `db:init` crée la base et le compte applicatif |
    | Entry point | `forge_mvc.db_backend = mariadb` |

    L'API que vous utilisez reste celle du cœur : `db:init`, `db:apply`, `migration:*`, et `core.database.db`.

??? note "9. Contextes d'utilisation"
    | Besoin | Élément |
    |---|---|
    | Backend de production | installer `forge-mvc-mariadb` + un serveur MariaDB |
    | Forcer ce backend | `DB_BACKEND=mariadb` |
    | Provisionner base + compte | `forge db:init` (avec `DB_ADMIN_*`) |
    | Appliquer le schéma | `forge db:apply` |
    | Faire évoluer le schéma | `forge migration:make` / `migration:apply` |
    | Lire/écrire en code | `core.database.db` (compte `DB_APP_*`) |

??? note "10. Exemple d'utilisation"
    Configurer l'environnement (`env/dev`), puis :

    ```bash
    pip install --pre forge-mvc-mariadb
    forge db:init      # crée la base et le compte applicatif (DB_ADMIN_*)
    forge db:apply     # applique le schéma des entités
    ```

    ```python
    import core.database.db as db
    rows = db.fetch_all("SELECT * FROM article", ())
    ```

    Le code applicatif ne sait pas qu'il parle à MariaDB : il utilise la couche BDD du cœur.

    !!! tip "Aide-mémoire"
        Deux comptes, un serveur :

        - `DB_ADMIN_*` pour provisionner et faire la DDL (`db:init`, `db:apply`, migrations) ;
        - `DB_APP_*` pour le runtime (DML) ;
        - le code utilise `core.database.db`, pas `mariadb`.

??? note "11. Serveur, comptes et dialecte"
    MariaDB est client-serveur : un serveur doit être joignable.
    `forge doctor` aide à diagnostiquer la connexion.

    Deux comptes séparent les responsabilités ([ADR-033](/docs/forge/adr/033-migrations-admin-credentials/)) : `DB_ADMIN_*` pour la structure, `DB_APP_*` (DML strict) pour le runtime, ce qui limite les droits de l'application en exécution.

    !!! warning "Provisioning et droits"
        `db:init` a besoin de `DB_ADMIN_*` avec les droits de créer une base, un utilisateur et d'accorder des privilèges.

        Le compte runtime `DB_APP_*` reste volontairement limité au DML.

    !!! note "Dialecte MariaDB"
        Le dialecte gère `AUTO_INCREMENT`, `ENGINE=InnoDB DEFAULT CHARSET=utf8mb4`, les index dans le `CREATE TABLE`, les backticks.

        Le SQL généré reste lisible (principe 5).

    !!! warning "Une migration qui échoue en cours de route ne s'annule pas"
        MariaDB valide implicitement autour de chaque instruction de définition (`CREATE`, `ALTER`, `DROP`).
        Une migration dont la troisième instruction échoue laisse donc les deux premières en place, malgré l'annulation.
        C'est le seul des quatre backends dans ce cas : PostgreSQL, SQL Server et SQLite annulent la migration entière.

        La migration n'étant pas enregistrée au journal, `migration:apply` la rejouera depuis le début et butera sur ce qui existe déjà.
        Forge le dit dans le message d'échec, en nommant l'instruction fautive et le nombre d'instructions qui persistent.
        Le rattrapage est manuel : défaire en base les effets des instructions déjà passées, puis relancer.

        La parade est en amont : appliquer d'abord la migration sur une base de test, et relire son SQL avec `forge migration:apply --dry-run`, qui l'imprime sans rien exécuter.

    !!! note "Indépendance du cœur"
        Le cœur de Forge ne dépend pas de `forge-mvc-mariadb` : il le découvre par entry point ([ADR-054](/docs/forge/adr/054-database-backend-optins/)).

## Voir aussi

- [Welcome-MariaDB](welcome/debutant/mariadb-welcome.md) : apprendre le backend pas à pas.
