# Première base SQL

Objectif : lire une donnée en base de données avec du SQL visible, sans ORM.

**Ce que vous allez apprendre :** créer une table via une migration, puis la
lire avec `fetch_one(...)` depuis un nouveau contrôleur dédié au domaine des
messages.

## Là où nous en sommes

`WelcomeController` couvre les neuf premiers paliers (HTTP pur), et
`mvc/routes.py` déclare ses treize routes jusqu'à `/server-validation`. Nous
abordons un nouveau domaine, la base de données : selon le principe
« nouveau domaine = nouveau contrôleur », nous créons un second contrôleur,
`MessageController`.

## L'ajout

### La migration

Créez la migration `mvc/migrations/<timestamp>_create_first_sql_messages.sql`
(remplacez `<timestamp>` par l'horodatage généré par Forge) :

```sql
CREATE TABLE IF NOT EXISTS first_sql_messages (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    content VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO first_sql_messages (content)
SELECT 'Bonjour SQL'
WHERE NOT EXISTS (SELECT 1 FROM first_sql_messages);
```

L'`INSERT` est idempotent : il n'ajoute le message « Bonjour SQL » que si la
table est vide, donc rejouer la migration ne crée pas de doublon. Appliquez
la migration avec `forge migration:apply` avant de tester `/first-sql`.

### Le nouveau contrôleur

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

L'import `insert` et la constante `INSERT_MESSAGE` serviront au palier
suivant ; ils sont déjà en place pour ne plus toucher aux imports.

Puis ajoutez l'import du contrôleur et la route `/first-sql` dans
`mvc/routes.py`.

## Votre mvc/routes.py à ce stade

```python
# mvc/routes.py
from core.http.router import Router
from mvc.controllers.home_controller import HomeController
from mvc.controllers.welcome_controller import WelcomeController
from mvc.controllers.message_controller import MessageController

router = Router()

with router.group("", public=True) as pub:
    pub.add("GET", "/", HomeController.index, name="home_index")
    pub.add("GET",  "/welcome", WelcomeController.index, name="welcome_index")
    pub.add("GET",  "/query-params", WelcomeController.query_params_index, name="query_params_index")
    pub.add("GET",  "/query-params/hello", WelcomeController.hello, name="query_params_hello")
    pub.add("GET",  "/first-html-view", WelcomeController.html_view, name="first_html_view_index")
    pub.add("GET",  "/dynamic-route/articles/{id}", WelcomeController.show_article, name="dynamic_route_article_show")
    pub.add("GET",  "/request-debug", WelcomeController.debug, name="request_debug_index")
    pub.add("GET",  "/json-response", WelcomeController.json_demo, name="json_response_index")
    pub.add("GET",  "/csrf", WelcomeController.csrf_demo, name="csrf_index")
    pub.add("GET",  "/form-post", WelcomeController.form, name="form_post_index")
    pub.add("POST", "/form-post", WelcomeController.form_submit, name="form_post_submit")
    pub.add("GET",  "/server-validation", WelcomeController.validate, name="server_validation_index")
    pub.add("POST", "/server-validation", WelcomeController.validate_submit, name="server_validation_submit")
    pub.add("GET",  "/first-sql", MessageController.index, name="first_sql_index")
```

## Comprendre ce code

- Le SQL reste visible : la requête `SELECT content FROM first_sql_messages
  ORDER BY id LIMIT 1` est lisible telle quelle, sans couche d'abstraction.
- `fetch_one(...)` renvoie une seule ligne sous forme de dictionnaire, ou
  `None` si la table est vide ; d'où le repli `(aucun message)`.
- Un nouveau domaine justifie un nouveau contrôleur : `MessageController` ne
  mélange pas la logique base de données avec les démonstrations HTTP de
  `WelcomeController`.

## Tester dans le navigateur

| URL | Résultat |
|---|---|
| `https://localhost:8000/first-sql` | `Message depuis la base : Bonjour SQL` |

## À retenir

- Une table se crée par une migration appliquée avec `forge migration:apply`.
- `fetch_one(...)` lit une ligne avec du SQL écrit à la main.
- Un nouveau domaine se loge dans son propre contrôleur.

Au palier suivant, nous écrivons à notre tour une ligne dans cette table.

[Continuer avec Écrire en base](first-sql-write.md)
