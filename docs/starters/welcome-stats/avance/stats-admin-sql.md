# Le SQL de consultation

Objectif : **voir** le SQL de lecture filtrable des événements.

**Ce que vous allez apprendre :** `get_stats_events_admin_sql` construit un `SELECT`
filtrable (nom, catégorie, limite) ; `prepare_stats_events_admin_params` fournit ses
paramètres liés. SQL visible, filtres paramétrés.

Premier palier du **niveau avancé** de la progression stats.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-stats` installé (palier « Installation »).

## Ce que ce starter montre

- un filtre optionnel par catégorie ;
- `get_stats_events_admin_sql` → le `SELECT` ;
- `prepare_stats_events_admin_params` → ses paramètres.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_stats.get_stats_events_admin_sql` | Le `SELECT` filtrable. | [Stats](../../../reference/api.md) |
| `forge_mvc_stats.prepare_stats_events_admin_params` | Les paramètres du `SELECT`. | [Stats](../../../reference/api.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/stats-admin-sql?category=navigation` : le `SELECT` adapté.

## Le contrôleur

```python
# mvc/controllers/stats_admin_sql_controller.py
from forge_mvc_stats import get_stats_events_admin_sql, prepare_stats_events_admin_params

category = request.param("category") or None
sql = get_stats_events_admin_sql(category=category, limit=20)
params = prepare_stats_events_admin_params(category=category, limit=20)
```

### Comprendre ce code

- Le SQL **s'adapte aux filtres** fournis (nom, catégorie) tout en restant paramétré.
- Voir le `SELECT` avant de l'exécuter garde le comportement transparent (SQL visible).
- La **limite** protège contre les lectures non bornées.

## À retenir

- `get_stats_events_admin_sql` + params = le `SELECT` filtrable, sans exécuter.
- Filtres paramétrés, limite par défaut.
- SQL visible aussi en lecture.

## Après ce starter

La suite : **exécuter** cette lecture et obtenir des événements.

[Lister les événements](stats-list.md)
