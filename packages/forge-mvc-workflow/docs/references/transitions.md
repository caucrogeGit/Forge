# Les transitions dans Forge Workflow

Ce document décrit comment `forge_mvc_workflow` déclare et vérifie les passages autorisés entre statuts.

Le fichier de code correspondant est `forge_mvc_workflow/transitions.py`.

## 1. À quoi sert ce module ?

Une transition décrit **explicitement** un passage autorisé d'un statut à un autre.
Aucune transition n'est jamais exécutée automatiquement : le module dit seulement si un passage est permis, l'application décide de l'appliquer.

C'est une application directe du principe « refuser la magie cachée »
: les passages permis sont déclarés, pas devinés.

## 2. Déclarer des transitions

```python
from forge_mvc_workflow import (
    make_status, validate_statuses,
    make_transition, validate_transitions,
    can_transition, get_available_transitions,
)

STATUTS = validate_statuses([
    make_status("draft", is_initial=True),
    make_status("pending"),
    make_status("published", is_final=True),
    make_status("archived", is_final=True),
])

TRANSITIONS = validate_transitions([
    make_transition("draft",     "pending"),
    make_transition("pending",   "published"),
    make_transition("pending",   "draft"),
    make_transition("published", "archived"),
], statuses=STATUTS)

can_transition(TRANSITIONS, "draft", "pending")     # True
can_transition(TRANSITIONS, "draft", "published")   # False
get_available_transitions(TRANSITIONS, "pending")   # [pending→published, pending→draft]
```

## 3. L'objet `WorkflowTransition`

```python
@dataclass(frozen=True)
class WorkflowTransition:
    from_status: str   # snake_case, obligatoire
    to_status: str     # snake_case, obligatoire
```

Il est **immuable** (`frozen=True`).
Le constructeur valide et normalise les deux noms ; une transition vers soi-même lève `WorkflowTransitionError`.

## 4. Les fonctions

| Fonction | Comportement |
|---|---|
| `make_transition(from_status, to_status)` | crée une `WorkflowTransition` validée |
| `validate_transitions(transitions, statuses=None)` | vérifie les doublons ; si `statuses` est fourni, vérifie que les statuts référencés existent |
| `can_transition(transitions, from_name, to_name)` | `True` si la transition est définie |
| `get_available_transitions(transitions, from_name)` | toutes les transitions partant de `from_name` |

## 5. Les règles

- `from_status` et `to_status` sont obligatoires, normalisés en snake_case.
- Une transition vers le même statut (`from == to`) lève `WorkflowTransitionError`.
- Un doublon `(from, to)` lève `WorkflowTransitionError`.
- `validate_transitions(..., statuses=STATUTS)` vérifie que tous les noms existent dans `STATUTS` ; sans `statuses`, cette vérification est sautée.
- `can_transition` et `get_available_transitions` normalisent les noms reçus en argument.

## 6. Les erreurs

`WorkflowTransitionError` est levée pour une transition vers soi-même, un doublon, ou un statut référencé inexistant.

## 7. Contextes d'utilisation

- **Déclaration** : `validate_transitions([...], statuses=STATUTS)` au chargement.
- **Garde de contrôleur** : `if not can_transition(...)` avant d'appliquer un changement de statut.
- **Vue** : `get_available_transitions(...)` pour proposer les actions possibles.

## 8. Voir aussi

- [Les statuts](status.md) : les états entre lesquels on transite.
- [Les helpers Jinja](jinja.md) : afficher le statut courant.
