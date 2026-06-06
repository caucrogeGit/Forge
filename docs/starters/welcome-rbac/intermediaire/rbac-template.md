# Permission dans un template

Objectif : afficher ou masquer un élément d'interface selon une permission, avec
`can()`.

**Ce que vous allez apprendre :** `make_can(request)` retourne un callable
`can(code) -> bool` lié à la requête. Forge l'expose automatiquement dans les
templates Jinja sous le nom `can()` — `{% if can("article.create") %}` conditionne
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
| `forge_mvc_rbac.make_can` | Callable `can(code)` lié à la requête. | [RBAC](../../../reference/api.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/rbac-template` : le bouton « Créer » est masqué tant
qu'aucun utilisateur n'a la permission.

## Le contrôleur et la vue

```python
# mvc/controllers/rbac_template_controller.py
from forge_mvc_rbac import make_can


class RbacTemplateController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        can = make_can(request)
        return BaseController.render("rbac_template/index.html",
            context={"can_create": can("article.create")}, request=request)
```

```jinja
{# Directement dans le template, can() est auto-enregistré #}
{% if can("article.create") %}
<button>Créer un article</button>
{% endif %}
```

### Comprendre ce code

- `can()` est **auto-enregistré** par `forge-mvc-rbac` dans le contexte Jinja : pas
  besoin de le passer à chaque vue.
- Conditionner l'UI évite d'afficher des actions impossibles — meilleure expérience
  **et** défense en profondeur (le guard reste indispensable côté serveur).
- Sans utilisateur, `can(...)` est `False` : sécurisé par défaut.

## À retenir

- `can(code)` adapte l'UI aux permissions, dans le contrôleur **et** le template.
- Masquer un bouton ne dispense **pas** du guard serveur (`require_*`).
- Sécurisé par défaut : aucun droit sans utilisateur.

## Après ce starter

Vous savez vérifier et appliquer. La suite (avancé) : relier tout ça aux utilisateurs.

[Bilan du niveau intermédiaire](bilan.md)
