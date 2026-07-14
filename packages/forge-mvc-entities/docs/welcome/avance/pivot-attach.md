# Attacher une association

Objectif : créer une association pivot **avec ses attributs**.

**Ce que vous allez apprendre :** `attach` ajoute une ligne dans la table pivot.
On lui donne l'`article_id`, le `tag_id` et un dictionnaire d'attributs (`position`, `epingle`).
Seuls les champs déclarés dans la liste blanche sont acceptés.

Suite du **niveau avancé** : après le modèle, la manipulation des associations.

!!! note "Module opt-in : SQL visible"
    En production, le service délègue à `core.database.db` (`execute`, `fetch_one`…).
    La table `article_tag` doit exister.
    Pour les tests, ces exécuteurs sont **injectables**.

## Classes Forge utilisées

| Méthode | Rôle dans ce starter | Référence |
|---------|----------------------|-----------|
| `PivotAdvancedService.attach(source_id, target_id, pivot_data)` | Crée l'association et retourne l'id inséré. | [Pivot avancé](../../reference.md) |

## Le contrôleur

```python
# mvc/controllers/pivot_attach_controller.py
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


class PivotAttachController(BaseController):

    @staticmethod
    def attach(request: Request) -> Response:
        article_id = int(request.form("article_id", default="0"))
        tag_id = int(request.form("tag_id", default="0"))

        service = _service()
        service.attach(article_id, tag_id, {"position": 1, "epingle": 0})

        return Response.text(f"Tag {tag_id} attaché à l'article {article_id}.")
```

### Comprendre ce code

- `attach(article_id, tag_id, {...})` insère la ligne `(article_id, tag_id, position, epingle)` et retourne l'identifiant inséré.
- Le dictionnaire d'attributs ne peut contenir **que** `position` et `epingle` : un champ inconnu lève une erreur (liste blanche).
- Le SQL produit est un `INSERT` paramétré : aucune valeur n'est concaténée.

!!! warning "Doublon de paire"
    Tel quel, attacher deux fois la même paire crée deux lignes (ou échoue sur la clé primaire SQL).
    Pour refuser le doublon **avant** l'`INSERT`, on active `unique_pair`, quelques paliers plus loin.

## La route

```python
# mvc/routes/__init__.py
from mvc.controllers.pivot_attach_controller import PivotAttachController

with router.group("", public=True) as public:
    public.add("POST", "/pivot/attach", PivotAttachController.attach, name="pivot_attach")
```

## À retenir

- `attach` crée l'association et écrit ses attributs.
- Seuls les champs de la liste blanche sont acceptés.
- L'`INSERT` est paramétré (pas d'injection).

## Après ce starter

Une association existe.
Voyons comment la **modifier** et la **détacher**.

[Modifier et détacher](pivot-update.md)
