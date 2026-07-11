# forge-mvc-fixtures

Données de démonstration et de test opt-in pour le framework Forge.

## Statut : Beta — opt-in officiel (scaffold)

`forge-mvc-fixtures` est marqué `Development Status :: 4 - Beta`.
Le paquet est introduit par l'ADR-074.

C'est un **opt-in à CLI seule** : il ajoutera les commandes `forge fixtures:load`
et `forge fixtures:purge` une fois complet. Il n'expose **aucune API runtime** ;
une application ne l'importe jamais à l'exécution.

Ce premier ticket met en place la structure du paquet.
Les commandes sont livrées aux tickets suivants, avec un contrat complet
(charte principe 10 : pas d'API publique à moitié faite).

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

| Commande | Rôle | Statut |
|---|---|---|
| `forge fixtures:load` | Charge un jeu de fixtures dans la base de l'environnement actif, après affichage du SQL. | À venir |
| `forge fixtures:purge` | Vide les tables ciblées pour repartir d'un état propre. | À venir |

## Compatibilité

Disponible séparément depuis Forge 1.0.0-rc.2 (ADR-074).
