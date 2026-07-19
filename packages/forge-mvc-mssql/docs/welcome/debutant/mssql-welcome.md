# Préparer la base

!!! note "Prérequis : installer l'opt-in"
    Installez `forge-mvc-mssql` avant de commencer : voir sa [référence](../../reference.md).

Objectif : premier contact avec le backend **opt-in** `forge-mvc-mssql`.

**Ce que vous allez apprendre :** `forge db:init` provisionne la base SQL Server, puis Forge suit son flux habituel.

Premier palier du **niveau débutant** de la progression SQL Server.

!!! note "Compte d'administration requis"
    `forge db:init --run` se connecte avec le compte `DB_ADMIN_*`, qui doit exister sur le serveur.

    Il crée la base, la connexion et l'utilisateur applicatifs, et le registre des migrations.

## Ce que ce palier montre

- provisionner la base et le compte applicatif avec `db:init` ;
- vérifier que le cœur résout le backend.

## 1. Provisionner la base

```bash
forge db:init
```

Forge **affiche** le SQL de provisioning (logins, base, utilisateurs, `GRANT` sur `SCHEMA::dbo`, table `forge_migrations`), en lots séparés par `GO` pour `sqlcmd`.

```bash
forge db:init --run
```

`--run` exécute ce provisioning avec le compte `DB_ADMIN_*`.

## 2. Vérifier le backend

```bash
forge doctor
```

`doctor` indique le backend résolu (`mssql`) et l'état de la connexion (pilote ODBC compris).

## Après cette étape

[Palier suivant : Appliquer une entité](mssql-apply.md)
