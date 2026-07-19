# Appliquer une entité

Objectif : créer une table dans SQL Server à partir d'une entité.

**Ce que vous allez apprendre :** sur la base provisionnée au palier précédent, `forge db:apply` applique le schéma SQL de vos entités.

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

Forge crée la table `article` avec le dialecte SQL Server (clé primaire `BIGINT IDENTITY(1,1)`, formes gardées `IF OBJECT_ID(...) IS NULL`).

## 3. Vérifier

```python
import core.database.db as db
print(db.fetch_all("SELECT name FROM sys.tables", ()))
```

La table `article` apparaît dans la liste.

!!! note "Paramètres natifs"
    `pyodbc` utilise nativement les `?` de Forge : aucune traduction n'est nécessaire.

## Après cette étape

[Bilan du niveau débutant](bilan.md)
