# Relations entre tables

Objectif : lire des données **réparties sur deux tables liées**, combinées par
une jointure SQL.

**Ce que vous allez apprendre :** relier deux tables par une **clé étrangère**
(`articles.category_id` → `categories.id`) et les lire ensemble avec un `JOIN`
SQL **visible**. Une vraie application relie ses données ; Forge ne masque pas
ces relations derrière un ORM — le SQL reste sous vos yeux.

Premier palier du **niveau avancé** de la
[progression officielle des starters](../../index.md#progression-recommandee),
après le [niveau intermédiaire](../intermediaire/bilan.md).

## Ce que ce starter montre

- deux tables liées par une **clé étrangère** (`FOREIGN KEY`) ;
- une lecture par **jointure** `SELECT … FROM articles JOIN categories …` ;
- l'affichage de chaque article **avec le nom de sa catégorie** ;
- aucune écriture, aucun ORM — le SQL est explicite.

Les deux tables sont créées et peuplées par la migration.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `core.database.db.fetch_all` | Exécuter le `SELECT … JOIN …` et renvoyer les lignes. | [Base de données](../../../reference/api.md#coredatabase) |
| `BaseController.render` | Rendre la liste jointe. | [BaseController](../../../reference/api.md#coremvccontroller) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/relations` : chaque article s'affiche avec, entre
parenthèses, le nom de sa catégorie.

## La migration

```sql
-- mvc/migrations/20260601140000_create_relations_tables.sql
CREATE TABLE IF NOT EXISTS categories (
    id   BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(100)    NOT NULL,
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
```

### Comprendre ce code

- `categories` est la table **parente**, `articles` la table **enfant**.
- La contrainte `FOREIGN KEY (category_id) REFERENCES categories (id)` garantit
  qu'un article pointe toujours vers une catégorie qui existe.
- La table parente est créée **avant** l'enfant : la contrainte l'exige.

## Le contrôleur

```python
# mvc/controllers/relations_controller.py
from core.database.db import fetch_all


SELECT_ARTICLES_WITH_CATEGORY = (
    "SELECT a.id, a.title, c.name AS category "
    "FROM articles a "
    "JOIN categories c ON c.id = a.category_id "
    "ORDER BY a.id"
)


class RelationsController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        articles = fetch_all(SELECT_ARTICLES_WITH_CATEGORY)
        return BaseController.render(
            "relations/index.html",
            context={"articles": articles},
            request=request,
        )
```

### Comprendre ce code

- Le `JOIN … ON c.id = a.category_id` **relie** chaque article à sa catégorie.
- `c.name AS category` ramène le nom de la catégorie dans chaque ligne renvoyée :
  pas besoin d'une seconde requête.
- Le SQL reste **lisible et explicite** — c'est tout l'esprit de Forge.

## La vue

```html
<!-- mvc/views/relations/index.html -->
{% if articles %}
<ul>
  {% for a in articles %}
  <li>#{{ a.id }} — {{ a.title }} <em>({{ a.category }})</em></li>
  {% endfor %}
</ul>
{% else %}
<p>Aucun article.</p>
{% endif %}
```

### Comprendre ce code

- Chaque ligne expose `a.title` **et** `a.category` : les deux tables sont déjà
  jointes côté SQL.

## À retenir

- Une **clé étrangère** relie deux tables et garantit la cohérence.
- Un `JOIN` lit les données reliées **en une seule requête**, SQL visible.
- Forge n'a pas d'ORM : vous écrivez le `SELECT … JOIN …` vous-même.

## Après ce starter

Premier palier du niveau avancé terminé. Faites le point dans le bilan du
niveau.

[Bilan du niveau avancé](bilan.md)
