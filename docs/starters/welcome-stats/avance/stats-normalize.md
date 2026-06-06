# Normaliser une ligne

Objectif : transformer une **ligne brute** de la base en dict propre, prêt à afficher.

**Ce que vous allez apprendre :** en base, les métadonnées sont une **chaîne JSON**.
`normalize_stats_event_row` désérialise les métadonnées et valide la ligne. Une ligne
incomplète ou un JSON invalide lève `StatsAdminError`.

Troisième palier du **niveau avancé** de la progression stats.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-stats` installé (palier « Installation »).

## Ce que ce starter montre

- une ligne brute (métadonnées en chaîne JSON) ;
- `normalize_stats_event_row(row)` → métadonnées en dict ;
- une transformation **pure**.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_stats.normalize_stats_event_row` | Normaliser une ligne brute (métadonnées désérialisées). | [Stats](../../../reference/api.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/stats-normalize` : la ligne brute et sa version normalisée.

## Le contrôleur

```python
# mvc/controllers/stats_normalize_controller.py
from forge_mvc_stats import normalize_stats_event_row

_RAW_ROW = {"id": 1, "name": "page_view", "label": "Vue de page", "category": "navigation",
            "metadata": '{"path": "/", "ref": "home"}', "created_at": "2026-01-01T10:00:00"}

normalized = normalize_stats_event_row(dict(_RAW_ROW))
# normalized["metadata"] est un dict, plus une chaîne
```

### Comprendre ce code

- `list_stats_events` applique déjà cette normalisation ; ce palier l'**isole** pour
  comprendre la transformation `chaîne JSON → dict`.
- La validation **refuse** une ligne incomplète ou un JSON invalide (`StatsAdminError`)
  plutôt que de propager des données douteuses.
- Le résultat est directement utilisable dans une vue ou une API.

## À retenir

- `normalize_stats_event_row` désérialise les métadonnées et valide la ligne.
- C'est la brique sous `list_stats_events`.
- Une ligne douteuse est refusée, pas propagée.

## Après ce starter

Vous avez parcouru toute la progression stats : événement, enregistrement, consultation.

[Bilan du niveau avancé](bilan.md)
