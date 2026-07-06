# Contraintes de champ

Objectif : déclarer des contraintes sur les attributs du pivot.

**Ce que vous allez apprendre :** `PivotFieldConstraint` rend un attribut **requis** (`required=True`) ou **non nullable** (`nullable=False`).
Le service les vérifie avant d'écrire et lève `PivotConstraintError` avec un **code** stable et le **champ** concerné.

Premier palier du **niveau avancé**.

!!! note "Module opt-in"
    Les contraintes du service complètent (sans remplacer) celles du schéma SQL.

## Classes Forge utilisées

| Classe | Rôle dans ce starter | Référence |
|--------|----------------------|-----------|
| `PivotFieldConstraint(name, required, nullable)` | Contrainte déclarative sur un champ pivot. | [Pivot avancé](../../reference.md) |
| `PivotConstraintError` | Erreur de contrainte (porte `code` et `field`). | [Pivot avancé](../../reference.md) |

## Déclarer des contraintes

Au lieu de `pivot_fields`, on passe `pivot_constraints` :

```python
# mvc/controllers/pivot_constraints_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_pivot import (
    PivotAdvancedService,
    PivotConstraintError,
    PivotFieldConstraint,
)


def _service() -> PivotAdvancedService:
    return PivotAdvancedService(
        table="article_tag",
        source_key="article_id",
        target_key="tag_id",
        pivot_constraints=[
            PivotFieldConstraint("position", required=True, nullable=False),
            PivotFieldConstraint("epingle", nullable=False),
        ],
    )


class PivotConstraintsController(BaseController):

    @staticmethod
    def attach(request: Request) -> Response:
        article_id = int(request.form("article_id", default="0"))
        tag_id = int(request.form("tag_id", default="0"))

        try:
            _service().attach(article_id, tag_id, {"position": 1, "epingle": 0})
        except PivotConstraintError as err:
            return Response.json({"erreur": err.code, "champ": err.field}, status=422)

        return Response.text("Association créée.")
```

### Comprendre ce code

- `required=True` sur `position` : un `attach` **sans** `position` lève `PivotConstraintError(code="required_field_missing", field="position")`.
- `nullable=False` : passer `position=None` (ou `epingle=None`) est refusé (`code="nullable_field_rejected"`).
- À l'`update`, `required` n'est **pas** vérifié (mise à jour partielle), mais `nullable` l'est toujours.
- `pivot_constraints` définit aussi la **liste blanche** : seuls `position` et `epingle` restent autorisés.

## À retenir

- `PivotFieldConstraint` déclare `required` et `nullable` par champ.
- Le service vérifie **avant** d'écrire, et lève `PivotConstraintError`.
- L'erreur porte un `code` stable et le `field` concerné.

## Après ce starter

Reste une garantie clé : refuser un **doublon** de paire.

[Unicité de la paire](pivot-unique.md)
