# Bonjour Forge Pivot

Objectif : premier contact avec le module **opt-in** `forge-mvc-pivot`.

**Ce que vous allez apprendre :** un pivot **enrichi** est une association
`many_to_many` dont la table de liaison **porte des attributs**. Entre un
`Article` et un `Tag`, la table `article_tag` peut stocker une `position`
(ordre du tag sur l'article) et un drapeau `epingle` (tag mis en avant). C'est
précisément ce que `PivotAdvancedService` rend explicite et sûr.

Premier palier du **niveau débutant** de la progression pivot
(vue d'ensemble des starters).

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-pivot` installé (palier « Installation »). Module à
    **SQL visible** : aucun ORM, les requêtes restent lisibles.

## Pivot ordinaire vs pivot enrichi

| Cas | Outil | Table de liaison |
|-----|-------|------------------|
| `Article` ↔ `Tag` sans donnée sur la relation | `many_to_many` simple | deux colonnes de clés seulement |
| `Article` ↔ `Tag` avec `position`, `epingle` | **pivot enrichi** (`forge-mvc-pivot`) | clés **+ colonnes d'attributs** |

Dès que la relation **elle-même** porte une donnée, le pivot enrichi s'impose.

## Ce que ce starter montre

- construire un `PivotAdvancedService` pour `article_tag` ;
- inspecter sa configuration (table, clés, champs autorisés) via une route JSON.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_pivot.PivotAdvancedService` | Service de lecture/écriture d'un pivot enrichi. | [Pivot avancé](../../reference.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/pivot-welcome` puis `/pivot-welcome/inspect`.

## Le contrôleur

```python
# mvc/controllers/pivot_welcome_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_pivot import PivotAdvancedService


def _article_tag_service() -> PivotAdvancedService:
    """Service pivot pour l'association Article ↔ Tag, avec deux attributs."""
    return PivotAdvancedService(
        table="article_tag",
        source_key="article_id",
        target_key="tag_id",
        pivot_fields=["position", "epingle"],
    )


class PivotWelcomeController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        return Response.text("Bonjour Forge Pivot")

    @staticmethod
    def inspect(request: Request) -> Response:
        service = _article_tag_service()
        return Response.json({
            "table": "article_tag",
            "source_key": "article_id",
            "target_key": "tag_id",
            "pivot_fields": ["position", "epingle"],
        })
```

### Comprendre ce code

- Un `PivotAdvancedService` est **générique** : on lui déclare la table, la clé
  source, la clé cible et la **liste blanche** des champs d'attributs autorisés.
- Cette liste blanche est centrale : seuls `position` et `epingle` pourront être
  écrits ; tout autre champ sera refusé (vous le verrez au niveau avancé).
- Aucun accès base ici : on ne fait qu'instancier et décrire le service.

## La route

Dans `mvc/routes.py`, ajoutez l'import en tête de fichier et les routes dans le groupe public.

```python
# mvc/routes.py
from mvc.controllers.pivot_welcome_controller import PivotWelcomeController

with router.group("", public=True) as public:
    public.add("GET", "/pivot-welcome", PivotWelcomeController.index, name="pivot_welcome_index")
    public.add("GET", "/pivot-welcome/inspect", PivotWelcomeController.inspect, name="pivot_welcome_inspect")
```

## À retenir

- Un pivot **enrichi** porte des attributs sur la relation elle-même.
- `PivotAdvancedService` déclare table, clés et **liste blanche** des champs.
- SQL visible, aucun ORM.

## Après ce starter

Premier contact établi. La suite : **générer** le sous-CRUD pivot avec une commande.

[Générer le sous-CRUD pivot](pivot-make.md)
