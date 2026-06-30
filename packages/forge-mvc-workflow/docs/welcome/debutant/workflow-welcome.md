# Welcome Workflow

Objectif : premier contact avec le module **opt-in** `forge-mvc-workflow`, une
machine à états applicative.

**Ce que vous allez apprendre :** un **statut** porte un nom, un libellé, une
couleur, et des marqueurs `is_initial` / `is_final`. `make_status` en crée un ;
`validate_statuses` vérifie l'ensemble (pas de doublon, au plus un statut initial).

Premier palier du **niveau débutant** de la progression workflow
(vue d'ensemble des starters).

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-workflow` installé (palier « Installation »). Module
    **sans état** : que des fonctions pures.

## Ce que ce starter montre

- une route texte de **premier contact** (`GET /workflow-welcome`) ;
- un jeu de statuts de démo (`draft → review → published → archived`) en JSON
  (`GET /workflow-welcome/inspect`).

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_workflow.make_status` | Créer un statut (nom, libellé, couleur, marqueurs). | Workflow |
| `forge_mvc_workflow.validate_statuses` | Valider un jeu de statuts. | Workflow |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/workflow-welcome` puis `/workflow-welcome/inspect`.

## Le contrôleur

```python
# mvc/controllers/workflow_welcome_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_workflow import make_status, validate_statuses


def _demo_statuses():
    """Workflow de publication de démonstration."""
    return validate_statuses([
        make_status("draft", "Brouillon", "gray", is_initial=True),
        make_status("review", "En revue", "yellow"),
        make_status("published", "Publié", "green"),
        make_status("archived", "Archivé", "red", is_final=True),
    ])


class WorkflowWelcomeController(BaseController):
    """Starter pédagogique : premier contact avec Forge Workflow."""

    @staticmethod
    def index(request: Request) -> Response:
        return Response.text("Welcome Workflow")

    @staticmethod
    def inspect(request: Request) -> Response:
        statuses = _demo_statuses()
        return Response.json({
            "count": len(statuses),
            "statuses": [
                {
                    "name": s.name,
                    "label": s.label,
                    "color": s.color,
                    "is_initial": s.is_initial,
                    "is_final": s.is_final,
                }
                for s in statuses
            ],
        })
```

### Comprendre ce code

- Un workflow a **un** statut initial (`is_initial`) et peut avoir des statuts finaux
  (`is_final`) : `validate_statuses` le vérifie.
- Le **nom** est l'identifiant (`snake_case`) ; le **libellé** et la **couleur** sont
  pour l'affichage.
- Le module est **sans état** : il décrit la machine, l'application stocke le statut
  courant de ses objets.

## La route

Dans le groupe public de `mvc/routes.py`, ajoutez l'import et les deux routes :

```python
# mvc/routes.py
from mvc.controllers.workflow_welcome_controller import WorkflowWelcomeController

with router.group("", public=True) as public:
    public.add("GET", "/workflow-welcome", WorkflowWelcomeController.index, name="workflow_welcome_index")
    public.add("GET", "/workflow-welcome/inspect", WorkflowWelcomeController.inspect, name="workflow_welcome_inspect")
```

## À retenir

- Un statut = nom + libellé + couleur + marqueurs (`is_initial`/`is_final`).
- `validate_statuses` garantit un jeu cohérent.
- Workflow décrit la machine ; il ne persiste rien.

## Après ce starter

Premier contact établi. La suite : la brique « nom de statut ».

[Nom de statut](workflow-status.md)
