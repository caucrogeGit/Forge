# Appliquer une entité

Objectif : créer une table dans PostgreSQL à partir d'une entité.

**Ce que vous allez apprendre :** sur une base existante, `forge db:apply` applique le schéma SQL de vos entités.

Deuxième palier du **niveau débutant**.

## Ce que ce palier montre

- déclarer une entité ;
- en générer le CRUD ;
- appliquer le schéma avec `forge db:apply`.

## 1. Déclarer l'entité

```bash
forge make:entity Article --no-input
```

`make:entity` produit le contrat `mvc/entities/article/article.json`, son SQL et son modèle Python.

Sans `--no-input`, la commande vous interroge sur la table et ses champs.
L'option pose une entité minimale, ce qui garde ce palier centré sur PostgreSQL plutôt que sur la modélisation.

## 2. Générer le CRUD

```bash
forge make:crud article
```

Le générateur produit le contrôleur et les vues à partir du contrat de l'étape précédente.
Il ne crée pas l'entité, et refuse si elle n'existe pas.

## 3. Appliquer le schéma

```bash
forge db:apply
```

Forge crée la table `article` avec le dialecte PostgreSQL (clé primaire `BIGSERIAL`, `CREATE INDEX` séparés).

## 4. Vérifier

```python
import core.database.db as db
print(db.fetch_all("SELECT tablename FROM pg_tables WHERE schemaname='public'", ()))
```

La table `article` apparaît dans la liste.

!!! note "Paramètres traduits"
    Forge écrit ses requêtes avec `?` ; l'adaptateur les traduit en `%s` pour psycopg, de façon transparente.

## Après cette étape

[Bilan du niveau débutant](bilan.md)
