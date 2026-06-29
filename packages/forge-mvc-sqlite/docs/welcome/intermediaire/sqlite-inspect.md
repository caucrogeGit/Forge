# Inspecter la base

Objectif : regarder ce que SQLite a réellement créé.

**Ce que vous allez apprendre :** comme la base est un fichier, on peut l'inspecter directement, ce qui est pratique en développement.

Deuxième palier du **niveau intermédiaire**.

## Ce que ce palier montre

- lister les tables ;
- décrire une table avec `PRAGMA`.

## 1. Lister les tables

```python
import core.database.db as db
tables = db.fetch_all("SELECT name FROM sqlite_master WHERE type='table'", ())
print([t["name"] for t in tables])
```

## 2. Décrire une table

```python
cols = db.fetch_all("PRAGMA table_info(article)", ())
for c in cols:
    print(c["name"], c["type"])
```

`PRAGMA table_info` est l'équivalent SQLite de l'introspection de colonnes ; Forge l'utilise pour le diff de migrations.

## 3. Avec un outil externe

Le fichier `DB_NAME` s'ouvre aussi avec n'importe quel client SQLite (ligne de commande `sqlite3`, extension d'éditeur), utile pour vérifier les données à la main.

## Après cette étape

[Bilan du niveau intermédiaire](bilan.md)
