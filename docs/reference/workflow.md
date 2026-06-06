# Workflow — Statuts et transitions

> **Module extrait** : depuis Forge 2.7.0, le code workflow vit dans
> `forge-mvc-workflow`. Voir `packages/forge-mvc-workflow/README.md` pour
> l'installation et l'API utilisateur. Cette page documente l'API publique
> pour mémoire et référence rapide.


`forge_mvc_workflow` est un **module officiel** Forge, distribué séparément depuis Forge 2.7.0 (ADR-004). Il modélise des états simples, des transitions explicitement autorisées et des helpers d'affichage pour les templates Jinja2. Il est indépendant de tout métier applicatif.

**Modules :**

- `forge_mvc_workflow.status` — statuts et validation ;
- `forge_mvc_workflow.transitions` — transitions entre statuts ;
- `forge_mvc_workflow.jinja` — helpers d'affichage injectés automatiquement dans `Jinja2Renderer`.

**Import principal :**

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

---

### Workflow — Statuts génériques

Les statuts modélisent les états possibles d'une entité applicative. Ils restent génériques : `draft`, `pending`, `published`, `archived`, `new`, `in_progress`, `done`, `cancelled`…

#### API

```python
from forge_mvc_workflow import make_status, validate_statuses, find_status

STATUTS = validate_statuses([
    make_status("draft",     label="Brouillon",  color="gray",   is_initial=True),
    make_status("pending",   label="En attente", color="yellow"),
    make_status("published", label="Publié",     color="green",  is_final=True),
    make_status("archived",  label="Archivé",    color="gray",   is_final=True),
])

s = find_status(STATUTS, "pending")
# → WorkflowStatus(name='pending', label='En attente', color='yellow', ...)

find_status(STATUTS, "unknown")
# → None
```

#### `WorkflowStatus`

```python
@dataclass
class WorkflowStatus:
    name: str        # snake_case, obligatoire
    label: str = ""  # fallback vers name si vide
    color: str = ""  # libre, ex. "yellow", "#f59e0b"
    is_initial: bool = False
    is_final: bool = False
```

Le constructeur valide et normalise `name` automatiquement. Un nom vide ou contenant des caractères non autorisés lève `WorkflowStatusError`.

#### Fonctions

| Fonction | Comportement |
|---|---|
| `normalize_status_name(value)` | Lowercase, espaces et tirets → `_`. Lève si chars interdits. |
| `validate_status_name(value)` | Normalise puis vérifie le format `[a-z][a-z0-9_]*`. Lève sinon. |
| `make_status(name, ...)` | Crée un `WorkflowStatus` validé. Raccourci du constructeur. |
| `validate_statuses(statuses)` | Vérifie doublons et unicité du statut initial. Retourne la liste. |
| `find_status(statuses, name)` | Retourne le statut correspondant ou `None`. |

#### Règles

- `name` obligatoire, normalisé en snake_case. Seuls lettres, chiffres, espaces et tirets en entrée (espaces et tirets → `_`). Le nom normalisé doit commencer par une lettre.
- `label` optionnel — utilise `name` si absent. `color` optionnel — chaîne libre.
- Au plus un statut `is_initial=True` dans une liste. Plusieurs `is_final=True` autorisés.
- Doublons de `name` dans une liste → `WorkflowStatusError`.

---

### Workflow — Transitions génériques

Les transitions décrivent explicitement les passages autorisés entre statuts. Aucune transition n'est jamais exécutée automatiquement.

#### API

```python
from forge_mvc_workflow import (
    make_status, validate_statuses,
    make_transition, validate_transitions,
    can_transition, get_available_transitions,
)

STATUTS = validate_statuses([
    make_status("draft",     is_initial=True),
    make_status("pending"),
    make_status("published", is_final=True),
    make_status("archived",  is_final=True),
])

TRANSITIONS = validate_transitions(
    [
        make_transition("draft",     "pending"),
        make_transition("pending",   "published"),
        make_transition("pending",   "draft"),
        make_transition("published", "archived"),
    ],
    statuses=STATUTS,
)

can_transition(TRANSITIONS, "draft", "pending")    # True
can_transition(TRANSITIONS, "draft", "published")  # False

available = get_available_transitions(TRANSITIONS, "pending")
# → [WorkflowTransition(from_status='pending', to_status='published'),
#    WorkflowTransition(from_status='pending', to_status='draft')]
```

