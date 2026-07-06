# Les statuts dans Forge Workflow

Ce document décrit comment `forge_mvc_workflow` modélise et valide les statuts d'une entité.

Le fichier de code correspondant est `forge_mvc_workflow/status.py`.

## 1. À quoi sert ce module ?

Un statut décrit l'état d'une entité applicative : `draft`, `pending`, `published`, `archived`… Ce module fournit l'objet `WorkflowStatus` et les fonctions pour créer et valider un jeu de statuts cohérent.

Les statuts restent **génériques** : aucun métier n'est imposé, c'est l'application qui choisit ses états.

## 2. Déclarer des statuts

```python
from forge_mvc_workflow import make_status, validate_statuses, find_status

STATUTS = validate_statuses([
    make_status("draft",     label="Brouillon",  color="gray",   is_initial=True),
    make_status("pending",   label="En attente", color="yellow"),
    make_status("published", label="Publié",     color="green",  is_final=True),
    make_status("archived",  label="Archivé",    color="gray",   is_final=True),
])

find_status(STATUTS, "pending")   # WorkflowStatus(name='pending', ...)
find_status(STATUTS, "unknown")   # None
```

## 3. L'objet `WorkflowStatus`

```python
@dataclass
class WorkflowStatus:
    name: str         # snake_case, obligatoire
    label: str = ""   # retombe sur name si vide
    color: str = ""   # libre, ex. "yellow", "#f59e0b"
    is_initial: bool = False
    is_final: bool = False
```

Le constructeur valide et **normalise** `name` automatiquement ; un nom vide ou contenant des caractères interdits lève `WorkflowStatusError`.

## 4. Les fonctions

| Fonction | Comportement |
|---|---|
| `make_status(name, ...)` | crée un `WorkflowStatus` validé (raccourci du constructeur) |
| `validate_statuses(statuses)` | vérifie doublons et unicité du statut initial ; retourne la liste |
| `find_status(statuses, name)` | retourne le statut correspondant, ou `None` |
| `normalize_status_name(value)` | minuscule, espaces et tirets vers `_` ; lève si caractères interdits |
| `validate_status_name(value)` | normalise puis vérifie le format `[a-z][a-z0-9_]*` |

## 5. Les règles

- `name` est obligatoire et normalisé en snake_case : lettres, chiffres, espaces et tirets en entrée (espaces et tirets deviennent `_`), et le nom doit commencer par une lettre.
- `label` est optionnel (retombe sur `name`) ; `color` est une chaîne libre.
- Au plus **un** statut `is_initial=True` par liste ; plusieurs `is_final=True` sont autorisés.
- Un doublon de `name` dans une liste lève `WorkflowStatusError`.

## 6. Les erreurs

`WorkflowStatusError` est levée pour un nom invalide, un doublon de statut, ou plusieurs statuts initiaux.

## 7. Contextes d'utilisation

- **Déclaration** : `validate_statuses([...])` une fois, au chargement de l'application.
- **Lecture** : `find_status(STATUTS, name)` pour retrouver un statut.

## 8. Voir aussi

- [Les transitions](transitions.md) : les passages autorisés entre statuts.
- [Les helpers Jinja](jinja.md) : afficher un statut dans un gabarit.
