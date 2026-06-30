# Nom d'événement

Objectif : comprendre le **nom d'événement** et comment Forge le normalise et le valide.

**Ce que vous allez apprendre :** un nom est un identifiant `snake_case`.
`normalize_event_name` le met en forme (« Page View » → `page_view`) ;
`validate_event_name` refuse les caractères interdits (un point, par exemple).

Deuxième palier du **niveau débutant** de la progression stats.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-stats` installé (palier « Installation »).

## Ce que ce starter montre

- `normalize_event_name(name)` → forme `snake_case` ;
- `validate_event_name(name)` → validité (ou `StatsEventError`) ;
- une transformation **pure**.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_stats.normalize_event_name` | Normaliser un nom d'événement. | Stats |
| `forge_mvc_stats.validate_event_name` | Refuser un nom invalide. | Stats |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/stats-event?name=Page View` → `page_view`.

## Le contrôleur

```python
# mvc/controllers/stats_event_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_stats import StatsEventError, normalize_event_name, validate_event_name

_DEMO_NAME = "Page View"


def _event_view(raw: str) -> dict:
    try:
        normalized = normalize_event_name(raw)
        validate_event_name(raw)
        return {"input": raw, "normalized": normalized, "valid": True, "error": None}
    except StatsEventError as exc:
        return {"input": raw, "normalized": None, "valid": False, "error": str(exc)}


class StatsEventController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        raw = request.query("name") or _DEMO_NAME
        return BaseController.render(
            "stats_event/index.html", context=_event_view(raw), request=request
        )
```

### Comprendre ce code

- Le nom `snake_case` est l'identifiant stable de l'événement ; le libellé reste
  libre pour l'affichage.
- Normaliser **avant** de comparer/agréger évite de disperser un même événement sous
  plusieurs noms.
- Un caractère interdit (point, accent) lève `StatsEventError`.

## La vue

```html
<!-- mvc/views/stats_event/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Nom d'événement - Forge</title>
</head>
<body>
  <h1>Nom d'événement</h1>

  <form method="get" action="/stats-event">
    <input type="text" name="name" value="{{ input }}" size="40">
    <button type="submit">Normaliser & valider</button>
  </form>

  <ul>
    <li>Entrée : <code>{{ input }}</code></li>
    <li>Normalisé : <code>{{ normalized }}</code></li>
    <li>Valide : <strong>{% if valid %}oui{% else %}non{% endif %}</strong>{% if error %} - {{ error }}{% endif %}</li>
  </ul>

  <p>Essayez <code>Page View</code> (→ <code>page_view</code>) puis <code>page.view</code>
  (refusé : le point n'est pas autorisé).</p>
</body>
</html>
```

## La route

Dans `mvc/routes.py`, ajoutez l'import en tête de fichier et la route dans le groupe public.

```python
# mvc/routes.py
from mvc.controllers.stats_event_controller import StatsEventController

with router.group("", public=True) as public:
    public.add("GET", "/stats-event", StatsEventController.index, name="stats_event_index")
```

## À retenir

- Un nom d'événement est un identifiant `snake_case` normalisé.
- Cohérence des noms = agrégats fiables.
- Normaliser puis valider.

## Après ce starter

La suite : le **schéma SQL** de la table des événements.

[Le schéma SQL](stats-schema.md)
