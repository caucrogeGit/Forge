# Appliquer une entité

Objectif : créer une table dans SQL Server à partir d'une entité.

**Ce que vous allez apprendre :** sur la base provisionnée au palier précédent, `forge db:apply` applique le schéma SQL de vos entités.

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
L'option pose une entité minimale, ce qui garde ce palier centré sur SQL Server plutôt que sur la modélisation.

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

Forge crée la table `article` avec le dialecte SQL Server (clé primaire `BIGINT IDENTITY(1,1)`, formes gardées `IF OBJECT_ID(...) IS NULL`).

## 4. Vérifier

```python
import core.database.db as db
print(db.fetch_all("SELECT name FROM sys.tables", ()))
```

La table `article` apparaît dans la liste.

!!! note "Paramètres natifs"
    `pyodbc` utilise nativement les `?` de Forge : aucune traduction n'est nécessaire.

## Après cette étape

[Bilan du niveau débutant](bilan.md)
