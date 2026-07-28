# Le backend SQL Server dans Forge (forge-mvc-mssql)

Ce document explique ce que fait l'opt-in `forge-mvc-mssql`, ce qu'il expose, et comment on s'en sert.

`forge-mvc-mssql` est un **backend de base de données** pour Forge, au-dessus de `pyodbc`, pour faire fonctionner la couche BDD du cœur sur Microsoft SQL Server.

Le cœur de Forge est agnostique BDD (ADR-054) : il découvre le backend installé par un entry point et n'en utilise qu'un seul par projet.

!!! note "Niveau plein"
    Backend au **niveau plein** (ADR-084, révision du 2026-07-19) : `db:init` provisionne SQL Server, l'identité d'insertion est fiable, et l'intégration est validée en CI contre un vrai SQL Server 2022.

    Un pilote ODBC système reste requis sur la machine cliente (« ODBC Driver 18 for SQL Server » par défaut).

??? note "1. Rôle du module"

    Le cœur génère le SQL et pilote les commandes BDD ; un backend les fait parler à un vrai serveur.

    `forge-mvc-mssql` fournit ce backend pour SQL Server : un adaptateur de connexion `pyodbc` conforme aux attentes du cœur, un dialecte Transact-SQL, et le **provisioning** de la base et des comptes par `db:init`.

    Bonne nouvelle côté paramètres : `pyodbc` utilise nativement les `?` de Forge, donc aucune traduction.

??? note "2. Installation et désinstallation"

    SQL Server est **client-serveur** : un serveur doit être joignable.
    Le pilote est `pyodbc`, qui requiert un pilote ODBC système.

    === "Depuis PyPI (stable)"

        La dernière version publiée :

        ```bash
        pip install --pre forge-mvc-mssql
        ```

    === "Depuis Git (avant-garde)"

        Cœur puis backend depuis git, dans le venv du projet, à la même version (le backend trouve le cœur git déjà en place, sans version publiée sur PyPI) :

        ```bash
        source .venv/bin/activate
        pip install "git+https://github.com/caucrogeGit/Forge.git@main"
        pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-mssql"
        ```

        !!! warning "Erreur « externally-managed-environment » ?"

            Lancées hors d'un venv, ces commandes visent le Python **système** (Debian 12+, Ubuntu 23.04+), protégé par PEP 668.
            La cible correcte est le venv du projet (`source .venv/bin/activate`), jamais le Python système.


    Le cœur découvre le backend par son entry point `forge_mvc.db_backend` : aucune commande d'activation n'est nécessaire.
    ### Désinstallation

    Retirez d'abord la configuration des fichiers d'environnement, puis le paquet :

    ```bash
    forge db:config --remove
    pip uninstall forge-mvc-mssql
    ```

    `db:config --remove` retire les clés `DB_*` posées par `db:config` des trois fichiers d'environnement (les valeurs renseignées sont perdues ; ADR-064).
    Un backend n'a pas de commande `disable` : découvert par entry point (ADR-054), retirer le paquet suffit ensuite à ce que le cœur ne le voie plus.
    Si besoin, supprimez aussi la base et le compte créés par `db:init`.

