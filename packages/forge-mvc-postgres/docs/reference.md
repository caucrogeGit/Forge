# Le backend PostgreSQL dans Forge (forge-mvc-postgres)

Ce document explique ce que fait l'opt-in `forge-mvc-postgres`, ce qu'il expose, et comment on s'en sert.

`forge-mvc-postgres` est un **backend de base de données** pour Forge, au-dessus de `psycopg` (v3), pour faire fonctionner la couche BDD du cœur sur un serveur PostgreSQL.

Le cœur de Forge est agnostique BDD (ADR-054) : il découvre le backend installé par un entry point et n'en utilise qu'un seul par projet.

!!! warning "Statut Alpha"
    La logique de dialecte et la traduction des paramètres sont **testées unitairement**, mais l'**intégration serveur** et le **provisioning par `db:init`** restent à valider/câbler.

    À ce stade, créez la base et le rôle à la main, puis utilisez `db:apply` / `migration:*`.

??? note "1. Rôle du module"

    Le cœur génère le SQL et pilote les commandes BDD ; un backend les fait parler à un vrai serveur.

    `forge-mvc-postgres` fournit ce backend pour PostgreSQL : un adaptateur de connexion `psycopg` conforme aux attentes du cœur, et un dialecte SQL PostgreSQL.

    Particularité technique : Forge génère des paramètres `?` ; l'adaptateur les **traduit** en `%s` (format psycopg) à l'exécution.

??? note "2. Installation et désinstallation"

    !!! warning "Backend Alpha"
        PostgreSQL est un backend **Alpha** : le dialecte et l'adaptateur sont testés, mais l'intégration sur un vrai serveur reste à valider.
        À réserver aux essais, pas encore à la production.

    PostgreSQL est **client-serveur** : un serveur doit être joignable.
    Le pilote est `psycopg` (v3).

    === "Depuis PyPI (stable)"

        La dernière version publiée :

        ```bash
        pip install --pre forge-mvc-postgres
        ```

    === "Depuis Git (avant-garde)"

        Cœur puis backend depuis git, dans le venv du projet, à la même version (le backend trouve le cœur git déjà en place, sans version publiée sur PyPI) :

        ```bash
        source .venv/bin/activate
        pip install "git+https://github.com/caucrogeGit/Forge.git@main"
        pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-postgres"
        ```

        !!! warning "Erreur « externally-managed-environment » ?"

            Lancées hors d'un venv, ces commandes visent le Python **système** (Debian 12+, Ubuntu 23.04+), protégé par PEP 668.
            La cible correcte est le venv du projet (`source .venv/bin/activate`), jamais le Python système.


    Le cœur découvre le backend par son entry point `forge_mvc.db_backend` : aucune commande d'activation n'est nécessaire.

    `forge db:config` amorce les variables du backend dans `env/example`, `env/dev` et `env/prod` (write-if-missing, sans secret ; ADR-064) :

    ```bash
    forge db:config
    ```

    Renseignez ensuite les valeurs dans `env/dev` (et `env/prod`) :

    ```env
    DB_NAME=mon_projet
    DB_HOST=127.0.0.1
    DB_PORT=5432
    DB_ADMIN_LOGIN=postgres
    DB_ADMIN_PWD=...
    DB_APP_LOGIN=mon_projet
    DB_APP_PWD=...
    ```

    `forge doctor` confirme le backend résolu (`postgres`) ; si plusieurs backends sont installés, fixez `DB_BACKEND=postgres`.

    La progression guidée, pas à pas : [Installation de forge-mvc-postgres](welcome/debutant/postgres-welcome.md).

    ### Désinstallation

    Retirez d'abord la configuration des fichiers d'environnement, puis le paquet :

    ```bash
    forge db:config --remove
    pip uninstall forge-mvc-postgres
    ```

    `db:config --remove` retire les clés `DB_*` posées par `db:config` des trois fichiers d'environnement (les valeurs renseignées sont perdues ; ADR-064).
    Un backend n'a pas de commande `disable` : découvert par entry point (ADR-054), retirer le paquet suffit ensuite à ce que le cœur ne le voie plus.
    Si besoin, supprimez aussi la base et le compte créés par `db:init`.

