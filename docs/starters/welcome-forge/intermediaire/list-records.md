# Lister des enregistrements

Objectif : lire **plusieurs** lignes en base et les afficher dans une vue.

**Ce que vous allez apprendre :** au palier débutant *Première base SQL*, vous
avez lu **une** ligne avec `fetch_one`. Ici vous lisez **toute la table** avec
`core.database.db.fetch_all`, qui retourne une **liste** de dictionnaires, puis
vous l'itérez dans la vue avec une boucle Jinja `{% for %}`.

Premier palier du **niveau intermédiaire** de la
[progression officielle des starters](../../index.md#progression-recommandee),
après [Écrire en base](../debutant/first-sql-write.md) (dernier palier du niveau
débutant).

## Ce que ce starter montre

- une route `GET /list-records` qui lit **plusieurs** lignes ;
- `core.database.db.fetch_all` (liste de lignes) au lieu de `fetch_one` ;
- une vue HTML qui **boucle** sur les lignes avec `{% for m in messages %}`.

Aucune écriture en base. Aucun formulaire. Aucun CRUD complet. Aucune entité JSON.

## Classes Forge utilisées

| Classe | Rôle dans ce starter | Référence |
|--------|----------------------|-----------|
| `Request` | Reçue par la méthode du contrôleur. | [Request](../../../reference/http.md#3-request-reference) |
| `Response` | Produite ici via `render(...)`. | [Response](../../../reference/http.md#4-response-reference) |
| `BaseController` | Fournit `render(...)` pour la vue. | [BaseController](../../../reference/api.md#coremvccontroller) |
| `core.database.db.fetch_all` | Lit **plusieurs** lignes (liste de dicts). | [Migrations SQL](../../../features/migrations.md) |

## Tester

La table neutre `first_sql_messages` est créée et peuplée par la migration
livrée avec ce starter :

```bash
forge migration:apply
forge run
```

Ouvrez `https://localhost:8000/list-records` → la liste des messages s'affiche.

## Les routes

```python
# mvc/routes.py
from mvc.controllers.list_records_controller import ListRecordsController

with router.group("", public=True) as pub:
    pub.add("GET", "/list-records", ListRecordsController.index, name="list_records_index")
```

## Le contrôleur

```python
# mvc/controllers/list_records_controller.py
from core.database.db import fetch_all
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


SELECT_ALL_MESSAGES = "SELECT id, content FROM first_sql_messages ORDER BY id"


class ListRecordsController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        messages = fetch_all(SELECT_ALL_MESSAGES)
        return BaseController.render(
            "list_records/index.html",
            context={"messages": messages},
            request=request,
        )
```

### Comprendre ce code

- `fetch_all(SELECT_ALL_MESSAGES)` exécute le `SELECT` et retourne une **liste**
  de dictionnaires (une entrée par ligne), là où `fetch_one` ne renvoyait qu'un
  seul dictionnaire (ou `None`).
- Le SQL reste une **constante de module** lisible et paramétrable (principe
  « SQL visible »).
- La liste est passée à la vue dans le **contexte** (`{"messages": messages}`).

## La vue

```html
<!-- mvc/views/list_records/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Lister des enregistrements — Forge</title>
</head>
<body>
  <h1>Messages</h1>

  {% if messages %}
  <ul>
    {% for m in messages %}
    <li>#{{ m.id }} — {{ m.content }}</li>
    {% endfor %}
  </ul>
  {% else %}
  <p>Aucun message en base.</p>
  {% endif %}
</body>
</html>
```

### Comprendre ce code

- `{% for m in messages %}` itère la liste reçue du contrôleur ; chaque `m` est
  un dictionnaire dont on lit `m.id` et `m.content`.
- `{% if messages %}` gère proprement le cas d'une table vide.
- Pas encore de gabarit partagé (`{% extends %}`) : c'est le palier *Héritage de
  gabarit* qui l'introduira ; ici la page reste un document HTML complet.

## À retenir

- `fetch_all` renvoie **une liste** ; `fetch_one` renvoie **une ligne**.
- Une vue affiche une collection avec `{% for %}` ; pensez au cas **vide**.
- Le SQL reste visible et paramétré, jamais concaténé.

## Après ce starter

C'est, pour l'instant, le dernier palier disponible du **niveau intermédiaire**.
Faites le point dans le bilan du niveau.

[Bilan du niveau intermédiaire](bilan.md)
