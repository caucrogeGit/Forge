# Première base SQLite

!!! note "Prérequis : installer l'opt-in"
    Installez `forge-mvc-sqlite` avant de commencer : voir sa [référence](../../reference.md).

Objectif : premier contact avec le backend **opt-in** `forge-mvc-sqlite`.

**Ce que vous allez apprendre :** SQLite range la base dans un fichier.
Le cœur de Forge le découvre dès qu'il est installé, et `forge db:init` crée ce fichier.

Premier palier du **niveau débutant** de la progression SQLite.

!!! note "Backend sans serveur"
    SQLite n'a pas de serveur : il n'y a ni base distante, ni compte à créer.

    `db:init` prépare simplement le fichier et la table technique `forge_migrations`.

## Ce que ce palier montre

- vérifier que le backend est actif ;
- créer la base avec `forge db:init`.

## 1. Vérifier le backend actif

```bash
forge doctor
```

`doctor` indique le backend BDD résolu.
Avec seulement `forge-mvc-sqlite` installé, c'est `sqlite`.

## 2. Créer la base

```bash
forge db:init
```

Forge crée le fichier SQLite (chemin `DB_NAME`) et la table `forge_migrations`.

Aucun serveur n'est contacté : tout se passe dans un fichier local.

## Après cette étape

[Palier suivant : Appliquer une entité](sqlite-apply.md)
