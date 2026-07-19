# Faire évoluer le schéma

Objectif : modifier le schéma SQL Server par migrations.

**Ce que vous allez apprendre :** les commandes `migration:*` du cœur fonctionnent sur SQL Server, sur la base provisionnée par `db:init`.

Premier palier du **niveau intermédiaire**.

## Ce que ce palier montre

- voir l'état des migrations ;
- créer et appliquer une migration.

## 1. État des migrations

```bash
forge migration:status
```

Forge compare la table `forge_migrations` aux fichiers de migration.

## 2. Créer une migration

```bash
forge migration:make ajout_colonne_resume
```

Le fichier SQL généré est éditable (le SQL reste visible).

## 3. Appliquer

```bash
forge migration:apply
```

La migration s'exécute sur SQL Server ; `forge_migrations` enregistre son passage.

!!! note "Formes gardées"
    SQL Server n'a pas `IF NOT EXISTS` pour les tables/index : Forge émet des formes gardées (`IF OBJECT_ID(...) IS NULL`, `IF NOT EXISTS (SELECT ... sys.indexes ...)`).

## Après cette étape

[Palier suivant : État du support](mssql-status.md)
