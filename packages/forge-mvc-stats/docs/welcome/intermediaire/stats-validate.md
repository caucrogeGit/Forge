# Valider un événement

Objectif : refuser un événement mal formé **avant** de l'écrire en base.

**Ce que vous allez apprendre :** `make_event` valide à la construction et
`validate_event` re-vérifie un événement existant. Un nom invalide lève
`StatsEventError` — on refuse avant toute écriture.

Troisième palier du **niveau intermédiaire** de la progression stats.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-stats` installé (palier « Installation »).

## Ce que ce starter montre

- `make_event(name, ...)` qui valide à la construction ;
- `validate_event(event)` qui re-vérifie ;
- la capture de `StatsEventError`.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_stats.make_event` | Construire (et valider) un événement. | [Stats](../../../reference/api.md) |
| `forge_mvc_stats.validate_event` | Re-vérifier un événement existant. | [Stats](../../../reference/api.md) |
| `forge_mvc_stats.StatsEventError` | Erreur si l'événement est invalide. | [Stats](../../../reference/api.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/stats-validate?name=page_view` (valide) puis
`?name=page.view` (refusé).

## Le contrôleur

```python
# mvc/controllers/stats_validate_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_stats import StatsEventError, make_event, validate_event

_DEMO_NAME = "page_view"


def _validate_view(name: str) -> dict:
    try:
        event = make_event(name, "Démo", "general", {})
        validate_event(event)
        return {"input": name, "valid": True, "name": event.name, "error": None}
    except StatsEventError as exc:
        return {"input": name, "valid": False, "name": None, "error": str(exc)}


class StatsValidateController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        name = request.query("name") or _DEMO_NAME
        return BaseController.render(
            "stats_validate/index.html", context=_validate_view(name), request=request
        )
```

### Comprendre ce code

- La validation se fait **à la construction** : un `make_event` invalide lève
  immédiatement, avant tout SQL.
- `validate_event` permet de re-vérifier un événement reçu d'ailleurs (désérialisé,
  par exemple).
- Refuser tôt = pas de données invalides en base.

## La vue

```html
<!-- mvc/views/stats_validate/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Valider un événement — Forge</title>
</head>
<body>
  <h1>Valider un événement</h1>

  <form method="get" action="/stats-validate">
    <input type="text" name="name" value="{{ input }}" size="40">
    <button type="submit">Construire & valider</button>
  </form>

  {% if valid %}
  <p data-level="success">✓ Événement valide : <code>{{ name }}</code>.</p>
  {% else %}
  <p data-level="error">✗ Refusé : {{ error }}</p>
  {% endif %}

  <p>Essayez <code>page_view</code> (valide) puis <code>page.view</code> (refusé avant
  toute écriture).</p>
</body>
</html>
```

## La route

Dans `mvc/routes.py`, ajoutez l'import en tête de fichier et la route dans le groupe public.

```python
# mvc/routes.py
from mvc.controllers.stats_validate_controller import StatsValidateController

with router.group("", public=True) as public:
    public.add("GET", "/stats-validate", StatsValidateController.index, name="stats_validate_index")
```

## À retenir

- Un événement est validé **avant** d'être écrit.
- `make_event` lève à la construction ; `validate_event` re-vérifie.
- `StatsEventError` porte la cause du refus.

## Après ce starter

Vous savez écrire des événements valides. La suite (avancé) : les **consulter**.

[Bilan du niveau intermédiaire](bilan.md)
