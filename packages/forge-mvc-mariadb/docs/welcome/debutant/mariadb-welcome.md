# Provisionner la base

Objectif : premier contact avec le backend **opt-in** `forge-mvc-mariadb`.

**Ce que vous allez apprendre :** MariaDB est un serveur ; `forge db:init` crée la base et le compte applicatif à partir du compte d'administration.

Premier palier du **niveau débutant** de la progression MariaDB.

!!! note "Backend serveur"
    Contrairement à SQLite, MariaDB a un serveur : `db:init` y crée une base et un utilisateur.

    Il faut donc un compte d'administration (`DB_ADMIN_*`) avec les droits suffisants.

## Ce que ce palier montre

- vérifier le backend et la connexion ;
- provisionner la base avec `forge db:init`.

## 1. Vérifier le backend et la connexion

```bash
forge doctor
```

`doctor` indique le backend résolu (`mariadb`) et teste l'accès au serveur.

## 2. Provisionner

```bash
forge db:init
```

Avec `DB_ADMIN_*`, Forge crée la base `DB_NAME`, le compte applicatif `DB_APP_*`, accorde les privilèges, et crée la table `forge_migrations`.

## Après cette étape

[Palier suivant : Appliquer une entité](mariadb-apply.md)
