# Transitions disponibles

Objectif : lister les statuts **atteignables** depuis un statut courant.

**Ce que vous allez apprendre :** `get_available_transitions(transitions, from)` liste
les passages partant du statut courant — idéal pour générer dynamiquement les
**boutons d'action** d'une fiche.

Troisième palier du **niveau intermédiaire** de la progression workflow.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-workflow` installé (palier « Installation »).

## Ce que ce starter montre

- `get_available_transitions(transitions, from)` → cibles possibles ;
- la génération des boutons d'action à partir des cibles ;
- une transformation **pure**.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_workflow.get_available_transitions` | Lister les transitions partant d'un statut. | [Workflow](../../../reference/api.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/workflow-available?from=review` : `published`, `draft`.

## Le contrôleur

```python
# mvc/controllers/workflow_available_controller.py
from forge_mvc_workflow import get_available_transitions, make_transition

_TRANSITIONS = [make_transition("draft", "review"), make_transition("review", "published"), ...]

available = get_available_transitions(_TRANSITIONS, from_name)
targets = [t.to_status for t in available]   # → boutons d'action
```

### Comprendre ce code

- Plutôt que de coder chaque bouton en dur, on **dérive** les actions possibles du
  statut courant : l'UI suit le workflow automatiquement.
- Un statut final renvoie une liste vide → aucune action, naturellement.
- C'est la version « lecture » de `can_transition` : on liste au lieu de tester un cas.

## À retenir

- `get_available_transitions` donne les actions possibles d'un statut.
- L'UI (boutons) se génère depuis le workflow, pas en dur.
- Statut final → aucune transition, sans cas particulier à coder.

## Après ce starter

Vous maîtrisez statuts et transitions. La suite (avancé) : l'**affichage**.

[Bilan du niveau intermédiaire](bilan.md)
