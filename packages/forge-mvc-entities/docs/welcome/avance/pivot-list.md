# Lister les associations

Objectif : lire toutes les associations d'un article, avec leurs attributs.

**Ce que vous allez apprendre :** `list_for_source` retourne les `PivotRow` liés à une source.
Chaque `PivotRow` porte `source_id`, `target_id` et un dict `pivot_data` (les attributs `position`, `epingle`).

!!! note "Module opt-in : SQL visible"
    `list_for_source` produit un `SELECT * FROM article_tag WHERE article_id = ?`.

## Classes Forge utilisées

| Méthode / classe | Rôle dans ce starter | Référence |
|------------------|----------------------|-----------|
| `PivotAdvancedService.list_for_source(source_id)` | Liste les associations d'une source. | [Pivot avancé](../../reference.md) |
| `PivotRow` | Ligne pivot : `source_id`, `target_id`, `pivot_data`. | [Pivot avancé](../../reference.md) |

## Le contrôleur

```python
# mvc/controllers/pivot_list_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_entities import PivotAdvancedService


def _service() -> PivotAdvancedService:
    return PivotAdvancedService(
        table="article_tag",
        source_key="article_id",
        target_key="tag_id",
        pivot_fields=["position", "epingle"],
    )


class PivotListController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        article_id = int(request.query("article_id", default="0"))

        rows = _service().list_for_source(article_id)
        return Response.json([
            {
                "article_id": row.source_id,
                "tag_id": row.target_id,
                "position": row.pivot_data.get("position"),
                "epingle": row.pivot_data.get("epingle"),
            }
            for row in rows
        ])
```

### Comprendre ce code

- `list_for_source(article_id)` retourne une liste de `PivotRow`.
- `row.pivot_data` est un dict des attributs : on lit `position` et `epingle` avec `.get(...)` pour rester tolérant si une colonne est absente.
- Les clés (`source_id`, `target_id`) sont séparées des attributs : la structure reflète exactement la table.

## La route

```python
# mvc/routes/__init__.py
from mvc.controllers.pivot_list_controller import PivotListController

with router.group("", public=True) as public:
    public.add("GET", "/pivot/list", PivotListController.index, name="pivot_list")
```

## À retenir

- `list_for_source` liste les associations d'une source.
- Chaque `PivotRow` sépare clés et `pivot_data` (attributs).
- Le `SELECT` est paramétré.

## Après ce starter

Vous maîtrisez le cycle attacher/modifier/lister.
Faisons le **bilan**.

[Continuer : contraintes de champ](pivot-constraints.md)
