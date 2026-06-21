# La table SQL dans Forge Stats

Ce document décrit la table `forge_stats_events` et la fonction qui produit son SQL de création.

Le fichier de code correspondant est `forge_mvc_stats/schema.py`.

## 1. À quoi sert ce module ?

Les événements ont besoin d'une table pour être stockés.
Ce module expose la **définition SQL** de la table `forge_stats_events`, sans jamais accéder à la base : il retourne une chaîne, vous l'exécutez où vous voulez (migration, script de setup).

## 2. La structure de la table

Nom : `forge_stats_events`

| Colonne | Type | Description |
|---|---|---|
| `id` | `BIGINT UNSIGNED AUTO_INCREMENT` | identifiant technique |
| `name` | `VARCHAR(100) NOT NULL` | nom normalisé de l'événement |
| `label` | `VARCHAR(150) NOT NULL` | libellé humain |
| `category` | `VARCHAR(100) DEFAULT 'general'` | catégorie générique |
| `metadata` | `JSON NULL` | données complémentaires optionnelles |
| `created_at` | `DATETIME DEFAULT CURRENT_TIMESTAMP` | date de création |

Index : `name`, `category`, `created_at`.

## 3. L'API

```python
from forge_mvc_stats import (
    STATS_EVENTS_TABLE,
    STATS_EVENTS_COLUMNS,
    get_stats_events_schema_sql,
)

STATS_EVENTS_TABLE      # "forge_stats_events"
STATS_EVENTS_COLUMNS    # ("id", "name", "label", "category", "metadata", "created_at")

sql = get_stats_events_schema_sql()
# "CREATE TABLE IF NOT EXISTS forge_stats_events ( ... )"
```

`get_stats_events_schema_sql()` retourne la chaîne SQL complète de création, sans accès à la base.

## 4. Contextes d'utilisation

- **Migration** : exécuter `get_stats_events_schema_sql()` au setup du projet.
- **Référence** : `STATS_EVENTS_COLUMNS` pour construire des requêtes cohérentes.

## 5. Voir aussi

- [Les événements](events.md) : ce qui est stocké dans la table.
- [Le tracking](tracking.md) : insérer une ligne dans la table.
- [L'affichage admin](admin.md) : lire la table.
