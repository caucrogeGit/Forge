# Les événements dans Forge Stats

Ce document décrit l'objet `StatsEvent` et la validation des noms d'événements.

Le fichier de code correspondant est `forge_mvc_stats/events.py`.

## 1. À quoi sert ce module ?

Un événement statistique est une chose mesurable : une vue de page, un clic, une soumission de formulaire.
Ce module définit le **contrat** d'un événement : son nom, son libellé, sa catégorie et ses métadonnées, ainsi que la normalisation et la validation du nom.

Il ne stocke rien et ne trace rien : il pose seulement la structure.

## 2. L'objet `StatsEvent`

```python
@dataclass(frozen=True)
class StatsEvent:
    name: str                     # snake_case, obligatoire
    label: str = ""               # retombe sur name si vide
    category: str = "general"     # retombe sur "general" si vide
    metadata: dict[str, Any] = field(default_factory=dict)
```

Il est **immuable** (`frozen=True`).
Le constructeur valide et normalise `name` ; `metadata` doit être un dictionnaire (`None` devient `{}`).

## 3. Créer et valider

```python
from forge_mvc_stats import KIND_PAGE_VIEW, make_event, validate_event

e = make_event("contact", label="Page contact", category="traffic",
               metadata={"path": "/contact"}, kind=KIND_PAGE_VIEW)
validate_event(e)   # retourne e
```

Le **nom** dit quelle page ou quelle action, le **type** dit laquelle des deux.
Cette page employait `"page_view"` comme nom, convention d'avant le champ `kind` : l'événement était alors compté comme une action, et l'agrégation par type devenait fausse.

| Fonction | Comportement |
|---|---|
| `make_event(name, ..., kind)` | crée un `StatsEvent` validé ; `kind` vaut `action` par défaut |
| `validate_event(event)` | vérifie que `event` est un `StatsEvent` ; retourne l'événement ou lève |
| `normalize_event_name(value)` | minuscule, espaces et tirets vers `_` ; lève si caractères interdits |
| `validate_event_name(value)` | normalise puis vérifie le format `[a-z][a-z0-9_]*` |

## 4. Les noms d'événements

Les noms sont de simples chaînes `snake_case` **définies par l'application**.
Forge ne fournit pas de liste prédéfinie, conformément au principe 1 (le framework n'est pas l'application).

Noms courants à utiliser directement : `"accueil"`, `"contact_click"`, `"form_submit"`, `"download_click"`, `"external_link_click"`, `"media_view"`.

`"page_view"` ne figure plus dans cette liste, et ce n'est pas un oubli.
Une consultation de page se déclare par `kind=KIND_PAGE_VIEW`, le nom restant celui de la page consultée : sans quoi toutes les pages se comptent sous un seul nom, et l'axe qui répond « quelles pages reviennent le plus » ne répond plus rien.

## 5. Les erreurs

`StatsEventError` est levée pour un nom invalide ou une métadonnée non valide.

## 6. Contextes d'utilisation

- **Déclaration** : `make_event(...)` au moment de mesurer quelque chose.
- **Tracking** : passez l'événement à `track_event` (voir [tracking](tracking.md)).

## 7. Voir aussi

- [Le tracking](tracking.md) : enregistrer un événement en base.
- [La table SQL](schema.md) : où sont stockés les événements.
