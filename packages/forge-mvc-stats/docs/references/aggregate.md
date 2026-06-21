# L'agrégation dans Forge Stats

Ce document décrit le comptage des événements groupés par une dimension.

Le fichier de code correspondant est `forge_mvc_stats/aggregate.py`.

## 1. À quoi sert ce module ?

Au-delà du journal brut, on veut souvent un **compte** : combien d'événements par catégorie, par nom, depuis telle date.
Ce module (ADR-037) agrège les événements groupés par une dimension.

## 2. Compter les événements

```python
from forge_mvc_stats import count_stats_events

totaux = count_stats_events(my_fetch_all, "category", since="2026-01-01T00:00:00Z")
# [{"bucket": "traffic", "total": 128}, {"bucket": "compte", "total": 17}]
```

## 3. La sécurité de la dimension

La dimension `group_by` est résolue par une **liste blanche** (`name` ou `category`) vers la colonne SQL : elle n'est jamais interpolée depuis une chaîne libre, donc aucune injection n'est possible.
Les filtres `name`, `category` et `since` (timestamp ISO sur `created_at >= ?`) sont des paramètres liés.

## 4. L'API

| Fonction | Comportement |
|---|---|
| `get_stats_counts_sql(group_by, name, category, since)` | le `SELECT <col> AS bucket, COUNT(*) AS total FROM forge_stats_events WHERE 1 = 1 [filtres] GROUP BY <col> ORDER BY total DESC, bucket ASC` ; `group_by` doit valoir `name` ou `category`, sinon `StatsAggregateError` |
| `prepare_stats_counts_params(group_by, name, category, since)` | valide et retourne le tuple de paramètres liés |
| `normalize_stats_count_row(row)` | normalise une ligne en `{"bucket": ..., "total": int}` |
| `count_stats_events(fetch_all, group_by, name, category, since)` | orchestre la requête et retourne la liste des comptes |

## 5. Les erreurs

`StatsAggregateError` est levée si `group_by` n'est pas dans la liste blanche (`name` ou `category`).

## 6. Contextes d'utilisation

- **Tableau de bord** : `count_stats_events(fetch_all, "category")` pour un récapitulatif.
- **Tendance** : `since` pour borner la période.

## 7. Voir aussi

- [L'affichage admin](admin.md) : lister plutôt que compter.
- [Les événements](events.md) : la matière comptée.
