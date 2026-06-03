# Rechercher / filtrer une liste

Objectif : filtrer une liste selon un mot-clé saisi par l'utilisateur.

**Ce que vous allez apprendre :** combiner deux notions déjà connues — les
**paramètres d'URL** (`request.param`, niveau débutant) et le **SQL visible** —
pour construire une recherche. Le mot-clé pilote une clause `WHERE content
LIKE ?` **paramétrée** (jamais concaténée).

Palier 2 du **niveau intermédiaire** de la
[progression officielle des starters](../../index.md#progression-recommandee),
après [Lister des enregistrements](list-records.md).

## Ce que ce starter montre

- une route `GET /filter-list?q=<mot>` ;
- la lecture du mot-clé avec `request.param("q", default="")` ;
- une clause SQL conditionnelle `WHERE content LIKE ?` **paramétrée** ;
- un champ de recherche (formulaire `GET`) dans la vue.

Aucune écriture en base. Aucune concaténation SQL. Aucun CRUD complet.

## Classes Forge utilisées

| Classe | Rôle dans ce starter | Référence |
|--------|----------------------|-----------|
| `Request` | Lire le mot-clé avec `request.param("q", ...)`. | [Request](../../../reference/http.md#3-request-reference) |
| `Response` | Produite via `render(...)`. | [Response](../../../reference/http.md#4-response-reference) |
| `BaseController` | Fournit `render(...)`. | [BaseController](../../../reference/api.md#coremvccontroller) |
| `core.database.db.fetch_all` | Lit la liste, filtrée ou non. | [Migrations SQL](../../../features/migrations.md) |

## Tester

```bash
forge migration:apply
forge run
```

Ouvrez `https://localhost:8000/filter-list` puis saisissez un mot dans le champ
de recherche → la liste ne montre que les messages correspondants.

## Le contrôleur

```python
# mvc/controllers/filter_list_controller.py
from core.database.db import fetch_all
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


SELECT_ALL = "SELECT id, content FROM first_sql_messages ORDER BY id"
SELECT_FILTERED = (
    "SELECT id, content FROM first_sql_messages "
    "WHERE content LIKE ? ORDER BY id"
)


class FilterListController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        query = request.param("q", default="").strip()
        if query:
            messages = fetch_all(SELECT_FILTERED, (f"%{query}%",))
        else:
            messages = fetch_all(SELECT_ALL)
        return BaseController.render(
            "filter_list/index.html",
            context={"messages": messages, "q": query},
            request=request,
        )
```

### Comprendre ce code

- `request.param("q", default="")` lit le mot-clé dans la *query string*
  (`?q=…`) ; vide par défaut.
- Quand `q` est renseigné, on exécute `SELECT_FILTERED` avec le **paramètre**
  `("%q%",)` : le `?` est lié à la valeur côté pilote SQL, **jamais** inséré
  dans la chaîne. C'est la protection contre l'injection SQL.
- Sans `q`, on retombe sur la liste complète (`SELECT_ALL`).

## La vue

```html
<!-- mvc/views/filter_list/index.html -->
<form method="get" action="/filter-list">
  <input type="text" name="q" value="{{ q }}" placeholder="Rechercher…">
  <button type="submit">Rechercher</button>
</form>

{% if messages %}
<ul>
  {% for m in messages %}
  <li>#{{ m.id }} — {{ m.content }}</li>
  {% endfor %}
</ul>
{% else %}
<p>Aucun message ne correspond.</p>
{% endif %}
```

### Comprendre ce code

- Le formulaire est en `method="get"` : la recherche se reflète dans l'URL
  (`?q=…`), partageable et rechargeable. Pas de `POST`, donc **pas de CSRF**
  ici (le CSRF protège les écritures).
- `value="{{ q }}"` réaffiche le mot-clé courant dans le champ.

## À retenir

- Une recherche = un paramètre d'URL + une clause SQL **paramétrée**.
- `LIKE ?` avec `("%mot%",)` : le motif est une **valeur liée**, pas une
  concaténation.
- Un formulaire de recherche est en `GET` (idempotent, partageable).

## Après ce starter

C'est, pour l'instant, le dernier palier disponible du **niveau intermédiaire**.
Faites le point dans le bilan du niveau.

[Bilan du niveau intermédiaire](bilan.md)
