# Relations entre tables

Objectif : lire des données **réparties sur deux tables liées**, combinées par
une jointure SQL.

**Ce que vous allez apprendre :** relier deux tables par une **clé étrangère**
(`articles.category_id` vers `categories.id`) et les lire ensemble avec un `JOIN`
SQL **visible**. Forge ne masque pas ces relations derrière un ORM : le SQL reste
sous vos yeux.

!!! info "Un mini-projet autonome"
    Le niveau avancé est un **tutoriel continu** : vous construisez à la main un
    seul petit projet, le « Catalogue d'articles », qui grandit palier après
    palier. C'est un projet **indépendant** des niveaux précédents. Vous écrivez
    le code vous-même, à la main, sans génération automatique.

## Démarrer le niveau

Créez un projet neuf et placez-vous dedans :

```bash
forge new catalogue
cd catalogue
```

Une base MariaDB est nécessaire dès ce palier. Voir
[Préparer MariaDB](../../../install/mariadb.md) si ce n'est pas déjà fait.

## L'ajout

### La migration

Créez la migration `mvc/migrations/<timestamp>_create_catalogue.sql`. La table
parente (`categories`) est créée **avant** l'enfant (`articles`) : la contrainte
l'exige.

```sql
CREATE TABLE IF NOT EXISTS categories (
    id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name          VARCHAR(100)    NOT NULL,
    article_count INT             NOT NULL DEFAULT 0,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS articles (
    id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    title       VARCHAR(255)    NOT NULL,
    category_id BIGINT UNSIGNED NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_articles_category
        FOREIGN KEY (category_id) REFERENCES categories (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO categories (name, article_count)
SELECT seed.name, seed.article_count FROM (
    SELECT 'Tutoriels' AS name, 1 AS article_count
    UNION ALL SELECT 'Références', 0
) AS seed
WHERE NOT EXISTS (SELECT 1 FROM categories);

INSERT INTO articles (title, category_id)
SELECT 'Bien démarrer avec Forge', c.id FROM categories c
WHERE c.name = 'Tutoriels'
AND NOT EXISTS (SELECT 1 FROM articles);
```

Appliquez la migration avec `forge migration:apply` avant de tester.

### Le contrôleur

Créez le fichier `mvc/controllers/article_controller.py` :

```python
# mvc/controllers/article_controller.py
from core.database.db import fetch_all
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

SELECT_ARTICLES_WITH_CATEGORY = (
    "SELECT a.id, a.title, c.name AS category "
    "FROM articles a "
    "JOIN categories c ON c.id = a.category_id "
    "ORDER BY a.id"
)


class ArticleController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        articles = fetch_all(SELECT_ARTICLES_WITH_CATEGORY)
        return BaseController.render(
            "article/index.html",
            request=request,
            context={"articles": articles},
        )
```

Créez la vue `mvc/views/article/index.html` :

```html
<!-- mvc/views/article/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="utf-8">
    <title>Catalogue d'articles</title>
</head>
<body>
    <h1>Articles</h1>

    {% if articles %}
    <ul>
        {% for a in articles %}
        <li>#{{ a.id }} : {{ a.title }} <em>({{ a.category }})</em></li>
        {% endfor %}
    </ul>
    {% else %}
    <p>Aucun article.</p>
    {% endif %}
</body>
</html>
```

Puis ajoutez l'import du contrôleur et la route `/articles` dans `mvc/routes.py`.

## Votre mvc/routes.py à ce stade

```python
# mvc/routes.py
from core.http.router import Router
from mvc.controllers.home_controller import HomeController
from mvc.controllers.article_controller import ArticleController

router = Router()

with router.group("", public=True) as pub:
    pub.add("GET", "/", HomeController.index, name="home_index")
    pub.add("GET", "/articles", ArticleController.index, name="articles_index")
```

## Comprendre ce code

- La contrainte `FOREIGN KEY (category_id) REFERENCES categories (id)` garantit
  qu'un article pointe toujours vers une catégorie qui existe.
- Le `JOIN … ON c.id = a.category_id` **relie** chaque article à sa catégorie ;
  `c.name AS category` ramène le nom dans chaque ligne, sans seconde requête.
- Le SQL reste **lisible et explicite** : c'est tout l'esprit de Forge, sans ORM.

## Tester dans le navigateur

| URL | Résultat |
|---|---|
| `https://localhost:8000/articles` | l'article de départ avec sa catégorie entre parenthèses |

## À retenir

- Une **clé étrangère** relie deux tables et garantit la cohérence.
- Un `JOIN` lit les données reliées **en une seule requête**, SQL visible.
- La table parente se crée avant l'enfant.

Au palier suivant, nous créons un article par une écriture **transactionnelle**.

[Continuer avec Écritures transactionnelles](db-transaction.md)
