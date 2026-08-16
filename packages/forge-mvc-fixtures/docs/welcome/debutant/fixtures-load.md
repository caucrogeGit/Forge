# Charger une première fixture

Objectif : écrire un fichier de fixtures et le charger avec `forge fixtures:load`.

**Ce que vous allez apprendre :** la commande affiche d'abord le SQL, puis l'exécute avec `--run`.

## Écrire la fixture

Créez le fichier `mvc/fixtures/01_villes.sql` (on suppose une table `ville` déjà provisionnée) :

```sql
-- Quelques villes de démonstration
INSERT INTO ville (nom) VALUES ('Lyon');
INSERT INTO ville (nom) VALUES ('Nice');
INSERT INTO ville (nom) VALUES ('Bordeaux');
```

Le préfixe `01_` fixe l'ordre de chargement quand vous aurez plusieurs fichiers.

## Voir avant d'écrire

Lancez la commande **sans option** :

```bash
forge db:config          # amorce la connexion dans env/ (une seule fois)
forge db:init            # provisionne la base
forge fixtures:load
```

Elle **affiche** le SQL qu'elle chargerait, sans rien exécuter.
C'est le même principe que `forge db:init` (charte §7) : on voit ce qui va être écrit avant que ce soit écrit.

## Charger

Quand le SQL vous convient, exécutez-le avec `--run` :

```bash
forge fixtures:load --run
```

La commande charge chaque instruction dans la base de l'environnement actif (`dev` par défaut) et affiche un résumé.
Relancez `--run` autant de fois que nécessaire : la fixture est **rejouable**.

## Vérifier

Ouvrez votre écran de liste, ou interrogez la base : les villes sont là.

## Commandes utilisées

| Commande | Rôle |
|---|---|
| `forge fixtures:load` | Affiche le SQL des fixtures (aucun effet). |
| `forge fixtures:load --run` | Charge les fixtures dans la base de l'environnement actif. |

## La suite

Faisons le bilan du niveau débutant.

[Continuer : bilan du niveau débutant](bilan.md)
