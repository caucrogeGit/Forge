# Forge Fixtures

`forge-mvc-fixtures` est l'opt-in de **données de démonstration et de test** de Forge (ADR-074).

Il ajoute deux commandes une fois installé :

- `forge fixtures:load` charge des jeux de données dans la base de l'environnement actif ;
- `forge fixtures:purge` vide les tables ciblées pour repartir d'un état propre.

C'est un opt-in **à ligne de commande seule** : aucune API runtime, une application ne l'importe jamais à l'exécution.

## Pour qui, pourquoi

Une démo ou un projet pédagogique a besoin d'un jeu de données de départ sur lequel travailler : quelques villes, des comptes d'exemple, un référentiel.
Peupler la base à la main à chaque remise à zéro est fastidieux.

Les fixtures répondent à ce besoin : des données **rejouables** (charger, purger, recharger) et **cadrées par environnement** (`dev`, `test`, jamais `prod` par défaut).

## Ce que ce n'est pas

Les fixtures ne gèrent pas le schéma.
Le référentiel **permanent** (ce qui doit exister partout, production comprise) reste une migration de seed appliquée par `forge migration:apply`.
Cette frontière est le cœur de l'ADR-074 : voir la [référence](reference.md).

## Installation

```bash
pip install --pre forge-mvc-fixtures
```

## Pour apprendre

La progression *Fixtures* enseigne pas à pas le chargement, la purge, le cadrage par environnement et la frontière avec la migration de seed.
Commencez par [Bonjour les fixtures](welcome/debutant/fixtures-welcome.md).
