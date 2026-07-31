# Appliquer une entité

Objectif : créer une table dans MariaDB à partir d'une entité.

**Ce que vous allez apprendre :** une fois la base provisionnée, `forge db:apply` applique le schéma SQL de vos entités (avec le compte admin).

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
L'option pose une entité minimale, ce qui garde ce palier centré sur MariaDB plutôt que sur la modélisation.

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
