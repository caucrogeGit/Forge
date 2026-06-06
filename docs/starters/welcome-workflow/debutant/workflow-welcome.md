# Bonjour Forge Workflow

Objectif : premier contact avec le module **opt-in** `forge-mvc-workflow`, une
machine à états applicative.

**Ce que vous allez apprendre :** un **statut** porte un nom, un libellé, une
couleur, et des marqueurs `is_initial` / `is_final`. `make_status` en crée un ;
`validate_statuses` vérifie l'ensemble (pas de doublon, au plus un statut initial).

Premier palier du **niveau débutant** de la progression workflow
([vue d'ensemble des starters](../../index.md)).

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
| `forge_mvc_workflow.make_status` | Créer un statut (nom, libellé, couleur, marqueurs). | [Workflow](../../../reference/api.md) |
| `forge_mvc_workflow.validate_statuses` | Valider un jeu de statuts. | [Workflow](../../../reference/api.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/workflow-welcome` puis `/workflow-welcome/inspect`.

## Le contrôleur

```python
# mvc/controllers/workflow_welcome_controller.py
from forge_mvc_workflow import make_status, validate_statuses


def _demo_statuses():
    return validate_statuses([
        make_status("draft", "Brouillon", "gray", is_initial=True),
        make_status("review", "En revue", "yellow"),
        make_status("published", "Publié", "green"),
        make_status("archived", "Archivé", "red", is_final=True),
    ])
```

### Comprendre ce code

- Un workflow a **un** statut initial (`is_initial`) et peut avoir des statuts finaux
  (`is_final`) — `validate_statuses` le vérifie.
- Le **nom** est l'identifiant (`snake_case`) ; le **libellé** et la **couleur** sont
  pour l'affichage.
- Le module est **sans état** : il décrit la machine, l'application stocke le statut
  courant de ses objets.

## À retenir

- Un statut = nom + libellé + couleur + marqueurs (`is_initial`/`is_final`).
- `validate_statuses` garantit un jeu cohérent.
- Workflow décrit la machine ; il ne persiste rien.

## Après ce starter

Premier contact établi. La suite : la brique « nom de statut ».

[Nom de statut](workflow-status.md)
