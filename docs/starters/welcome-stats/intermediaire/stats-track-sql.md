# Le SQL d'insertion

Objectif : **voir** le SQL d'insertion d'un événement avant de l'exécuter.

**Ce que vous allez apprendre :** `get_track_event_sql` retourne l'`INSERT` paramétré ;
`prepare_track_event_values` retourne le tuple de valeurs d'un événement (métadonnées
sérialisées en JSON). SQL visible, requête paramétrée (anti-injection).

Premier palier du **niveau intermédiaire** de la progression stats.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-stats` installé (palier « Installation »).

## Ce que ce starter montre

- `get_track_event_sql()` → l'`INSERT` ;
- `prepare_track_event_values(event)` → le tuple de valeurs ;
- une transformation **pure** (on montre, on n'exécute pas).

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_stats.get_track_event_sql` | L'`INSERT` paramétré. | [Stats](../../../reference/api.md) |
| `forge_mvc_stats.prepare_track_event_values` | Le tuple de valeurs d'un événement. | [Stats](../../../reference/api.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/stats-track-sql` : l'`INSERT` et ses valeurs.

## Le contrôleur

```python
# mvc/controllers/stats_track_sql_controller.py
from forge_mvc_stats import get_track_event_sql, make_event, prepare_track_event_values

event = make_event("page_view", "Vue de page", "navigation", {"path": "/"})
sql = get_track_event_sql()
values = prepare_track_event_values(event)   # ('page_view', 'Vue de page', 'navigation', '{"path": "/"}')
```

### Comprendre ce code

- Le SQL est **paramétré** (`?`) : les valeurs ne sont jamais concaténées (anti-injection).
- Les **métadonnées** (dict) sont sérialisées en JSON pour tenir dans une colonne texte.
- Voir le SQL avant de l'exécuter rend le comportement transparent (SQL visible).

## À retenir

- `get_track_event_sql` + `prepare_track_event_values` = SQL + valeurs, sans exécuter.
- Requête paramétrée, métadonnées en JSON.
- Transparence : on lit ce qui sera écrit.

## Après ce starter

La suite : **exécuter** cet enregistrement.

[Enregistrer un événement](stats-track.md)
