# Normaliser une ligne

Objectif : transformer une **ligne brute** de la base en dict propre, prêt à afficher.

**Ce que vous allez apprendre :** en base, les métadonnées sont une **chaîne JSON**.
`normalize_stats_event_row` désérialise les métadonnées et valide la ligne.
Une ligne incomplète ou un JSON invalide lève `StatsAdminError`.

Troisième palier du **niveau avancé** de la progression stats.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-stats` installé.

## Ce que ce starter montre

- une ligne brute (métadonnées en chaîne JSON) ;
- `normalize_stats_event_row(row)` → métadonnées en dict ;
- une transformation **pure**.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_stats.normalize_stats_event_row` | Normaliser une ligne brute (métadonnées désérialisées). | Stats |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/stats-normalize` : la ligne brute et sa version normalisée.

## Le contrôleur

```python
# mvc/controllers/stats_normalize_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_stats import normalize_stats_event_row

_RAW_ROW = {
    "id": 1,
    "name": "page_view",
    "label": "Vue de page",
    "category": "navigation",
    "metadata": '{"path": "/", "ref": "home"}',
    "created_at": "2026-01-01T10:00:00",
}


class StatsNormalizeController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        normalized = normalize_stats_event_row(dict(_RAW_ROW))
        # normalized["metadata"] est un dict, plus une chaîne
        return BaseController.render(
            "stats_normalize/index.html",
            context={
                "raw_metadata": _RAW_ROW["metadata"],
                "normalized_metadata": normalized["metadata"],
                "name": normalized["name"],
            },
            request=request,
        )
```

### Comprendre ce code

- `list_stats_events` applique déjà cette normalisation ; ce palier l'**isole** pour comprendre la transformation `chaîne JSON → dict`.
- La validation **refuse** une ligne incomplète ou un JSON invalide (`StatsAdminError`) plutôt que de propager des données douteuses.
- Le résultat est directement utilisable dans une vue ou une API.

## La vue

```html
<!-- mvc/views/stats_normalize/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Normaliser une ligne - Forge</title>
</head>
<body>
  <h1>Normaliser une ligne</h1>

  <p>Événement : <code>{{ name }}</code></p>

  <ul>
    <li>Métadonnées brutes (chaîne JSON, telles qu'en base) : <code>{{ raw_metadata }}</code></li>
    <li>Métadonnées normalisées (dict, prêtes à afficher) : <code>{{ normalized_metadata }}</code></li>
  </ul>

  <p>La normalisation désérialise le JSON et valide la ligne : un JSON invalide ou une
  colonne manquante est refusé (<code>StatsAdminError</code>).</p>
</body>
</html>
```

## La route

Dans `mvc/routes/__init__.py`, ajoutez l'import en tête de fichier et la route dans le groupe public.

```python
# mvc/routes/__init__.py
from mvc.controllers.stats_normalize_controller import StatsNormalizeController

with router.group("", public=True) as public:
    public.add("GET", "/stats-normalize", StatsNormalizeController.index, name="stats_normalize_index")
```

## À retenir

- `normalize_stats_event_row` désérialise les métadonnées et valide la ligne.
- C'est la brique sous `list_stats_events`.
- Une ligne douteuse est refusée, pas propagée.

## Après ce starter

Vous avez parcouru toute la progression stats : événement, enregistrement, consultation.

[Suivant : compter sans ficher](stats-vie-privee.md)