??? note "3. Commandes"

    Ce backend n'ajoute aucune commande : il est découvert par l'entry point `forge_mvc.db_backend` et fournit, au runtime, un dialecte SQL et un adaptateur de connexion.
    Les commandes de base de données que vous utilisez avec lui sont fournies par le moteur d'entités (`forge-mvc-entities`) :

    | Commande | Rôle | Exemple |
    |---|---|---|
    | `db:config` | Amorce les variables du backend dans `env/*` (write-if-missing). | `forge db:config` |
    | `db:init` | Affiche le SQL de provisioning ; `--run` l'exécute. | `forge db:init --run` |
    | `db:apply` | Applique le SQL des entités à la base. | `forge db:apply` |
    | `migration:make` | Génère une migration depuis l'écart de schéma. | `forge migration:make` |
    | `migration:apply` | Applique les migrations en attente. | `forge migration:apply` |

??? note "4. Vue d'ensemble rapide"

    | Élément | Valeur |
    |---|---|
    | Paquet | `forge-mvc-postgres` |
    | Module | `forge_mvc_postgres` |
    | Catégorie | Bases de données (ADR-055) |
    | Statut | **Alpha** (dialecte testé, intégration à valider) |
    | Couche | backend BDD opt-in **exclusif** (un seul par projet) |
    | Dépend de | `forge-mvc`, `psycopg` (v3), un serveur PostgreSQL |
    | Découverte | entry point `forge_mvc.db_backend` nommé `postgres` |
    | Sélection | automatique si seul installé ; sinon `DB_BACKEND=postgres` |
    | Paramètres | `?` traduits en `%s` à l'exécution |
    | Identité | `BIGSERIAL` |
    | Provisioning CLI | **pas encore câblé** : création base + rôle manuelle |
    | Décision d'architecture | ADR-054 |
    | Installation | `pip install --pre forge-mvc-postgres` |

