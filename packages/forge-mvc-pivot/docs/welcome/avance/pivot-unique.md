# Unicité de la paire

Objectif : refuser l'attachement d'une paire déjà existante.

**Ce que vous allez apprendre :** avec `unique_pair=True`, le service vérifie **avant l'INSERT** que la paire `(article_id, tag_id)` n'existe pas déjà.
Sinon, il lève `PivotConstraintError(code="duplicate_pair")`.

!!! note "Module opt-in"
    Ce contrôle applicatif est un **confort d'UX** : il donne une erreur claire avant d'écrire.
    La garantie de fond reste la **clé primaire composite** du schéma SQL (vue au niveau débutant).

## Classes Forge utilisées

| Option / méthode | Rôle dans ce starter | Référence |
|------------------|----------------------|-----------|
| `PivotAdvancedService(..., unique_pair=True)` | Active la vérification d'unicité avant `attach`. | [Pivot avancé](../../reference.md) |
| `PivotAdvancedService.get(source_id, target_id)` | Retourne l'association ou `None`. | [Pivot avancé](../../reference.md) |

## Le contrôleur

```python
# mvc/controllers/pivot_unique_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_pivot import PivotAdvancedService, PivotConstraintError


def _service() -> PivotAdvancedService:
    return PivotAdvancedService(
        table="article_tag",
        source_key="article_id",
        target_key="tag_id",
        pivot_fields=["position", "epingle"],
        unique_pair=True,
    )


class PivotUniqueController(BaseController):

    @staticmethod
    def attach(request: Request) -> Response:
        article_id = int(request.form("article_id", default="0"))
        tag_id = int(request.form("tag_id", default="0"))

        try:
            _service().attach(article_id, tag_id, {"position": 1, "epingle": 0})
        except PivotConstraintError as err:
            if err.code == "duplicate_pair":
                return Response.text("Ce tag est déjà attaché à cet article.", status=409)
            raise

        return Response.text("Association créée.")
```

### Comprendre ce code

- `unique_pair=True` fait un `get(source_id, target_id)` avant l'`INSERT` ; si la paire existe, `attach` lève `PivotConstraintError(code="duplicate_pair")`.
- Le contrôle est **non atomique** : sous forte concurrence, deux requêtes simultanées pourraient passer le `get` avant l'`INSERT`.
  La clé primaire SQL reste donc le garde-fou décisif.
- On distingue le `code` pour répondre `409 Conflict` proprement.

## À retenir

- `unique_pair=True` refuse un doublon **avant** l'`INSERT`, avec un code clair.
- C'est un confort d'UX ; la garantie réelle est la clé primaire composite.
- Tester le `code` permet une réponse HTTP adaptée.

## Après ce starter

Dernière étape : transformer ces erreurs en messages **de formulaire**.

[Erreurs de formulaire](pivot-form.md)
