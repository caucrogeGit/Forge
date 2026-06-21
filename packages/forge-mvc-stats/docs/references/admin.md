# L'affichage admin dans Forge Stats

Ce document décrit la consultation des événements enregistrés.

Le fichier de code correspondant est `forge_mvc_stats/admin.py`.

## 1. À quoi sert ce module ?

Une fois les événements enregistrés, on veut les **lister** : les derniers, ou ceux d'un nom ou d'une catégorie.
Ce module fournit cette consultation. Le développeur **injecte** la fonction `fetch_all` : Forge ne lit jamais la base automatiquement.

Pas de dashboard graphique, pas de middleware, pas de cookie de session.

## 2. Lister les événements

```python
from forge_mvc_stats import list_stats_events

def my_fetch_all(sql, params):
    cursor.execute(sql, params)
    return [dict(row) for row in cursor.fetchall()]

events = list_stats_events(my_fetch_all)                                  # 50 derniers
page_views = list_stats_events(my_fetch_all, name="page_view", limit=100) # par nom
traffic = list_stats_events(my_fetch_all, category="traffic")            # par catégorie
```

Chaque entrée est un `dict` normalisé (`id`, `name`, `label`, `category`, `metadata` toujours un dict, `created_at`).

## 3. L'API

| Fonction | Comportement |
|---|---|
| `get_stats_events_admin_sql(name, category, limit)` | le `SELECT ... FROM forge_stats_events WHERE 1 = 1 [AND name = ?] [AND category = ?] ORDER BY created_at DESC, id DESC LIMIT ?` |
| `prepare_stats_events_admin_params(name, category, limit)` | valide et retourne le tuple de paramètres ; `name` normalisé, `limit` borné à 500 |
| `normalize_stats_event_row(row)` | désérialise `metadata`, `None`/`""` vers `{}` ; lève `StatsAdminError` si colonne manquante ou JSON invalide |
| `list_stats_events(fetch_all, name, category, limit)` | orchestre la requête et retourne une liste de dicts normalisés |

## 4. Les erreurs

`StatsAdminError` est levée si une ligne est mal formée (colonne manquante, JSON `metadata` invalide).

## 5. Contextes d'utilisation

- **Page admin** : `list_stats_events(fetch_all, ...)` pour un tableau d'événements.
- **Filtre** : `name` et `category` pour cibler ; `limit` borné à 500.

## 6. Voir aussi

- [Le tracking](tracking.md) : alimente ce que l'admin lit.
- [L'agrégation](aggregate.md) : compter plutôt que lister.
