# Gérer les erreurs de catalogue

Objectif : réagir proprement à un catalogue absent, invalide, ou à une locale dangereuse.

**Ce que vous allez apprendre :** un catalogue principal absent ou mal formé lève `TranslationCatalogError`.
Une locale contenant des caractères de chemin (`..`, `/`) est **refusée** de la même manière : elle ne peut jamais désigner un fichier hors du dossier des catalogues.

Dernier palier du **niveau avancé**.

!!! note "Module opt-in : sécurité"
    La locale ne sert qu'à composer `<locale>.json`.
    Tout caractère de chemin est rejeté : pas de traversal possible.

## Classes Forge utilisées

| Élément | Rôle dans ce starter | Référence |
|---------|----------------------|-----------|
| `TranslationCatalogError` | Catalogue absent, JSON invalide, ou locale interdite. | Opt-ins |

## Le contrôleur

```python
# mvc/controllers/i18n_errors_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_i18n import TranslationCatalogError, load_catalog


class I18nErrorsController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        locale = request.query("lang", default="fr")
        try:
            catalogue = load_catalog(locale)
        except TranslationCatalogError as err:
            # locale inconnue, JSON invalide, ou locale dangereuse (../)
            return Response.json({"erreur": str(err)}, status=422)

        return Response.json({"locale": locale, "cles": sorted(catalogue.keys())})
```

### Comprendre ce code

- `load_catalog("zz")` (catalogue inexistant) lève `TranslationCatalogError`.
- `load_catalog("../secret")` est **refusé** : la locale doit correspondre à un motif strict (lettres, chiffres, `-`, `_`), donc aucun chemin n'en sort.
- Un fichier JSON mal formé (ou dont une valeur n'est pas une chaîne) lève la même erreur : on l'attrape et on répond `422` sans détail technique.

## La route

```python
# mvc/routes.py
from mvc.controllers.i18n_errors_controller import I18nErrorsController

with router.group("", public=True) as public:
    public.add("GET", "/i18n-errors", I18nErrorsController.index, name="i18n_errors_index")
```

## À retenir

- Catalogue absent ou JSON invalide → `TranslationCatalogError`.
- Une locale avec caractères de chemin est refusée (anti-traversal).
- On attrape l'erreur pour répondre proprement, sans fuite technique.

## Après ce starter

Vous tenez l'i18n de bout en bout.
Faisons le **bilan** du niveau avancé.

[Bilan du niveau avancé](bilan.md)
