# Provisionner la base

!!! note "Prérequis : deux paquets"
    ```bash
    pip install --pre forge-mvc-mariadb forge-mvc-entities
    ```

    Le backend seul ne suffit pas.
    Les commandes de base de données (`db:init`, `db:apply`, `migration:*`) sont fournies par le moteur d'entités, extrait du cœur par l'[ADR-070](/docs/forge/adr/070-entities-engine-extraction/).

    Voir la [référence](../../reference.md) pour la mise en service complète.

Objectif : premier contact avec le backend **opt-in** `forge-mvc-mariadb`.

**Ce que vous allez apprendre :** MariaDB est un serveur ; `forge db:init` génère le SQL qui crée la base et les deux comptes, que vous exécutez dans votre session d'administration.

Premier palier du **niveau débutant** de la progression MariaDB.

!!! note "Backend serveur"
    Contrairement à SQLite, MariaDB a un serveur : il faut y créer une base et des comptes.

    Forge ne demande jamais le root du serveur : `db:init` **affiche** le SQL, et c'est vous qui l'exécutez (ADR-067).

## Ce que ce palier montre

- vérifier le backend et la connexion ;
- renseigner l'accès au serveur ;
- provisionner la base avec `forge db:init`.

## 1. Vérifier le backend et la connexion

```bash
forge doctor
```

`doctor` indique le backend résolu (`mariadb`) et teste l'accès au serveur.

Sur un projet neuf, il signale que la configuration est incomplète, ce que le palier suivant corrige.

## 2. Renseigner l'accès au serveur

```bash
forge db:config
```

Cette commande amorce dans `env/example`, `env/dev` et `env/prod` les clés attendues par le backend, sans jamais écraser une valeur déjà renseignée (ADR-064).

Ouvrez ensuite `env/dev` et renseignez les valeurs vides, en particulier les mots de passe des deux comptes.
Forge n'invente aucun secret et n'en écrit aucun dans les gabarits.

## 3. Provisionner

`forge db:init` lit `env/` et affiche le script SQL de provisioning (base + comptes scellés à `DB_NAME`) :

```bash
forge db:init
```

Collez ce script dans une session d'administration MariaDB :

```bash
sudo mariadb
```

Il crée la base `DB_NAME`, le compte d'administration de la base (`DB_ADMIN_*`) et le compte applicatif (`DB_APP_*`).
Si vous disposez d'un compte serveur et voulez que Forge l'exécute directement, utilisez `forge db:init --run`.

## Après cette étape

[Palier suivant : Appliquer une entité](mariadb-apply.md)
