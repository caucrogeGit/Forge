# Workflow — Référence

> **Module extrait** : le code workflow vit dans `forge-mvc-workflow`.
> Voir `packages/forge-mvc-workflow/README.md` pour l'installation et l'API utilisateur.

`forge_mvc_workflow` est un **module officiel** Forge, distribué séparément (ADR-004).
Il modélise des états simples, des transitions explicitement autorisées et des helpers d'affichage pour les gabarits Jinja2.
Il est indépendant de tout métier applicatif.

## Référence par module

| Module | Page | Contenu |
|---|---|---|
| `status.py` | [Les statuts](references/status.md) | `WorkflowStatus`, `make_status`, `validate_statuses`, `find_status` |
| `transitions.py` | [Les transitions](references/transitions.md) | `WorkflowTransition`, `can_transition`, `get_available_transitions` |
| `jinja.py` | [Les helpers Jinja](references/jinja.md) | badges et libellés de statut pour les gabarits |

## Import principal

```python
from forge_mvc_workflow import (
    WorkflowStatus, WorkflowStatusError,
    make_status, validate_statuses, find_status,
    normalize_status_name, validate_status_name,
    WorkflowTransition, WorkflowTransitionError,
    make_transition, validate_transitions,
    can_transition, get_available_transitions,
    workflow_status_label, workflow_status_color,
    workflow_status_badge_class, workflow_status_badge,
    make_workflow_jinja_helpers,
)
```

## Limites actuelles

La brique Workflow fournit un socle de statuts, de transitions et d'affichage.
Forge ne fournit **pas encore** dans ce socle :

- table SQL de workflow (pas de colonne `statut` générée) ;
- migration SQL ;
- historique des changements de statut ;
- auteur et timestamp du changement ;
- intégration CRUD (les listes et formulaires admin n'affichent pas encore le statut) ;
- intégration des pages publiques (les gabarits publics n'incluent pas encore le badge) ;
- CLI workflow (`forge make:workflow-status`…) ;
- générateur de contrôleur ou de gabarit avec statut ;
- permissions RBAC liées aux transitions (ex. : seul un admin peut publier) ;
- notifications ou emails déclenchés par une transition ;
- logique métier applicative (statut de demande, de réservation, etc.).

Ces fonctionnalités peuvent être construites par l'application au-dessus du socle actuel, ou seront traitées dans des tickets ultérieurs.
