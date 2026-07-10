# Les sessions persistantes dans Forge (forge-mvc-sessions-db)

`forge-mvc-sessions-db` fournit `DbSessionStore`, un store de session adossé à la base de données (table `forge_sessions`).

Le cœur de Forge, agnostique du SGBD, ne fournit qu'un store mémoire et un store fichier ; ce paquet ajoute le store BDD, partagé entre processus et persistant.

??? note "1. Rôle du module"

    Une session Forge conserve l'état d'un visiteur entre deux requêtes (jeton CSRF, utilisateur authentifié, messages flash).

    Le store par défaut du cœur (`MemorySessionStore`) garde ces données en mémoire du processus : elles disparaissent au redémarrage et ne sont pas partagées entre workers.

    `DbSessionStore` stocke chaque session dans la table `forge_sessions` de la base configurée du projet, ce qui la rend partagée entre processus et durable.

??? note "2. Installation et désinstallation"

    ### Installation

    === "Depuis PyPI (stable)"

        La dernière version publiée :

        ```bash
        pip install --pre forge-mvc-sessions-db
        ```

    === "Depuis Git (avant-garde)"

        Cœur puis opt-in depuis git, dans le venv du projet (l'opt-in trouve le cœur git déjà en place, sans version publiée sur PyPI) :

        ```bash
        source .venv/bin/activate
        pip install "git+https://github.com/caucrogeGit/Forge.git@main"
        pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-sessions-db"
        ```

        !!! warning "Erreur « externally-managed-environment » ?"

            Lancées hors d'un venv, ces commandes visent le Python **système** (Debian 12+, Ubuntu 23.04+), protégé par PEP 668.
            La cible correcte est le venv du projet (`source .venv/bin/activate`), jamais le Python système.

    Cet opt-in est une bibliothèque : on l'importe et on passe le store à `forge.configure`, il n'y a pas de câblage de routes.

    ```python
    import core.forge as forge
    from forge_mvc_sessions_db import DbSessionStore

    forge.configure(session_store=DbSessionStore(ttl=3600))
    ```

    `forge opt-in:install sessions-db` affiche la commande `pip` sans l'exécuter.

    Puis créez la table `forge_sessions`, prérequis dur du module : sans elle, la première requête de session échoue par une erreur SQL.

    Le paquet ne livre aucun script ; placez le DDL dans `mvc/models/sql/forge_sessions.sql` :

    ```sql
    CREATE TABLE IF NOT EXISTS forge_sessions (
        session_id CHAR(64)  NOT NULL,
        data       LONGTEXT  NOT NULL,
        expire_at  DATETIME  NOT NULL,
        created_at DATETIME  NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME  NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (session_id),
        INDEX idx_forge_sessions_expire_at (expire_at)
    );
    ```

    Appliquez ensuite le schéma avec `forge db:apply`.
    Le DDL ci-dessus est écrit pour MariaDB : adaptez les types au backend actif si nécessaire (par exemple `TEXT` au lieu de `LONGTEXT`, et un `CREATE INDEX` séparé sur SQLite ou PostgreSQL).

    ### Désinstallation

    ```bash
    pip uninstall forge-mvc-sessions-db
    ```

    Le cœur revient alors à son store par défaut (`MemorySessionStore`).
    `forge opt-in:remove sessions-db` affiche la commande `pip uninstall` sans l'exécuter.

??? note "3. Commandes"

    Cet opt-in n'expose aucune commande CLI : il s'utilise **par import** dans le code applicatif (voir l'API publique ci-dessous).

??? note "4. Vue d'ensemble rapide"

    | Élément | Valeur |
    |---|---|
    | Paquet | `forge-mvc-sessions-db` |
    | Module | `forge_mvc_sessions_db` |
    | Catégorie | Exploitation et outillage (ADR-055) |
    | Couche | opt-in (brique optionnelle) |
    | Dépend de | `forge-mvc` et un backend BDD (ADR-054) |
    | API publique | `DbSessionStore` |
    | Table SQL | `forge_sessions` |
    | Exécuteurs | injectés en **callables** (`fetch_one`, `execute`), défaut `core.database.db` |
    | Contrat implémenté | `core.sessions.SessionStore` |
    | Principe | SQL portable, horodatages calculés côté Python (pas de `NOW()` propriétaire) |
    | Décision d'architecture | ADR-054 (backends BDD et extraction du store de session) |
    | Installation | `pip install --pre forge-mvc-sessions-db` |

??? note "5. Schémas UML"

    Le diagramme de classe montre l'implémentation du contrat ; le diagramme de séquence montre le cycle d'une session persistée.

    ### 5.1 Diagramme de classe

    `DbSessionStore` implémente l'intégralité du contrat `SessionStore` du cœur et délègue tout son SQL à un exécuteur injecté.

    ```mermaid
    classDiagram
        class SessionStore {
            <<protocol>>
            +create(data) str
            +get(session_id) dict
            +set(session_id, data) None
            +delete(session_id) None
            +regenerate(session_id) str
            +cleanup_expired() int
        }
        class DbSessionStore {
            -_fetch_one
            -_execute
            -_ttl
            +create(data) str
            +get(session_id) dict
            +set(session_id, data) None
            +replace(session_id, data) None
            +delete(session_id) None
            +regenerate(session_id) str
            +authenticate(session_id, user_data, ttl) str
            +touch_expiry(session_id, ttl) bool
            +cleanup_expired() int
        }
        class forge_sessions {
            <<table>>
            session_id
            data
            expire_at
            created_at
            updated_at
        }
        SessionStore <|.. DbSessionStore : implémente
        DbSessionStore ..> forge_sessions : lit / écrit via core.database.db
    ```

    Ce que le diagramme révèle :

    - `DbSessionStore` respecte le contrat `SessionStore`, donc il se configure comme n'importe quel autre store ;
    - les données vivent dans la table `forge_sessions` ;
    - le store ne touche jamais la base directement : il passe par les exécuteurs `fetch_one` / `execute` (par défaut ceux de `core.database.db`).

    ### 5.2 Diagramme de séquence

    ```mermaid
    sequenceDiagram
        participant App as Application
        participant Store as DbSessionStore
        participant DB as core.database.db

        App->>Store: create()
        Store->>DB: INSERT forge_sessions (id, data, expire_at, created_at, updated_at)
        App->>Store: get(session_id)
        Store->>DB: SELECT data WHERE id = ? AND expire_at > ?
        DB-->>Store: data JSON
        Store-->>App: dict de session
        App->>Store: cleanup_expired()
        Store->>DB: DELETE WHERE expire_at < ?
    ```

    L'horodatage comparé (`?`) est calculé côté Python, jamais par une fonction SQL propriétaire.

??? note "6. API publique"

    | Nom | Signature | Rôle |
    |---|---|---|
    | `DbSessionStore` | `DbSessionStore(fetch_one=None, execute=None, ttl=SESSION_TTL)` | Store de session BDD ; exécuteurs injectables, durée de vie en secondes |
    | `create` | `create(data=None) -> str` | Crée une session (structure Forge standard) et retourne son identifiant |
    | `get` | `get(session_id) -> dict | None` | Retourne les données, ou `None` si absente, expirée ou corrompue |
    | `set` | `set(session_id, data) -> None` | Met à jour (merge) une session existante |
    | `replace` | `replace(session_id, data) -> None` | Remplace intégralement les données (sans merge) |
    | `delete` | `delete(session_id) -> None` | Supprime la session |
    | `regenerate` | `regenerate(session_id) -> str` | Nouvel identifiant, données préservées (anti-fixation) |
    | `authenticate` | `authenticate(session_id, user_data, ttl_seconds) -> str | None` | Rotation atomique vers une session authentifiée |
    | `touch_expiry` | `touch_expiry(session_id, ttl_seconds) -> bool` | Repousse l'expiration |
    | `cleanup_expired` | `cleanup_expired() -> int` | Supprime les sessions expirées, retourne le nombre supprimé |

    Le module expose aussi `set_flash` / `get_flash` pour les messages flash.

??? note "7. Contextes d'utilisation"

    | Besoin | Store recommandé |
    |---|---|
    | Développement local, tests | `MemorySessionStore` (cœur) |
    | Persistance mono-processus simple | `FileSessionStore` (cœur) |
    | Production multi-worker (Gunicorn, uWSGI) | `DbSessionStore` (cet opt-in) |
    | Déploiement multi-nœud derrière la même base | `DbSessionStore` (cet opt-in) |

??? note "8. Exemples d'utilisation"

    ### 8.1 Configurer le store

    ```python
    import core.forge as forge
    from forge_mvc_sessions_db import DbSessionStore

    forge.configure(session_store=DbSessionStore(ttl=3600))
    ```

    La table `forge_sessions` doit exister au préalable (script `mvc/models/sql/forge_sessions.sql`).

    ### 8.2 Nettoyer les sessions expirées

    ```python
    from forge_mvc_sessions_db import DbSessionStore

    store = DbSessionStore()
    supprimees = store.cleanup_expired()
    print(f"{supprimees} sessions expirées supprimées")
    ```

    À appeler depuis un cron applicatif : rien n'est planifié automatiquement.

    ### 8.3 Tester sans base réelle

    ```python
    from forge_mvc_sessions_db import DbSessionStore

    rows = {}

    def fake_fetch_one(sql, params):
        row = rows.get(params[0])
        return {"data": row} if row else None

    def fake_execute(sql, params=()):
        return 1

    store = DbSessionStore(fetch_one=fake_fetch_one, execute=fake_execute)
    ```

    Les exécuteurs `fetch_one` / `execute` sont injectables : les tests n'ont pas besoin d'une base.

??? note "9. Portabilité et exécuteurs injectés"

    Le store délègue tout son SQL aux callables `fetch_one` / `execute`, qui pointent par défaut vers `core.database.db`.

    `core.database.db` dispatche vers le backend BDD actif (`forge-mvc-mariadb`, `forge-mvc-sqlite`, etc.), en traduisant le style de paramètres (`?`) et le dialecte.

    Comme les horodatages sont calculés côté Python et passés en paramètres, aucune fonction date propriétaire n'apparaît dans le SQL : le store fonctionne à l'identique sur tous les backends (ADR-054).

    !!! warning "Création de la table"
        Le store suppose la table `forge_sessions` présente.
        Elle n'est pas créée automatiquement : appliquez le script `mvc/models/sql/forge_sessions.sql`.

## Voir aussi

- [Le store (store.py)](references/store.md) : `DbSessionStore` et ses méthodes.
- [Les sessions dans le cœur](/docs/forge/reference/sessions/) : contrat `SessionStore`, stores mémoire et fichier.
- [Welcome-Sessions BDD](welcome/debutant/sessions-db-welcome.md) : parcours d'apprentissage.
