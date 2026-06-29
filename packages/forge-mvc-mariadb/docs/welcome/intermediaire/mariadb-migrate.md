# Faire évoluer le schéma

Objectif : modifier le schéma MariaDB par migrations.

**Ce que vous allez apprendre :** les commandes `migration:*` du cœur gèrent les évolutions, à l'identique quel que soit le backend.

Premier palier du **niveau intermédiaire**.

## Ce que ce palier montre

- voir l'état des migrations ;
- créer et appliquer une migration.

## 1. État des migrations

```bash
forge migration:status
```

La sortie compare la table `forge_migrations` aux fichiers de migration.

## 2. Créer une migration

```bash
forge migration:make ajout_colonne_resume
```

Forge crée un fichier SQL que vous éditez (le SQL reste visible).

## 3. Appliquer

```bash
forge migration:apply
```

La migration s'exécute avec le compte `DB_ADMIN_*` (DDL), et `forge_migrations` enregistre son passage.

!!! note "Diff de schéma"
    `forge migration:diff` génère un diff SQL entre vos entités et la base, utile pour préparer une migration.

## Après cette étape

[Palier suivant : Les deux comptes](mariadb-creds.md)
