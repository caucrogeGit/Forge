# forge-mvc-fixtures

Données de démonstration et de test opt-in pour le framework Forge.

## Statut : Beta — opt-in officiel (scaffold)

`forge-mvc-fixtures` est marqué `Development Status :: 4 - Beta`.
Le paquet est introduit par l'ADR-074.

C'est un **opt-in à CLI seule** : il ajoute les commandes `forge fixtures:load`
et `forge fixtures:purge` une fois installé. Il n'expose **aucune API runtime** ;
une application ne l'importe jamais à l'exécution.

## Pourquoi un opt-in

Peupler une base de données de démonstration ou de test est de l'outillage de
développement, pas du runtime de framework (principe 8, ADR-004).

Ce besoin est distinct de la migration de seed (ADR-074, principe 11) :

- les **données de référence permanentes** (partout, production comprise)
  restent une migration appliquée par `forge migration:apply` ;
- les **données de démo ou de test**, que l'on veut **rejouer** (charger, purger,
  recharger) et **cadrer par environnement** (`dev`, `test`, jamais `prod` par
  défaut), relèvent de cet opt-in.

Le SQL des fixtures reste **visible** : ce sont des fichiers `.sql` relus, pas un
format opaque (principe 5).

## Installation

```bash
pip install --pre forge-mvc-fixtures
```

Pour développer le paquet en mode éditable depuis les sources du dépôt Forge :

```bash
pip install -r requirements-dev.txt  # installe forge-mvc-fixtures depuis packages/
```

## Commandes

| Commande | Rôle |
|---|---|
| `forge fixtures:load` | Charge les fixtures `mvc/fixtures/*.sql` dans la base de l'environnement actif. Affiche le SQL par défaut ; `--run` exécute ; `--run --force` en production. |
| `forge fixtures:purge` | Vide les tables ciblées par les fixtures (dérivées des `INSERT INTO`) pour repartir d'un état propre. Mêmes options `--run` / `--force`. |

## Compatibilité

Disponible séparément depuis Forge 1.0.0-rc.2 (ADR-074).
