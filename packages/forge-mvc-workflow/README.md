# forge-mvc-workflow

Module workflow pour Forge — statuts et transitions applicatives.

Extrait du core Forge depuis la version 2.6.0 (ADR-004).

## Installation

```bash
pip install forge-mvc-workflow
# ou en mode developpement
pip install -e packages/forge-mvc-workflow/
```

## Usage

```python
from forge_mvc_workflow import (
    WorkflowStatus,
    WorkflowTransition,
    make_status,
    make_transition,
    validate_statuses,
    validate_transitions,
    can_transition,
    get_available_transitions,
    make_workflow_jinja_helpers,
)

# Definir des statuts
statuses = validate_statuses([
    make_status("brouillon", label="Brouillon", color="gray"),
    make_status("confirme", label="Confirme", color="green"),
    make_status("annule", label="Annule", color="red"),
])

# Definir des transitions autorisees
transitions = validate_transitions([
    make_transition("brouillon", "confirme"),
    make_transition("brouillon", "annule"),
    make_transition("confirme", "annule"),
], statuses=statuses)

# Verifier une transition
if can_transition(transitions, "brouillon", "confirme"):
    ...

# Obtenir les transitions disponibles depuis un statut
available = get_available_transitions(transitions, "brouillon")
```

## Helpers Jinja2

```python
env.globals.update(make_workflow_jinja_helpers())
```

Dans un template :

```jinja2
{{ workflow_status_badge(reservation.status) }}
{{ workflow_status_label(reservation.status) }}
```

## Cas d'usage

- Statut d'une reservation (brouillon → confirmee → terminee → annulee)
- Statut d'un document (redaction → validation → publie)
- Statut d'une commande (panier → payee → expediee → livree)

## API publique

- `WorkflowStatus` — dataclass statut (name, label, color)
- `WorkflowTransition` — dataclass transition (from_status, to_status)
- `make_status(name, label, color)` — constructeur valide
- `make_transition(from_status, to_status)` — constructeur valide
- `validate_statuses(list)` — valide une liste de statuts
- `validate_transitions(list, statuses)` — valide les transitions par rapport aux statuts
- `can_transition(transitions, from_name, to_name)` — teste une transition
- `get_available_transitions(transitions, from_name)` — liste les transitions disponibles
- `make_workflow_jinja_helpers()` — dict de helpers Jinja2
