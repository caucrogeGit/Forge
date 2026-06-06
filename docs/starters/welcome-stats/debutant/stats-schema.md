# Le schéma SQL

Objectif : lire le **schéma SQL** exact de la table des événements — Forge garde le SQL
visible.

**Ce que vous allez apprendre :** `get_stats_events_schema_sql` retourne le
`CREATE TABLE` de `forge_stats_events`. Fidèle à la charte (principe 5), Forge Stats
n'a **pas d'ORM** : on lit le schéma réel.

Troisième palier du **niveau débutant** de la progression stats.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-stats` installé (palier « Installation »).

## Ce que ce starter montre

- `get_stats_events_schema_sql()` → le `CREATE TABLE` ;
- la liste des colonnes ;
- une transformation **pure** (on montre le SQL, on ne l'exécute pas).

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_stats.get_stats_events_schema_sql` | Le `CREATE TABLE` de `forge_stats_events`. | [Stats](../../../reference/api.md) |
| `forge_mvc_stats.STATS_EVENTS_COLUMNS` | Les colonnes de la table. | [Stats](../../../reference/api.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/stats-schema` : le `CREATE TABLE` exact s'affiche.

## Le contrôleur

```python
# mvc/controllers/stats_schema_controller.py
from forge_mvc_stats import STATS_EVENTS_COLUMNS, STATS_EVENTS_TABLE, get_stats_events_schema_sql


class StatsSchemaController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render("stats_schema/index.html", context={
            "table": STATS_EVENTS_TABLE,
            "columns": list(STATS_EVENTS_COLUMNS),
            "schema_sql": get_stats_events_schema_sql(),
        }, request=request)
```

### Comprendre ce code

- On **lit** le schéma réel qui sera créé en base : aucune abstraction ne le cache
  (charte principe 5, « garder SQL visible »).
- Exposer le SQL plutôt qu'un ORM rend le comportement auditable et prévisible.
- L'application applique ce `CREATE TABLE` une fois (migration), puis Forge Stats y écrit.

## À retenir

- `get_stats_events_schema_sql` montre le `CREATE TABLE` exact.
- SQL visible, pas d'ORM (charte principe 5).
- Le schéma est auditable avant toute exécution.

## Après ce starter

Vous avez les briques (événement, schéma). La suite (intermédiaire) : **enregistrer**.

[Bilan du niveau débutant](bilan.md)
