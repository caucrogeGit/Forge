# Appliquer une entité

Objectif : créer une table dans MariaDB à partir d'une entité.

**Ce que vous allez apprendre :** une fois la base provisionnée, `forge db:apply` applique le schéma SQL de vos entités (avec le compte admin).

Deuxième palier du **niveau débutant**.

## Ce que ce palier montre

- générer une entité et son CRUD ;
- appliquer le schéma avec `forge db:apply`.

## 1. Générer une entité

```bash
forge make:crud article
```

## 2. Appliquer le schéma

```bash
forge db:apply
```

Forge crée la table `article` avec le dialecte MariaDB (`INT AUTO_INCREMENT`, `ENGINE=InnoDB DEFAULT CHARSET=utf8mb4`).

## 3. Vérifier

```python
import core.database.db as db
print(db.fetch_all("SHOW TABLES", ()))
```

La table `article` apparaît dans la liste.

!!! note "DDL avec le compte admin"
    `db:apply` et les migrations modifient la structure : ils utilisent `DB_ADMIN_*`, pas le compte runtime (ADR-033).

## Après cette étape

[Bilan du niveau débutant](bilan.md)
