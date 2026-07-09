# Préparer la base

!!! note "Prérequis : installer l'opt-in"
    Installez `forge-mvc-postgres` avant de commencer : voir sa [référence](../../reference.md).

Objectif : premier contact avec le backend **opt-in** `forge-mvc-postgres` (Alpha).

**Ce que vous allez apprendre :** comme le provisioning CLI n'est pas encore câblé, on crée la base et le rôle à la main, puis Forge prend le relais.

Premier palier du **niveau débutant** de la progression PostgreSQL.

!!! warning "Alpha : provisioning manuel"
    `forge db:init` ne provisionne pas encore PostgreSQL.

    On crée donc la base et le rôle avec les outils PostgreSQL, puis on utilise `db:apply`.

## Ce que ce palier montre

- créer la base et le rôle PostgreSQL ;
- vérifier que le cœur résout le backend.

## 1. Créer base et rôle

```bash
createdb mon_projet
psql -c "CREATE ROLE mon_projet LOGIN PASSWORD 'motdepasse';"
psql -c "GRANT ALL ON DATABASE mon_projet TO mon_projet;"
```

(En conteneur Docker, exécutez ces commandes dans le conteneur PostgreSQL.)

## 2. Vérifier le backend

```bash
forge doctor
```

`doctor` indique le backend résolu (`postgres`) et l'état de la connexion.

## Après cette étape

[Palier suivant : Appliquer une entité](postgres-apply.md)
