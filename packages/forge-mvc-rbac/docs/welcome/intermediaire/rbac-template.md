# Permission dans un template

Objectif : afficher ou masquer un élément d'interface selon une permission, avec
`can()`.

**Ce que vous allez apprendre :** `make_can(request)` retourne un callable
`can(code) -> bool` lié à la requête. Forge l'expose automatiquement dans les
templates Jinja sous le nom `can()` : `{% if can("article.create") %}` conditionne
l'UI.

Troisième palier du **niveau intermédiaire** de la progression RBAC.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-rbac` installé. Sans utilisateur connecté,
    `can(...)` renvoie `False`.

## Ce que ce starter montre

- `make_can(request)` → `can(code)` ;
- l'usage de `can()` directement dans le template (auto-enregistré) ;
- l'UI qui s'adapte aux droits.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_rbac.make_can` | Callable `can(code)` lié à la requête. | RBAC |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/rbac-template` : le bouton « Créer » est masqué tant
qu'aucun utilisateur n'a la permission.

## Le contrôleur

Créez le contrôleur `mvc/controllers/rbac_template_controller.py` :

```python
# mvc/controllers/rbac_template_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_rbac import make_can


class RbacTemplateController(BaseController):
    """Starter pédagogique : conditionner l'UI à une permission via can()."""

    @staticmethod
    def index(request: Request) -> Response:
        can = make_can(request)
        return BaseController.render(
            "rbac_template/index.html",
            context={"can_list": can("article.list"), "can_create": can("article.create")},
            request=request,
        )
```

## La vue

Créez la vue `mvc/views/rbac_template/index.html` :

```html
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Permission dans un template - Forge</title>
</head>
<body>
  <h1>Permission dans un template</h1>

  <p>Valeurs calculées dans le contrôleur :</p>
  <ul>
    <li><code>can("article.list")</code> : <strong>{{ can_list }}</strong></li>
    <li><code>can("article.create")</code> : <strong>{{ can_create }}</strong></li>
  </ul>

  <p>Directement dans le template, via le helper <code>can()</code> auto-enregistré :</p>
  {% if can("article.create") %}
  <button>Créer un article</button>
  {% else %}
  <p><em>Bouton « Créer » masqué (permission manquante).</em></p>
  {% endif %}

  <p>Sans utilisateur connecté, <code>can(...)</code> renvoie <code>False</code> : l'UI
  s'adapte automatiquement aux droits.</p>
</body>
</html>
```

## La route

Ajoutez l'import et la route dans le groupe public de `mvc/routes.py` :

```python
# mvc/routes.py
from mvc.controllers.rbac_template_controller import RbacTemplateController

with router.group("", public=True) as public:
    public.add("GET", "/rbac-template", RbacTemplateController.index, name="rbac_template_index")
```

### Comprendre ce code

- `can()` est **auto-enregistré** par `forge-mvc-rbac` dans le contexte Jinja : pas
  besoin de le passer à chaque vue.
- Conditionner l'UI évite d'afficher des actions impossibles : meilleure expérience
  **et** défense en profondeur (le guard reste indispensable côté serveur).
- Sans utilisateur, `can(...)` est `False` : sécurisé par défaut.

## À retenir

- `can(code)` adapte l'UI aux permissions, dans le contrôleur **et** le template.
- Masquer un bouton ne dispense **pas** du guard serveur (`require_*`).
- Sécurisé par défaut : aucun droit sans utilisateur.

## Après ce starter

Vous savez vérifier et appliquer. La suite (avancé) : relier tout ça aux utilisateurs.

[Bilan du niveau intermédiaire](bilan.md)
