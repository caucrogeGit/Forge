# Appliquer une entité

Objectif : créer une table dans PostgreSQL à partir d'une entité.

**Ce que vous allez apprendre :** sur une base existante, `forge db:apply` applique le schéma SQL de vos entités.

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

Forge crée la table `article` avec le dialecte PostgreSQL (clé primaire `BIGSERIAL`, `CREATE INDEX` séparés).

## 3. Vérifier

```python
import core.database.db as db
print(db.fetch_all("SELECT tablename FROM pg_tables WHERE schemaname='public'", ()))
```

La table `article` apparaît dans la liste.

!!! note "Paramètres traduits"
    Forge écrit ses requêtes avec `?` ; l'adaptateur les traduit en `%s` pour psycopg, de façon transparente.

## Après cette étape

[Bilan du niveau débutant](bilan.md)
