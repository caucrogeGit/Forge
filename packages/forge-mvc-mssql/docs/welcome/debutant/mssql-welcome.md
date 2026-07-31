# Préparer la base

!!! note "Prérequis : deux paquets"
    ```bash
    pip install --pre forge-mvc-mssql forge-mvc-entities
    ```

    Le backend seul ne suffit pas.
    Les commandes de base de données (`db:init`, `db:apply`, `migration:*`) sont fournies par le moteur d'entités, extrait du cœur par l'[ADR-070](/docs/forge/adr/070-entities-engine-extraction/).

    Voir la [référence](../../reference.md) pour la mise en service complète.

Objectif : premier contact avec le backend **opt-in** `forge-mvc-mssql`.

**Ce que vous allez apprendre :** `forge db:init` provisionne la base SQL Server, puis Forge suit son flux habituel.

Premier palier du **niveau débutant** de la progression SQL Server.

!!! note "Compte d'administration requis"
    `forge db:init --run` se connecte avec le compte `DB_ADMIN_*`, qui doit exister sur le serveur.

    Il crée la base, la connexion et l'utilisateur applicatifs, et le registre des migrations.

## Ce que ce palier montre

- provisionner la base et le compte applicatif avec `db:init` ;
- vérifier que le cœur résout le backend.

## 1. Renseigner l'accès au serveur

```bash
forge db:config
```

Cette commande amorce dans `env/example`, `env/dev` et `env/prod` les clés attendues par le backend, sans jamais écraser une valeur déjà renseignée (ADR-064).

Ouvrez ensuite `env/dev` et renseignez les valeurs vides, en particulier les mots de passe des deux comptes.
Forge n'invente aucun secret et n'en écrit aucun dans les gabarits.
Sans cette étape, `db:init` refuse et nomme les variables manquantes.

## 2. Provisionner la base

```bash
forge db:init
```

Forge **affiche** le SQL de provisioning (logins, base, utilisateurs, `GRANT` sur `SCHEMA::dbo`, table `forge_migrations`), en lots séparés par `GO` pour `sqlcmd`.

```bash
forge db:init --run
```

`--run` exécute ce provisioning avec le compte `DB_ADMIN_*`.

## 3. Vérifier le backend

```bash
forge doctor
```

`doctor` indique le backend résolu (`mssql`) et l'état de la connexion (pilote ODBC compris).

## Après cette étape

[Palier suivant : Appliquer une entité](mssql-apply.md)
