# Paginer une liste

Objectif : n'afficher qu'une **tranche** des lignes à la fois, avec une
navigation page par page.

**Ce que vous allez apprendre :** lire un numéro de page avec `request.param`,
le traduire en `LIMIT ? OFFSET ?` **paramétré**, et utiliser un `COUNT(*)` pour
savoir s'il existe une page suivante.

Palier 3 du **niveau intermédiaire** de la
[progression officielle des starters](../../index.md#progression-recommandee),
après [Rechercher / filtrer](filter-list.md).

## Ce que ce starter montre

- une route `GET /pagination?page=N` ;
- `LIMIT ? OFFSET ?` paramétré, l'offset calculé depuis la page ;
- un `COUNT(*)` pour le total et les liens **précédent / suivant** ;
- une conversion robuste du paramètre `page` (valeur invalide → page 1).

Aucune écriture. Aucun CRUD complet.

## Classes Forge utilisées

| Classe | Rôle dans ce starter | Référence |
|--------|----------------------|-----------|
| `Request` | Lire la page avec `request.param("page", ...)`. | [Request](../../../reference/http.md#3-request-reference) |
| `Response` | Produite via `render(...)`. | [Response](../../../reference/http.md#4-response-reference) |
| `BaseController` | Fournit `render(...)`. | [BaseController](../../../reference/api.md#coremvccontroller) |
| `core.database.db.fetch_all` / `fetch_one` | Lire une tranche + compter le total. | [Migrations SQL](../../../features/migrations.md) |

## Tester

```bash
forge migration:apply
forge run
```

Ouvrez `https://localhost:8000/pagination` → la première page (3 messages) +
un lien **Suivant**. Cliquez pour parcourir les pages.

## Le contrôleur

```python
# mvc/controllers/pagination_controller.py
from core.database.db import fetch_all, fetch_one
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


PAGE_SIZE = 3
SELECT_PAGE = (
    "SELECT id, content FROM first_sql_messages "
    "ORDER BY id LIMIT ? OFFSET ?"
)
COUNT_ALL = "SELECT COUNT(*) AS total FROM first_sql_messages"


def _page_number(raw: str) -> int:
    try:
        page = int(raw)
    except (TypeError, ValueError):
        return 1
    return page if page >= 1 else 1


class PaginationController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        page = _page_number(request.param("page", default="1"))
        offset = (page - 1) * PAGE_SIZE
        messages = fetch_all(SELECT_PAGE, (PAGE_SIZE, offset))
        total = fetch_one(COUNT_ALL)["total"]
        return BaseController.render(
            "pagination/index.html",
            context={
                "messages": messages,
                "page": page,
                "has_prev": page > 1,
                "has_next": page * PAGE_SIZE < total,
            },
            request=request,
        )
```

### Comprendre ce code

- `LIMIT ? OFFSET ?` sont **paramétrés** : la taille de page et l'offset sont
  des valeurs liées, jamais concaténées.
- `offset = (page - 1) * PAGE_SIZE` : la page 1 commence à 0, la page 2 à 3, etc.
- `COUNT(*)` donne le total ; `has_next = page * PAGE_SIZE < total` dit s'il
  reste des lignes après la page courante.
- `_page_number` protège contre un `?page=` absent ou non numérique.

## La vue

```html
<!-- mvc/views/pagination/index.html -->
<h1>Messages, page {{ page }}</h1>

{% if messages %}
<ul>
  {% for m in messages %}
  <li>#{{ m.id }} : {{ m.content }}</li>
  {% endfor %}
</ul>
{% endif %}

<nav>
  {% if has_prev %}<a href="/pagination?page={{ page - 1 }}">← Précédent</a>{% endif %}
  {% if has_next %}<a href="/pagination?page={{ page + 1 }}">Suivant →</a>{% endif %}
</nav>
```

### Comprendre ce code

- Les liens **précédent / suivant** ne s'affichent que s'ils mènent quelque
  part (`has_prev` / `has_next`).
- La page courante est passée dans l'URL (`?page=N`) : partageable et rechargeable.

## À retenir

- Paginer = `LIMIT`/`OFFSET` paramétrés + un `COUNT(*)` pour les bornes.
- L'offset se calcule depuis le numéro de page : `(page - 1) * taille`.
- Toujours blinder la conversion d'un paramètre d'URL en entier.

## Après ce starter

Passez au palier suivant : **Héritage de gabarit**, factoriser l'enveloppe
HTML commune avec `{% extends %}`.

[Continuer avec Héritage de gabarit](layout-template.md)
