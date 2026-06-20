# Erreurs de formulaire

Objectif : afficher une erreur de pivot dans un formulaire, proprement.

**Ce que vous allez apprendre :** `pivot_error_to_form_error` convertit une
exception du service en `PivotFormError` — un objet stable (`code`, `message`,
`field`) prêt à être affiché à côté du bon champ.

Dernier palier du **niveau avancé**.

!!! note "Module opt-in"
    On ne laisse jamais une exception brute remonter à l'utilisateur : on la
    traduit en message de formulaire.

## Classes Forge utilisées

| Fonction / classe | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `pivot_error_to_form_error(error)` | Normalise une exception pivot en `PivotFormError`. | [Pivot avancé](../../../entities/pivot-advanced.md) |
| `PivotFormError` | Erreur affichable : `code`, `message`, `field`. | [Pivot avancé](../../../entities/pivot-advanced.md) |

## Le contrôleur

```python
# mvc/controllers/pivot_form_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_pivot import (
    PivotAdvancedService,
    PivotConstraintError,
    PivotFieldConstraint,
    pivot_error_to_form_error,
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
        unique_pair=True,
    )


class PivotFormController(BaseController):

    @staticmethod
    def submit(request: Request) -> Response:
        article_id = int(request.form("article_id", default="0"))
        tag_id = int(request.form("tag_id", default="0"))
        epingle = int(request.form("epingle", default="0"))

        try:
            # position omise volontairement : déclenche la contrainte required.
            _service().attach(article_id, tag_id, {"epingle": epingle})
        except PivotConstraintError as err:
            form_error = pivot_error_to_form_error(err)
            return BaseController.render(
                "pivot_form/index.html",
                context={
                    "erreur_code": form_error.code,
                    "erreur_message": form_error.message,
                    "erreur_champ": form_error.field,
                },
                request=request,
            )

        return Response.text("Association créée.")
```

### Comprendre ce code

- `pivot_error_to_form_error` transforme `PivotConstraintError` en
  `PivotFormError` : un `code`, un `message` humain et le `field` fautif.
- Le `field` permet d'afficher l'erreur **à côté du bon champ** du formulaire
  (par exemple sous `position`).
- Une exception non liée au pivot renvoie un `PivotFormError` générique : pas de
  fuite de détail SQL vers l'utilisateur.

## La vue (extrait)

```html
{% if erreur_message %}
<p class="erreur" data-champ="{{ erreur_champ }}">{{ erreur_message }}</p>
{% endif %}
```

## À retenir

- `pivot_error_to_form_error` normalise une erreur pivot pour le formulaire.
- `PivotFormError` porte `code`, `message` et `field`.
- L'utilisateur voit un message clair, jamais une exception brute.

## Après ce starter

Vous tenez le pivot enrichi de bout en bout. Faisons le **bilan** du niveau avancé.

[Bilan du niveau avancé](bilan.md)
