# Modifier et détacher

Objectif : changer les attributs d'une association, puis la supprimer.

**Ce que vous allez apprendre :** `update` modifie les **attributs** d'une paire existante (jamais les clés).
`detach` supprime l'association.
Les deux ciblent la paire `(article_id, tag_id)`.

!!! note "Module opt-in : SQL visible"
    `update` produit un `UPDATE … WHERE article_id = ? AND tag_id = ?`, `detach` un `DELETE …` ; tout paramétré.

## Classes Forge utilisées

| Méthode | Rôle dans ce starter | Référence |
|---------|----------------------|-----------|
| `PivotAdvancedService.update(source_id, target_id, pivot_data)` | Met à jour les attributs ; retourne le nombre de lignes touchées. | [Pivot avancé](../../reference.md) |
| `PivotAdvancedService.detach(source_id, target_id)` | Supprime l'association ; retourne le nombre de lignes touchées. | [Pivot avancé](../../reference.md) |

## Le contrôleur

```python
# mvc/controllers/pivot_update_controller.py
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


class PivotUpdateController(BaseController):

    @staticmethod
    def repositionner(request: Request) -> Response:
        article_id = int(request.form("article_id", default="0"))
        tag_id = int(request.form("tag_id", default="0"))
        position = int(request.form("position", default="0"))

        touched = _service().update(article_id, tag_id, {"position": position})
        return Response.text(f"{touched} association(s) repositionnée(s).")

    @staticmethod
    def detacher(request: Request) -> Response:
        article_id = int(request.form("article_id", default="0"))
        tag_id = int(request.form("tag_id", default="0"))

        touched = _service().detach(article_id, tag_id)
        return Response.text(f"{touched} association(s) détachée(s).")
```

### Comprendre ce code

- `update` ne touche **que** les attributs fournis (mise à jour partielle) ; il ne modifie jamais `article_id` ni `tag_id`.
- Un `update` avec un dictionnaire vide ne fait rien (retourne `0`).
- `detach` supprime la ligne de la paire et retourne le nombre de lignes supprimées (`0` si la paire n'existait pas).

## Les routes

```python
# mvc/routes.py
from mvc.controllers.pivot_update_controller import PivotUpdateController

with router.group("", public=True) as public:
    public.add("POST", "/pivot/update", PivotUpdateController.repositionner, name="pivot_update")
    public.add("POST", "/pivot/detach", PivotUpdateController.detacher, name="pivot_detach")
```

## À retenir

- `update` modifie les attributs d'une paire (jamais les clés).
- `detach` supprime l'association.
- Les deux retournent le nombre de lignes touchées.

## Après ce starter

Vous savez écrire et supprimer.
Voyons comment **lire** les associations d'un article.

[Lister les associations](pivot-list.md)
