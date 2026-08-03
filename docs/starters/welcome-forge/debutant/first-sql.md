# Première base SQL

**Objectif**{ .intro-label } : lire une donnée en base de données avec du SQL visible, sans ORM.

**Ce que vous allez apprendre :**{ .intro-label } créer une table via une migration, puis la lire avec `fetch_one(...)` depuis un nouveau contrôleur dédié au domaine des messages.

`WelcomeController` couvre tous les paliers HTTP précédents, et `mvc/routes/__init__.py` déclare ses routes jusqu'à `/welcome/validate`.

Nous abordons un nouveau domaine, la base de données : selon le principe « nouveau domaine = nouveau contrôleur », nous créons un second contrôleur, `MessageController`.

??? note "Documentations"
    Pour bien comprendre ce palier :

    | Document | Ce qu'il apporte |
    |---|---|
    | [Migrations SQL](../../../features/migrations.md) | comment créer une table et appliquer une migration |

??? note "Migrations"
    Avant la première migration, initialisez la base de données (une seule fois pour ce mini-projet) :

    ```bash
    forge db:init
    ```

    `forge db:init` prépare la base et la table `forge_migrations`, qui enregistre les migrations déjà appliquées.
    Sur un backend **sans serveur** comme SQLite, il crée directement le fichier.
    Sur un backend **serveur**, il affiche le SQL de provisioning, base et comptes, à exécuter dans une session d'administration, ou l'exécute avec `--run` ([ADR-067](../../../adr/067-db-init-provisioning-sql.md)).
    Sans cette étape, `forge migration:apply` n'a ni base ni table de suivi et échoue.

    Générez ensuite le fichier de migration ; Forge l'horodate pour vous :

    ```bash
    forge migration:make create_first_sql_messages
    ```

    Forge crée `mvc/migrations/<timestamp>_create_first_sql_messages.sql`.
    Ouvrez ce fichier et placez-y le SQL suivant :

    ```sql
    CREATE TABLE IF NOT EXISTS first_sql_messages (
        id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
        content VARCHAR(255) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

    INSERT INTO first_sql_messages (content)
    SELECT 'Bonjour SQL'
    WHERE NOT EXISTS (SELECT 1 FROM first_sql_messages);
    ```

    L'`INSERT` est idempotent : il n'ajoute le message « Bonjour SQL » que si la table est vide, donc rejouer la migration ne crée pas de doublon.
    Appliquez enfin la migration avec `forge migration:apply` avant de tester `/message`.

??? note "Contrôleurs"
    Créez le fichier `mvc/controllers/message_controller.py` :

    ```python
    # mvc/controllers/message_controller.py
    from core.database.db import fetch_one, insert
    from core.http.request import Request
    from core.http.response import Response
    from core.mvc.controller.base_controller import BaseController

    SELECT_FIRST_MESSAGE = "SELECT content FROM first_sql_messages ORDER BY id LIMIT 1"
    INSERT_MESSAGE = "INSERT INTO first_sql_messages (content) VALUES (?)"


    class MessageController(BaseController):

        @staticmethod
        def index(request: Request) -> Response:
            row = fetch_one(SELECT_FIRST_MESSAGE)
            message = row["content"] if row else "(aucun message)"
            return Response.text(f"Message depuis la base : {message}")
    ```

    | Élément | Rôle |
    |---|---|
    | `SELECT content FROM first_sql_messages ...` | Le SQL reste **visible**, lisible tel quel, sans couche d'abstraction. |
    | `fetch_one(...)` | Renvoie une seule ligne sous forme de dictionnaire, ou `None` si la table est vide ; d'où le repli `(aucun message)`. |
    | `MessageController` | Un nouveau domaine justifie un nouveau contrôleur : il ne mélange pas la logique base de données avec les démonstrations HTTP de `WelcomeController`. |

    L'import `insert` et la constante `INSERT_MESSAGE` serviront au palier suivant ; ils sont déjà en place pour ne plus toucher aux imports.

??? note "Routes"
    Ajoutez l'import du contrôleur et la route `/message` dans `mvc/routes/__init__.py` :

    ```python
    # mvc/routes/__init__.py
    from core.http.router import Router
    from mvc.controllers.home_controller import HomeController
    from mvc.controllers.welcome_controller import WelcomeController
    from mvc.controllers.message_controller import MessageController

    router = Router()

    with router.group("", public=True) as public:
        public.add("GET", "/", HomeController.index, name="home-index")
        public.add("GET",  "/welcome", WelcomeController.index, name="welcome-index")
        public.add("GET",  "/welcome/hello", WelcomeController.hello, name="welcome-hello")
        public.add("GET",  "/welcome/html", WelcomeController.html, name="welcome-html")
        public.add("GET",  "/welcome/article/{id}", WelcomeController.article, name="welcome-article")
        public.add("GET",  "/welcome/debug", WelcomeController.debug, name="welcome-debug")
        public.add("GET",  "/welcome/json", WelcomeController.json_demo, name="welcome-json")
        public.add("GET",  "/welcome/csrf", WelcomeController.csrf, name="welcome-csrf")
        public.add("GET",  "/welcome/form", WelcomeController.form, name="welcome-form")
        public.add("POST", "/welcome/form-submit", WelcomeController.form_submit, name="welcome-form_submit")
        public.add("GET",  "/welcome/validate", WelcomeController.validate, name="welcome-validate")
        public.add("POST", "/welcome/validate-submit", WelcomeController.validate_submit, name="welcome-validate_submit")
        public.add("GET",  "/message", MessageController.index, name="message-index")
    ```

??? note "Tests"
    | URL | Résultat |
    |---|---|
    | `https://localhost:8000/message` | `Message depuis la base : Bonjour SQL` |

??? note "À retenir"
    - La base s'initialise une fois avec `forge db:init`, puis chaque table naît d'une migration générée (`forge migration:make`), éditée, et appliquée (`forge migration:apply`).
    - `fetch_one(...)` lit une ligne avec du SQL écrit à la main.
    - Un nouveau domaine se loge dans son propre contrôleur.

Au palier suivant, nous écrivons à notre tour une ligne dans cette table.

[Continuer avec Écrire en base](first-sql-write.md)