??? note "5. Schémas UML"

    Les deux schémas suivants montrent deux vues complémentaires du backend.

    Le diagramme de classe montre l'adaptateur et le dialecte.

    Le diagramme de séquence montre la traduction des paramètres à l'exécution.

    ### 5.1 Diagramme de classe

    Le diagramme de classe montre que le backend enveloppe `psycopg` pour répondre au contrat du cœur, en traduisant les paramètres.

    ```mermaid
    classDiagram
        direction LR

        class DatabaseBackend {
            <<protocol, cœur>>
            +name
            +dialect
            +get_connection()
        }

        class PostgreSQLBackend {
            +name = "postgres"
            +requires_provisioning = true
            +get_connection() connexion
        }

        class translate {
            <<module>>
            +translate_placeholders(sql) str
        }

        class PostgreSQLDialect {
            +BIGSERIAL
            +CREATE INDEX séparés
            +guillemets doubles
        }

        class psycopg {
            <<pilote>>
        }

        PostgreSQLBackend ..|> DatabaseBackend : implémente
        PostgreSQLBackend --> psycopg : connexion
        PostgreSQLBackend --> translate : ? -> %s
        PostgreSQLBackend --> PostgreSQLDialect : dialecte
    ```

    À retenir :

    - le backend enveloppe `psycopg` (curseur lignes-dict, lastrowid via `lastval()`) ;
    - les paramètres `?` de Forge sont traduits en `%s` ;
    - le dialecte gère `BIGSERIAL` et les `CREATE INDEX` séparés ;
    - `psycopg` est importé paresseusement (l'usage du dialecte ne le requiert pas).

    ### 5.2 Diagramme de séquence

    Le diagramme de séquence montre une requête traduite à l'exécution.

    ```mermaid
    sequenceDiagram
        participant Core as core.database
        participant Backend as forge-mvc-postgres
        participant Tr as translate_placeholders
        participant PG as PostgreSQL (psycopg)

        Core->>Backend: execute("... WHERE id = ?", (42,))
        Backend->>Tr: traduit ? en %s
        Tr-->>Backend: "... WHERE id = %s"
        Backend->>PG: execute(sql traduit, (42,))
        PG-->>Backend: résultat
        Backend-->>Core: lignes (dict)
    ```

    À retenir :

    - la traduction `?` vers `%s` est transparente pour le cœur ;
    - les littéraux chaîne sont préservés à la traduction ;
    - `lastrowid` est obtenu via `SELECT lastval()` ;
    - le SQL généré reste celui de Forge, juste adapté au format psycopg.

??? note "6. Ce que fournit le backend"

    | Élément | Rôle |
    |---|---|
    | `PostgreSQLBackend` | implémente le contrat `DatabaseBackend` |
    | Adaptateur `psycopg` | curseur lignes-dict (`dict_row`), `lastrowid` via `lastval()` |
    | `translate_placeholders` | traduit `?` en `%s` |
    | `PostgreSQLDialect` | `BIGSERIAL`, `CREATE INDEX` séparés, guillemets doubles, `information_schema` |
    | Entry point | `forge_mvc.db_backend = postgres` |

??? note "7. Contextes d'utilisation"

    | Besoin | Élément |
    |---|---|
    | Utiliser PostgreSQL | installer `forge-mvc-postgres` + un serveur PostgreSQL |
    | Forcer ce backend | `DB_BACKEND=postgres` |
    | Créer base et rôle | **à la main** (Alpha) : `createdb`, `CREATE ROLE` |
    | Appliquer le schéma | `forge db:apply` (sur une base existante) |
    | Faire évoluer le schéma | `forge migration:*` |

??? note "8. Exemple d'utilisation (Alpha)"

    ```bash
    # 1. Préparer base et rôle à la main (provisioning CLI non câblé)
    createdb mon_projet
    psql -c "CREATE ROLE mon_projet LOGIN PASSWORD '...';"
    psql -c "GRANT ALL ON DATABASE mon_projet TO mon_projet;"

    # 2. Installer le backend et configurer env/dev (DB_APP_*, DB_ADMIN_*, DB_NAME)
    pip install --pre forge-mvc-postgres

    # 3. Appliquer le schéma
    forge db:apply
    ```

    Le code applicatif utilise `core.database.db`, comme avec tout autre backend.

    !!! tip "Aide-mémoire"
        En Alpha :

        - créez la base et le rôle à la main ;
        - `db:apply` / `migration:*` fonctionnent sur la base existante ;
        - `?` est traduit en `%s` automatiquement.

??? note "9. Statut Alpha et limites"

    Le dialecte (types, DDL) et la traduction des paramètres sont testés unitairement.
    L'**intégration** sur un vrai serveur reste à valider côté projet.

    Le **provisioning par `db:init`** n'est pas encore câblé pour PostgreSQL : créez la base et le rôle manuellement en attendant.

    !!! warning "À valider sur un serveur"
        Tester réellement PostgreSQL demande un serveur (local ou conteneur Docker).

        `db:init` peut signaler que le provisioning n'est pas pris en charge pour ce backend : c'est attendu (Alpha).

    !!! note "Dialecte PostgreSQL"
        `BIGSERIAL` pour l'identité, `CREATE INDEX` séparés, guillemets doubles, introspection via `information_schema`.

    !!! note "Indépendance du cœur"
        Le cœur de Forge ne dépend pas de `forge-mvc-postgres` : il le découvre par entry point (ADR-054).

## Voir aussi

- [Welcome-PostgreSQL](welcome/debutant/postgres-welcome.md) : apprendre le backend pas à pas.
- [ADR-054](https://forgemvc.com/docs/forge/adr/054-database-backend-optins/) : cœur agnostique BDD.
