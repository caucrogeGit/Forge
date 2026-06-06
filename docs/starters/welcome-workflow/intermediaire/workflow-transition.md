# Déclarer les transitions

Objectif : déclarer les **passages autorisés** entre statuts.

**Ce que vous allez apprendre :** `make_transition(from, to)` crée une transition ;
`validate_transitions` vérifie l'ensemble contre les statuts connus. Ce qui n'est
**pas** déclaré est interdit (fermé par défaut).

Premier palier du **niveau intermédiaire** de la progression workflow.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-workflow` installé (palier « Installation »).

## Ce que ce starter montre

- `make_transition(from, to)` pour chaque passage ;
- `validate_transitions(transitions, statuses)` ;
- la liste des transitions validées.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_workflow.make_transition` | Créer une transition `from → to`. | [Workflow](../../../reference/api.md) |
| `forge_mvc_workflow.validate_transitions` | Valider l'ensemble des transitions. | [Workflow](../../../reference/api.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/workflow-transition` : la liste des passages autorisés.

## Le contrôleur

```python
# mvc/controllers/workflow_transition_controller.py
from forge_mvc_workflow import make_status, make_transition, validate_transitions

_RAW_TRANSITIONS = [("draft", "review"), ("review", "published"), ("review", "draft"), ("published", "archived")]

transitions = validate_transitions(
    [make_transition(f, t) for f, t in _RAW_TRANSITIONS], _STATUSES
)
```

### Comprendre ce code

- Le workflow est **fermé par défaut** : seuls les passages déclarés sont possibles.
- `validate_transitions` peut vérifier que chaque transition relie des statuts connus.
- Déclarer explicitement les transitions rend le cycle de vie **auditable**.

## À retenir

- Une transition autorise un passage `from → to`.
- Tout ce qui n'est pas déclaré est **interdit**.
- Le cycle de vie est explicite et validé.

## Après ce starter

La suite : vérifier si un passage précis est autorisé.

[Vérifier une transition](workflow-check.md)
