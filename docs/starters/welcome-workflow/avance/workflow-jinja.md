# Helpers Workflow dans Jinja

Objectif : utiliser les helpers de statut **directement dans un template**.

**Ce que vous allez apprendre :** `make_workflow_jinja_helpers()` retourne un dict des
helpers (`workflow_status_badge`, `_label`, `_color`, `_badge_class`) prêt à injecter
dans le contexte d'une vue. Contrairement à RBAC, ils ne sont **pas** auto-enregistrés.

Troisième palier du **niveau avancé** de la progression workflow.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-workflow` installé (palier « Installation »).

## Ce que ce starter montre

- `make_workflow_jinja_helpers()` → dict de helpers ;
- l'injection des helpers dans le contexte de la vue ;
- leur usage direct dans le template.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_workflow.make_workflow_jinja_helpers` | Helpers de statut prêts à injecter dans Jinja. | [Workflow](../../../reference/api.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/workflow-jinja` : badge, libellé, couleur et classes
calculés dans le template.

## Le contrôleur et la vue

```python
# mvc/controllers/workflow_jinja_controller.py
from forge_mvc_workflow import make_status, make_workflow_jinja_helpers


class WorkflowJinjaController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        context = {"status": _DEMO_STATUS}
        context.update(make_workflow_jinja_helpers())   # injecte les helpers
        return BaseController.render("workflow_jinja/index.html", context=context, request=request)
```

```jinja
{# Les helpers injectés sont appelables dans le template #}
<li>Badge : {{ workflow_status_badge(status) }}</li>
<li>Libellé : {{ workflow_status_label(status) }}</li>
```

### Comprendre ce code

- Les helpers de `forge-mvc-workflow` ne sont **pas** auto-enregistrés (contrairement
  au `can()` de RBAC) : on les ajoute au contexte de la vue, ou à l'environnement Jinja
  de l'application une fois pour toutes.
- Une fois injectés, ils s'utilisent comme des fonctions de template.
- Cela laisse l'application **maîtresse** de ce qu'elle expose à ses templates
  (explicite plutôt que magique).

## À retenir

- `make_workflow_jinja_helpers()` regroupe les helpers d'affichage.
- Injection **explicite** dans le contexte ou l'environnement Jinja.
- Pas de magie : l'application décide ce qu'elle expose.

## Après ce starter

Vous avez parcouru toute la progression workflow : statuts, transitions, affichage.

[Bilan du niveau avancé](bilan.md)
