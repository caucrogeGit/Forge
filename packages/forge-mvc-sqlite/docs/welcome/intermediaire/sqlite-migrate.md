# Faire évoluer le schéma

Objectif : modifier le schéma de la base SQLite par migrations.

**Ce que vous allez apprendre :** Forge gère les évolutions de schéma avec les commandes `migration:*`, qui fonctionnent à l'identique sur SQLite.

Premier palier du **niveau intermédiaire**.

## Ce que ce palier montre

- voir l'état des migrations ;
- créer et appliquer une migration.

## 1. État des migrations

```bash
forge migration:status
```

La sortie liste les migrations appliquées (table `forge_migrations`) et celles en attente.

## 2. Créer une migration

```bash
forge migration:make ajout_colonne_resume
```

Forge crée un fichier de migration SQL que vous éditez (le SQL reste visible).

## 3. Appliquer

```bash
forge migration:apply
```

La migration s'exécute sur le fichier SQLite, et `forge_migrations` enregistre son passage.

!!! note "Même API que les autres backends"
    Les commandes `migration:*` sont celles du cœur : votre flux ne change pas selon le backend.

## Après cette étape

[Palier suivant : Inspecter la base](sqlite-inspect.md)
