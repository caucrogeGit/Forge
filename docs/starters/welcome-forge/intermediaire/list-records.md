# Lister des enregistrements

Objectif : lire **plusieurs** lignes en base et les afficher dans une vue.

**Ce que vous allez apprendre :** lire toute une table avec
`core.database.db.fetch_all`, qui retourne une **liste** de dictionnaires, puis
l'itérer dans la vue avec une boucle Jinja `{% for %}`.

!!! info "Un mini-projet autonome"
    Le niveau intermédiaire est un **tutoriel continu** : vous construisez à la
    main un seul petit projet, le « Carnet de notes », qui grandit palier après
    palier. C'est un projet **indépendant** du niveau débutant, pas besoin de
    l'avoir suivi. Comme au débutant, vous écrivez le code vous-même, à la main,
    sans génération automatique.

## Démarrer le niveau

Créez un projet neuf et placez-vous dedans :

```bash
forge new carnet-de-notes
cd carnet-de-notes
```

Une base MariaDB est nécessaire dès ce palier. Voir
[Préparer MariaDB](../../../install/mariadb.md) si ce n'est pas déjà fait.

## L'ajout

### La migration

Créez la migration `mvc/migrations/<timestamp>_create_notes.sql` (remplacez
`<timestamp>` par l'horodatage généré par Forge) :

```sql
CREATE TABLE IF NOT EXISTS notes (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    content VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO notes (content)
SELECT seed.content FROM (
    SELECT 'Première note' AS content
    UNION ALL SELECT 'Deuxième note'
    UNION ALL SELECT 'Troisième note'
) AS seed
WHERE NOT EXISTS (SELECT 1 FROM notes);
```

L'`INSERT` est idempotent : il ne pose les notes de départ que si la table est
vide, donc rejouer la migration ne crée pas de doublon. Appliquez la migration
avec `forge migration:apply` avant de tester.

### Le contrôleur

Créez le fichier `mvc/controllers/note_controller.py` :

```python
# mvc/controllers/note_controller.py
from core.database.db import fetch_all
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

SELECT_ALL = "SELECT id, content FROM notes ORDER BY id"


class NoteController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        notes = fetch_all(SELECT_ALL)
        return BaseController.render(
            "note/index.html",
            request=request,
            context={"notes": notes},
        )
```

Créez la vue `mvc/views/note/index.html` :

```html
<!-- mvc/views/note/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="utf-8">
    <title>Carnet de notes</title>
</head>
<body>
    <h1>Mes notes</h1>

    {% if notes %}
    <ul>
        {% for note in notes %}
        <li>#{{ note.id }} : {{ note.content }}</li>
        {% endfor %}
    </ul>
    {% else %}
    <p>Aucune note en base.</p>
    {% endif %}
</body>
</html>
```

Puis ajoutez l'import du contrôleur et la route `/notes` dans `mvc/routes.py`.

## Votre mvc/routes.py à ce stade

```python
# mvc/routes.py
from core.http.router import Router
from mvc.controllers.home_controller import HomeController
from mvc.controllers.note_controller import NoteController

router = Router()

with router.group("", public=True) as pub:
    pub.add("GET", "/", HomeController.index, name="home_index")
    pub.add("GET", "/notes", NoteController.index, name="notes_index")
```

## Comprendre ce code

- `fetch_all(SELECT_ALL)` exécute le `SELECT` et retourne une **liste** de
  dictionnaires, une entrée par ligne (là où `fetch_one` ne renvoie qu'une
  ligne ou `None`).
- Le SQL reste visible : `SELECT id, content FROM notes ORDER BY id` se lit tel
  quel, sans ORM, comme une **constante de module**.
- La vue **boucle** sur la liste avec `{% for note in notes %}` et gère le cas
  d'une table vide avec `{% if notes %}`.

## Tester dans le navigateur

| URL | Résultat |
|---|---|
| `https://localhost:8000/notes` | la liste des trois notes de départ |

## À retenir

- `fetch_all` renvoie **une liste** de lignes ; `fetch_one` renvoie **une** ligne.
- Une table se crée par une migration appliquée avec `forge migration:apply`.
- Une vue affiche une collection avec `{% for %}` ; pensez au cas **vide**.

Au palier suivant, nous factorisons l'enveloppe HTML de cette page dans un
gabarit partagé.

[Continuer avec Héritage de gabarit](layout-template.md)
