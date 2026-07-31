# Générer plutôt qu'écrire à la main

Objectif : produire un fichier de fixtures depuis une factory, au lieu de taper les `INSERT` à la main.

**Ce que vous allez apprendre :** `fixtures:make-factory` échafaude une factory depuis le contrat d'entité, `fixtures:generate` l'exécute et écrit le `.sql`.

## Le problème

Écrire cinquante villes à la main est fastidieux et peu réaliste.
Une **factory** décrit comment produire des lignes ; Forge génère ensuite le `.sql` à partir d'elle.

## Déclarer l'entité visée

Une factory se déduit d'un contrat d'entité, il en faut donc un.

```bash
forge make:entity ville --no-input
forge db:apply
```

Sans le contrat, `fixtures:make-factory` refuse, faute de quoi lire.
Sans `db:apply`, la table n'existe pas encore et le chargement des fixtures échouera sur un `no such table`.

## Échafauder la factory

```bash
forge fixtures:make-factory ville
```

Forge lit le contrat `mvc/entities/ville` et écrit `mvc/fixtures/factories/ville_factory.py`.
Chaque champ reçoit déjà un provider Faker **plausible**, deviné par type et par nom (un champ `nom` textuel, un `code_postal`, un booléen...).
Vous partez d'une factory qui fonctionne.

## Générer le SQL

```bash
forge fixtures:generate ville --rows 50 --seed 42
```

Forge exécute la factory, **affiche** le SQL produit (on voit ce qui va être écrit), puis l'écrit dans `mvc/fixtures/ville.sql`.

- `--rows 50` : cinquante lignes.
- `--seed 42` : génération **reproductible** (même graine, mêmes données ; tout le monde charge le même `.sql`).

Le fichier n'est pas écrasé s'il existe déjà : ajoutez `--force` pour le remplacer (charte §9).

## Charger

La suite ne change pas : c'est le même chargement qu'une fixture écrite à la main.

```bash
forge fixtures:load --run
```

La factory alimente la voie existante ; il n'y a qu'un seul mécanisme de chargement.

## Commandes utilisées

| Commande | Rôle |
|---|---|
| `forge fixtures:make-factory <entity>` | Échafaude une factory depuis le contrat d'entité. |
| `forge fixtures:generate <entity> --rows N --seed S` | Exécute la factory, affiche puis écrit le `.sql`. |

## La suite

Faisons le bilan du niveau intermédiaire.

[Continuer : bilan du niveau intermédiaire](bilan.md)
