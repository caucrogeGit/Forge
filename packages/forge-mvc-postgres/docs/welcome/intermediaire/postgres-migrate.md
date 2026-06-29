# Faire évoluer le schéma

Objectif : modifier le schéma PostgreSQL par migrations.

**Ce que vous allez apprendre :** les commandes `migration:*` du cœur fonctionnent sur PostgreSQL, sur une base déjà préparée.

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

La migration s'exécute sur PostgreSQL ; `forge_migrations` enregistre son passage.

!!! note "Même API que les autres backends"
    Les commandes `migration:*` sont celles du cœur ; le flux ne change pas selon le backend.

## Après cette étape

[Palier suivant : État du support Alpha](postgres-status.md)
