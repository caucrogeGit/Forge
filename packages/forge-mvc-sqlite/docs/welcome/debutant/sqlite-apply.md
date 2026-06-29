# Appliquer une entité

Objectif : créer une table dans la base SQLite à partir d'une entité.

**Ce que vous allez apprendre :** une fois la base créée, `forge db:apply` applique le schéma SQL de vos entités.

Deuxième palier du **niveau débutant**.

## Ce que ce palier montre

- générer une entité et son CRUD ;
- appliquer le schéma avec `forge db:apply`.

## 1. Générer une entité

```bash
forge make:crud article
```

Le générateur produit l'entité, le contrôleur et les vues (voir la doc du cœur pour le détail).

## 2. Appliquer le schéma

```bash
forge db:apply
```

Forge crée la table `article` dans le fichier SQLite, avec le dialecte SQLite (clé primaire `INTEGER PRIMARY KEY AUTOINCREMENT`).

## 3. Vérifier

```python
import core.database.db as db
print(db.fetch_all("SELECT name FROM sqlite_master WHERE type='table'", ()))
```

La table `article` apparaît dans la liste.

## Après cette étape

[Bilan du niveau débutant](bilan.md)
