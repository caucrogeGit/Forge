# Préparer la base

!!! note "Prérequis : installer l'opt-in"
    Installez `forge-mvc-postgres` avant de commencer : voir sa [référence](../../reference.md).

Objectif : premier contact avec le backend **opt-in** `forge-mvc-postgres`.

**Ce que vous allez apprendre :** `forge db:init` provisionne la base et le rôle applicatif, puis Forge prend le relais.

Premier palier du **niveau débutant** de la progression PostgreSQL.

!!! note "Provisioning par la CLI"
    `forge db:init` affiche le SQL de provisioning (rôles, base, droits, table `forge_migrations`).

    `forge db:init --run` l'exécute : le compte `DB_ADMIN_*` doit exister côté serveur.

## Ce que ce palier montre

- provisionner la base et le rôle PostgreSQL avec `db:init` ;
- vérifier que le cœur résout le backend.

## 1. Provisionner base et rôle

```bash
forge db:init        # affiche le SQL de provisioning
forge db:init --run  # crée la base, le rôle applicatif et le registre de migrations
```

Le compte `DB_ADMIN_*` renseigné dans `env/dev` doit exister côté serveur.
(En conteneur Docker, exécutez ces commandes depuis le projet, le serveur restant joignable via `DB_HOST`/`DB_PORT`.)

## 2. Vérifier le backend

```bash
forge doctor
```

`doctor` indique le backend résolu (`postgres`) et l'état de la connexion.

## Après cette étape

[Palier suivant : Appliquer une entité](postgres-apply.md)
