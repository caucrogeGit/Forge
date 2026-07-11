# Fixtures ou migration de seed

Objectif : choisir sans hésiter entre une fixture et une migration de seed.

**Ce que vous allez apprendre :** les deux insèrent des données, mais servent des besoins disjoints (principe 11, une seule façon officielle par besoin).

## La question à se poser

> Cette donnée doit-elle exister **partout et toujours**, production comprise ?

- **Oui** : c'est du référentiel permanent. Écrivez une **migration de seed**.
- **Non**, c'est de la démo ou du test que je veux pouvoir recharger : écrivez une **fixture**.

## Migration de seed

Une migration de seed est un fichier de migration écrit à la main, appliqué par `forge migration:apply`.

- Elle s'applique **une seule fois** (enregistrée par empreinte) et **dans tous les environnements**.
- Elle est l'histoire du schéma et de ses données de référence.
- On ne la rejoue pas : elle est définitive.

C'est le bon choix pour une liste de pays, des rôles applicatifs, un référentiel métier stable.

## Fixture

Une fixture est un fichier `mvc/fixtures/*.sql` chargé par `forge fixtures:load`.

- Elle est **rejouable** : charger, purger, recharger à volonté.
- Elle est **cadrée par environnement** et la production est protégée.
- Elle ne gère pas le schéma : elle peuple des tables déjà provisionnées.

C'est le bon choix pour des villes de démonstration, des comptes d'essai, un jeu de test.

## Tableau de décision

| Critère | Migration de seed | Fixture |
|---|---|---|
| Présente en production | Oui | Non (protégée) |
| Rejouable | Non (une fois) | Oui |
| Gère le schéma | Non (données seules) | Non (données seules) |
| Commande | `migration:apply` | `fixtures:load` / `fixtures:purge` |

## La suite

Voyons pourquoi les fixtures sont un opt-in à part, à CLI seule.

[Continuer : un opt-in CLI-only](fixtures-optin.md)
