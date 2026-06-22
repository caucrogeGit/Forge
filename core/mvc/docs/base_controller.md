# Le contrôleur de base dans Forge

Ce document décrit `BaseController`, classe mère de tous les contrôleurs.

Le fichier de code correspondant est `core/mvc/controller/base_controller.py`.

## 1. À quoi sert ce module ?

Un contrôleur reçoit une requête et produit une réponse.
`BaseController` fournit les utilitaires communs : rendre une vue, rediriger, poser un message flash.

## 2. L'objet

```python
from core.mvc.controller.base_controller import BaseController

class ArticleController(BaseController):
    @staticmethod
    def index(request):
        return BaseController.render("article/index.html", request=request,
                                     context={"articles": rows})
```

| Élément | Rôle |
|---|---|
| `BaseController` | classe de base : `render(...)`, `redirect(...)`, gestion du contexte et du flash |

`render` injecte le contexte Jinja (dont les fournisseurs enregistrés, voir [le registre](registry.md)) et rend la vue ; `redirect` produit une redirection, avec `flash` optionnel.

## 3. Contextes d'utilisation

- **Toute action de contrôleur** : `BaseController.render` / `redirect`.

## 4. Voir aussi

- [Le registre de contexte Jinja](registry.md) : enrichir le contexte de rendu.
- [L'objet Response (core/http)](../core-http/response.md) et [le gestionnaire de gabarits](../core-templating/manager.md).
