# Les helpers SQL dans Forge

Ce document décrit les fonctions d'exécution SQL explicites du cœur.

Le fichier de code correspondant est `core/database/db.py`.

## 1. À quoi sert ce module ?

Forge **garde le SQL visible** (principe 5) : pas d'ORM, vous écrivez vos requêtes.
Ce module fournit quatre helpers pour les exécuter, en paramétrant toujours les valeurs (pas d'interpolation de chaîne).

## 2. L'API

```python
from core.database.db import fetch_one, fetch_all, execute, insert

rows = fetch_all("SELECT id, name FROM categories ORDER BY name")
row  = fetch_one("SELECT * FROM article WHERE id = ?", (article_id,))
new_id = insert("INSERT INTO article (title) VALUES (?)", (title,))
n = execute("UPDATE article SET title = ? WHERE id = ?", (title, article_id))
```

| Fonction | Rôle | Retour |
|---|---|---|
| `fetch_one(sql, params=(), *, tx=None)` | un SELECT, première ligne | `dict` ou `None` |
| `fetch_all(sql, params=(), *, tx=None)` | un SELECT, toutes les lignes | `list[dict]` |
| `execute(sql, params=(), *, tx=None)` | une requête (UPDATE/DELETE…) | `rowcount` |
| `insert(sql, params=(), *, tx=None)` | une insertion | `lastrowid` |

## 3. Les paramètres liés

Les valeurs passent **toujours** par `params` (placeholders `?`), jamais par interpolation : c'est la défense contre l'injection SQL.

## 4. Les transactions

Le paramètre `tx` rattache la requête à une [transaction explicite](transaction.md) : les helpers écrivent **dans** la transaction sans committer eux-mêmes.

## 5. Contextes d'utilisation

- **Lecture** : `fetch_one` / `fetch_all`.
- **Écriture** : `insert` (récupère l'id), `execute` (rowcount).
- **Atomique** : passer `tx=tx` dans un bloc `with transaction()`.

## 6. Voir aussi

- [Les transactions](transaction.md) : grouper des écritures atomiques.
- [Le pool de connexions](connection.md) : la connexion sous-jacente.
- [Le chargeur de requêtes SQL](sql_loader.md).
