# Faire évoluer le schéma avec les migrations

Objectif : appliquer le schéma à une base, puis le faire évoluer proprement.

**Ce que vous allez apprendre :** les commandes `migration:*` transforment vos contrats en un schéma appliqué à la base, de façon incrémentale et traçable.
Le SQL reste visible : une migration est un fichier que vous relisez avant de l'appliquer.

!!! note "Un backend est requis"
    Ce palier touche une vraie base.
    Installez et configurez un backend (par exemple `pip install forge-mvc-sqlite`), puis provisionnez avec `forge db:init`.

## Préparer la base

```bash
forge db:config    # amorce DB_NAME dans env/ (une seule fois)
forge db:init
forge db:apply     # crée en base les tables de vos entités
```

`db:init` **affiche** le SQL de provisioning (base et comptes) dérivé de votre environnement ; `--run` l'exécute.
Vous voyez donc ce qui va être fait avant que ce soit fait.

`db:apply` est l'étape que l'on oublie, et c'est celle qui rend le reste utilisable.
Les paliers précédents ont produit le SQL de vos entités dans `mvc/entities/`, mais produire du SQL n'est pas le poser en base.
Sans cette commande, les tables n'existent pas et les écrans engendrés par `make:crud` répondent 500 sur une table absente.
À relancer chaque fois que vous ajoutez une entité ou une relation.

## Créer une migration

Après avoir déclaré ou modifié des entités (niveau débutant), générez la migration correspondante :

```bash
forge migration:make ajout_colonne_resume
```

Le nom est obligatoire : il devient celui du fichier produit, et c'est lui que vous lirez dans l'historique des migrations.
Choisissez-le descriptif, à la façon d'un message de commit.

Forge produit un fichier de migration à partir de l'écart entre vos contrats et l'état connu du schéma.
Ouvrez-le : c'est du SQL lisible, que vous pouvez relire et versionner.

## Appliquer

```bash
forge migration:apply
```

La migration est appliquée à la base, et son application est enregistrée : elle ne sera pas rejouée.

```bash
forge migration:status
```

`migration:status` liste ce qui est appliqué et ce qui reste en attente.

## Le cycle d'évolution

1. Modifier un contrat d'entité (ajouter un champ, une relation…).
2. `forge build:model` pour régénérer les projections.
3. `forge migration:make` pour capturer l'écart.
4. `forge migration:apply` pour le porter en base.

Ce cycle garde le contrat comme source, la base comme reflet appliqué, et chaque étape lisible.

## Commandes Forge utilisées

| Commande | Rôle dans ce palier | Référence |
|---|---|---|
| `forge db:init` | Afficher (puis exécuter) le SQL de provisioning. | [db:init](../../modules/db_init.md) |
| `forge migration:make` | Générer une migration depuis l'écart de schéma. | [migration:*](../../modules/migrations.md) |
| `forge migration:apply` | Appliquer les migrations en attente. | [migration:*](../../modules/migrations.md) |
| `forge migration:status` | Lister l'état des migrations. | [migration:*](../../modules/migrations.md) |

## La suite

Vous savez modéliser et faire évoluer une couche de données.
Faisons le bilan du niveau intermédiaire avant le niveau avancé.

[Suivant : horodatages et suppression logique](options-entite.md)
