# Préparer la base

!!! note "Prérequis : deux paquets"
    ```bash
    pip install --pre forge-mvc-postgres forge-mvc-entities
    ```

    Le backend seul ne suffit pas.
    Les commandes de base de données (`db:init`, `db:apply`, `migration:*`) sont fournies par le moteur d'entités, extrait du cœur par l'[ADR-070](/docs/forge/adr/070-entities-engine-extraction/).

    Voir la [référence](../../reference.md) pour la mise en service complète.

Objectif : premier contact avec le backend **opt-in** `forge-mvc-postgres`.

**Ce que vous allez apprendre :** `forge db:init` provisionne la base et le rôle applicatif, puis Forge prend le relais.

Premier palier du **niveau débutant** de la progression PostgreSQL.

!!! note "Provisioning par la CLI"
    `forge db:init` affiche le SQL de provisioning (rôles, base, droits, table `forge_migrations`).

    `forge db:init --run` l'exécute : le compte `DB_ADMIN_*` doit exister côté serveur.

## Ce que ce palier montre

- renseigner l'accès au serveur ;
- provisionner la base et le rôle PostgreSQL avec `db:init` ;
- vérifier que le cœur résout le backend.

## 1. Renseigner l'accès au serveur

```bash
forge db:config
```

Cette commande amorce dans `env/example`, `env/dev` et `env/prod` les clés attendues par le backend, sans jamais écraser une valeur déjà renseignée (ADR-064).

Ouvrez ensuite `env/dev` et renseignez les valeurs vides, en particulier les mots de passe des deux comptes.
Forge n'invente aucun secret et n'en écrit aucun dans les gabarits.
Sans cette étape, `db:init` refuse et nomme les variables manquantes.

## 2. Provisionner base et rôle

```bash
forge db:init        # affiche le SQL de provisioning
forge db:init --run  # crée la base, le rôle applicatif et le registre de migrations
```

Le compte `DB_ADMIN_*` renseigné dans `env/dev` doit exister côté serveur.
(En conteneur Docker, exécutez ces commandes depuis le projet, le serveur restant joignable via `DB_HOST`/`DB_PORT`.)

## 3. Vérifier le backend

```bash
forge doctor
```

`doctor` indique le backend résolu (`postgres`) et l'état de la connexion.

## Après cette étape

[Palier suivant : Appliquer une entité](postgres-apply.md)