#### `WorkflowTransition`

```python
@dataclass(frozen=True)
class WorkflowTransition:
    from_status: str  # snake_case, obligatoire
    to_status: str    # snake_case, obligatoire
```

Immuable (`frozen=True`). Le constructeur valide et normalise les deux noms. Une transition vers soi-même lève `WorkflowTransitionError`.

#### Fonctions

| Fonction | Comportement |
|---|---|
| `make_transition(from_status, to_status)` | Crée une `WorkflowTransition` validée. |
| `validate_transitions(transitions, statuses=None)` | Vérifie doublons ; si `statuses` fourni, vérifie l'existence des statuts. |
| `can_transition(transitions, from_name, to_name)` | `True` si la transition est définie, `False` sinon. |
| `get_available_transitions(transitions, from_name)` | Liste toutes les transitions depuis `from_name`. |

#### Règles

- `from_status` et `to_status` obligatoires, normalisés en snake_case.
- Transition vers le même statut (`from == to`) → `WorkflowTransitionError`.
- Doublons `(from, to)` dans une liste → `WorkflowTransitionError`.
- `validate_transitions(..., statuses=STATUTS)` vérifie que tous les noms référencés existent dans `STATUTS`. Sans `statuses`, cette vérification est sautée.
- `can_transition` et `get_available_transitions` normalisent les noms passés en argument.

---

### Workflow — Helpers Jinja

Les helpers d'affichage permettent de rendre un statut dans un template Jinja2 sans accéder à la base de données ni déclencher de transition.

#### Injection automatique

Les helpers sont injectés automatiquement dans tout `Jinja2Renderer` via `make_workflow_jinja_helpers()`. Aucune configuration supplémentaire n'est requise dans les templates.

#### Usage dans un template

```jinja
{# Libellé seul #}
{{ workflow_status_label(demande.statut) }}

{# Classes CSS pour un <span> personnalisé #}
<span class="{{ workflow_status_badge_class(demande.statut) }}">
  {{ workflow_status_label(demande.statut) }}
</span>

{# Badge HTML complet (auto-échappé) #}
{{ workflow_status_badge(demande.statut) }}
```

#### Fonctions

| Fonction | Comportement |
|---|---|
| `workflow_status_label(status)` | `status.label` ou `status.name` si vide. `""` pour `None`. |
| `workflow_status_color(status)` | `status.color` ou `"gray"` si absent ou non listé. |
| `workflow_status_badge_class(status)` | Classes Tailwind complètes pour le badge. |
| `workflow_status_badge(status)` | `Markup` HTML `<span>` prêt à l'emploi, auto-échappé. |
| `make_workflow_jinja_helpers()` | Dict des quatre helpers — injection manuelle possible. |

#### Couleurs prises en charge

| `color` | Palette Tailwind |
|---|---|
| `gray` (défaut) | `bg-gray-100 text-gray-700` |
| `blue` | `bg-blue-100 text-blue-700` |
| `green` | `bg-green-100 text-green-700` |
| `yellow` | `bg-yellow-100 text-yellow-700` |
| `red` | `bg-red-100 text-red-700` |
| `purple` | `bg-purple-100 text-purple-700` |

Couleur absente ou non listée → palette `gray`. Classes de base communes : `inline-flex items-center rounded-full px-2 py-1 text-xs font-medium`.

---

### Workflow — Limites actuelles

La brique Workflow fournit un socle de statuts, de transitions et d'affichage. Forge ne fournit **pas encore** dans ce socle :

- table SQL de workflow (pas de colonne `statut` générée) ;
- migration SQL ;
- historique des changements de statut ;
- auteur et timestamp du changement ;
- intégration CRUD — les listes et formulaires admin n'affichent pas encore le statut ;
- intégration pages publiques — les templates publics n'incluent pas encore le badge de statut ;
- CLI workflow (`forge make:workflow-status`…) ;
- générateur de contrôleur ou de template avec statut ;
- permissions RBAC liées aux transitions (ex. : seul un admin peut publier) ;
- notifications ou emails déclenchés par une transition ;
- logique métier Communes & Séjours (statut de demande, de réservation, etc.).

Ces fonctionnalités peuvent être construites par l'application au-dessus du socle actuel, ou seront traitées dans des tickets ultérieurs.

---