??? note "3. Mise en service"

    Installer le paquet ne suffit pas à le rendre opérationnel.
    Voici les gestes propres à `forge-mvc-mssql`, dans l'ordre.

    Ils déclinent la procédure canonique, [Rendre un opt-in opérationnel : les cinq
    points](/docs/forge/install/opt-ins/#rendre-un-opt-in-operationnel-les-cinq-points),
    adaptée à un backend : il n'y a pas d'inscription au registre, le cœur le découvre par
    son entry point.

    #### 1. L'épingler

    ```text
    forge-mvc-mssql==<version de forge-mvc>
    ```

    Dans `requirements.txt`, à la même version ou au même commit que `forge-mvc`.
    Sans cette ligne, le pilote n'existe que sur votre machine, et l'application démarre
    sans backend chez un collègue, sur un serveur ou en intégration continue.

    #### 2. Configurer, provisionner et vérifier

    `forge db:config` amorce les variables du backend dans `env/example`, `env/dev` et `env/prod` (write-if-missing, sans secret ; ADR-064) :

    ```bash
    forge db:config
    ```

    Renseignez ensuite les valeurs dans `env/dev` (et `env/prod`) :

    ```env
    DB_NAME=mon_projet
    DB_HOST=127.0.0.1
    DB_PORT=1433
    DB_ADMIN_LOGIN=sa
    DB_ADMIN_PWD=...
    DB_APP_LOGIN=mon_projet
    DB_APP_PWD=...
    DB_ODBC_DRIVER=ODBC Driver 18 for SQL Server
    ```

    `forge doctor` confirme le backend résolu (`mssql`) ; si plusieurs backends sont installés, fixez `DB_BACKEND=mssql`.

    `forge db:init` **affiche** le SQL de provisioning dérivé de `env/`, sans se connecter (ADR-067) : logins d'administration et applicatif, base, utilisateurs, `GRANT` sur `SCHEMA::dbo`, table `forge_migrations`, en lots séparés par `GO` pour `sqlcmd` :

    ```bash
    forge db:init
    ```

    `forge db:init --run` exécute ce provisioning avec le compte `DB_ADMIN_*`, qui doit exister sur le serveur : la base, la connexion et l'utilisateur applicatifs et le registre des migrations sont créés.

    La progression guidée, pas à pas : [Installation de forge-mvc-mssql](welcome/debutant/mssql-welcome.md).

??? note "4. Commandes"

    Ce backend n'ajoute aucune commande : il est découvert par l'entry point `forge_mvc.db_backend` et fournit, au runtime, un dialecte SQL et un adaptateur de connexion.
    Les commandes de base de données que vous utilisez avec lui sont fournies par le moteur d'entités (`forge-mvc-entities`) :

    | Commande | Rôle | Exemple |
    |---|---|---|
    | `db:config` | Amorce les variables du backend dans `env/*` (write-if-missing). | `forge db:config` |
    | `db:init` | Affiche le SQL de provisioning ; `--run` l'exécute. | `forge db:init --run` |
    | `db:apply` | Applique le SQL des entités à la base. | `forge db:apply` |
    | `migration:make` | Génère une migration depuis l'écart de schéma. | `forge migration:make` |
    | `migration:apply` | Applique les migrations en attente. | `forge migration:apply` |

??? note "5. Vue d'ensemble rapide"

    | Élément | Valeur |
    |---|---|
    | Paquet | `forge-mvc-mssql` |
    | Module | `forge_mvc_mssql` |
    | Catégorie | Bases de données (ADR-055) |
    | Statut | **niveau plein** (ADR-084 ; intégration validée en CI contre SQL Server 2022) |
    | Couche | backend BDD opt-in **exclusif** (un seul par projet) |
    | Dépend de | `forge-mvc`, `pyodbc`, un pilote ODBC, un serveur SQL Server |
    | Découverte | entry point `forge_mvc.db_backend` nommé `mssql` |
    | Sélection | automatique si seul installé ; sinon `DB_BACKEND=mssql` |
    | Paramètres | `?` natifs (pyodbc) : aucune traduction |
    | Identité | `BIGINT IDENTITY(1,1)` |
    | Pilote ODBC | « ODBC Driver 18 for SQL Server » par défaut (`DB_ODBC_DRIVER`) |
    | Provisioning | **oui** : `db:init` affiche le SQL ; `--run` l'exécute avec `DB_ADMIN_*` |
    | Décision d'architecture | ADR-054 |
    | Installation | `pip install --pre forge-mvc-mssql` |

??? note "6. Schémas UML"

    Les deux schémas suivants montrent deux vues complémentaires du backend.

    Le diagramme de classe montre l'adaptateur et le dialecte.

    Le diagramme de séquence montre une requête via pyodbc.

    ### 5.1 Diagramme de classe

    Le diagramme de classe montre que le backend enveloppe `pyodbc` pour répondre au contrat du cœur.

    ```mermaid
    classDiagram
        direction LR

        class DatabaseBackend {
            <<protocol, cœur>>
            +name
            +dialect
            +get_connection()
        }

        class MSSQLBackend {
            +name = "mssql"
            +requires_provisioning = true
            +get_connection() connexion
        }

        class MSSQLDialect {
            +BIGINT IDENTITY(1,1)
            +identifiants [crochets]
            +formes gardées IF OBJECT_ID
        }

        class pyodbc {
            <<pilote ODBC>>
        }

        MSSQLBackend ..|> DatabaseBackend : implémente
        MSSQLBackend --> pyodbc : connexion
        MSSQLBackend --> MSSQLDialect : dialecte
    ```

    À retenir :

    - le backend enveloppe `pyodbc` (curseur lignes-dict via `description`, `lastrowid` via `SCOPE_IDENTITY()`) ;
    - les paramètres `?` de Forge sont utilisés tels quels ;
    - le dialecte gère `IDENTITY`, les crochets et les formes gardées ;
    - `pyodbc` est importé paresseusement et requiert un pilote ODBC système.

    ### 5.2 Diagramme de séquence

    Le diagramme de séquence montre une requête runtime via pyodbc.

    ```mermaid
    sequenceDiagram
        participant Core as core.database
        participant Backend as forge-mvc-mssql
        participant ODBC as pyodbc + pilote
        participant Server as SQL Server

        Core->>Backend: execute("... WHERE id = ?", (42,))
        Backend->>ODBC: execute(sql, (42,))  (? natif)
        ODBC->>Server: requête
        Server-->>ODBC: lignes
        Backend->>Backend: convertit en dicts (cursor.description)
        Backend-->>Core: lignes (dict)
    ```

    À retenir :

    - aucune traduction de paramètres (pyodbc utilise `?`) ;
    - les lignes pyodbc sont converties en dicts via `cursor.description` ;
    - `lastrowid` est obtenu via `SELECT SCOPE_IDENTITY()` ;
    - un pilote ODBC doit être installé sur la machine.

??? note "7. Ce que fournit le backend"

    | Élément | Rôle |
    |---|---|
    | `MSSQLBackend` | implémente le contrat `DatabaseBackend` |
    | Adaptateur `pyodbc` | curseur lignes-dict, `lastrowid` via `SCOPE_IDENTITY()` |
    | `MSSQLDialect` | `BIGINT IDENTITY(1,1)`, crochets, `CREATE INDEX` gardés, `INFORMATION_SCHEMA` |
    | Entry point | `forge_mvc.db_backend = mssql` |

??? note "8. Contextes d'utilisation"

    | Besoin | Élément |
    |---|---|
    | Utiliser SQL Server | installer `forge-mvc-mssql` + pilote ODBC + serveur |
    | Forcer ce backend | `DB_BACKEND=mssql` |
    | Choisir le pilote ODBC | `DB_ODBC_DRIVER` |
    | Provisionner base + comptes | `forge db:init` (avec `DB_ADMIN_*`) |
    | Appliquer le schéma | `forge db:apply` |
    | Faire évoluer le schéma | `forge migration:*` |

??? note "9. Exemple d'utilisation"

    ```bash
    # 1. Installer le backend + pilote ODBC, configurer env/dev
    pip install --pre forge-mvc-mssql
    forge db:config

    # 2. Provisionner la base et les comptes (DB_ADMIN_* existant)
    forge db:init --run

    # 3. Appliquer le schéma
    forge db:apply
    ```

    Le code applicatif utilise `core.database.db`, comme avec tout autre backend.

    !!! tip "Aide-mémoire"
        - `db:init` affiche le SQL de provisioning ; `--run` l'exécute avec `DB_ADMIN_*` ;
        - `db:apply` / `migration:*` suivent le flux du cœur ;
        - `?` est natif (pyodbc), pas de traduction.

??? note "10. Statut, ODBC et dialecte"

    Le backend est au **niveau plein** (ADR-084, révision du 2026-07-19).

    L'intégration est validée en CI contre un vrai SQL Server 2022 (pilote ODBC Driver 18) : couche BDD (insertion, lecture, `rowcount`, anti-injection, transactions, clés étrangères) et runner de migrations (application, idempotence, dry-run, refus `CHANGED`, rollback réel, introspection `INFORMATION_SCHEMA`).

    L'identité d'insertion (`lastrowid` de `db.insert`) est fiable : `SCOPE_IDENTITY()` est exécuté dans le même lot que l'INSERT.

    L'escape hatch `DB_APP_PRIVILEGES` au-delà du DML (SELECT, INSERT, UPDATE, DELETE) reste propre à MariaDB : `db:init` le refuse explicitement sur SQL Server.

    SQL Server n'a pas `IF NOT EXISTS` pour les tables : le dialecte émet des **formes gardées** (`IF OBJECT_ID(...) IS NULL`).

    !!! warning "Pilote ODBC requis"
        `pyodbc` a besoin d'un pilote ODBC système (par défaut « ODBC Driver 18 for SQL Server »), surchargeable via `DB_ODBC_DRIVER`.

        Sans pilote, la connexion échoue.

    !!! note "Dialecte SQL Server"
        `BIGINT IDENTITY(1,1)` pour l'identité, identifiants entre crochets `[...]`, `CREATE INDEX` gardés, introspection via `INFORMATION_SCHEMA`.

    !!! note "Indépendance du cœur"
        Le cœur de Forge ne dépend pas de `forge-mvc-mssql` : il le découvre par entry point (ADR-054).

## Voir aussi

- [Welcome-SQL Server](welcome/debutant/mssql-welcome.md) : apprendre le backend pas à pas.
- [ADR-054](https://forgemvc.com/docs/forge/adr/054-database-backend-optins/) : cœur agnostique BDD.
