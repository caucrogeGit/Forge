# Bonjour les fixtures

Objectif : comprendre ce qu'est une fixture et où elle vit dans un projet Forge.

**Ce que vous allez apprendre :** une fixture est un jeu de **données de départ** pour la base, écrit en SQL visible et rejouable.

## Le besoin

Vous avez une base avec des tables (créées par les migrations), mais elles sont vides.
Pour développer un écran ou faire une démo, il vous faut des données : quelques villes, des comptes d'exemple.
Les saisir à la main à chaque remise à zéro est fastidieux.

Une fixture répond à ce besoin : un fichier SQL que vous chargez d'un geste, autant de fois que vous voulez.

## Où vivent les fixtures

Les fixtures sont des fichiers `.sql` dans le dossier `mvc/fixtures/` de votre projet :

```
mvc/
  fixtures/
    01_villes.sql
```

Le SQL reste **visible** : vous écrivez des `INSERT INTO` que vous relisez.
Rien de caché, rien de magique.

## Fixtures ou migration ?

Retenez la frontière dès maintenant.

- Une donnée qui doit exister **partout et toujours** (un référentiel de production) est une **migration de seed**.
- Une donnée de **démonstration ou de test**, que vous voulez charger, vider et recharger, est une **fixture**.

Ce palier et les suivants ne parlent que des fixtures.

## Prérequis

- l'opt-in installé : `pip install --pre forge-mvc-fixtures` ;
- un backend BDD configuré (par exemple `pip install forge-mvc-sqlite`) ;
- au moins une table déjà provisionnée par une migration.

## La suite

Écrivons une première fixture et chargeons-la.

[Continuer : charger une première fixture](fixtures-load.md)
