# Le chargeur de relations CRUD dans Forge

Ce document décrit le chargement des relations pour le générateur CRUD.

Le fichier de code correspondant est `cli/entities/crud/relations_loader.py`.

## 1. À quoi sert ce module ?

Il charge et résout les relations exploitées par `make:crud` depuis les définitions d'entités et de relations.
Il prépare les relations `many_to_one` et `many_to_many` sous une forme prête pour les *builders*.

Il choisit aussi le champ de libellé d'une entité reliée et construit les bases de requêtes liées.

## 2. L'API

Le module fournit les helpers de chargement des relations CRUD (`many_to_one` et `many_to_many`), la résolution du champ de libellé et la construction des bases de sélection.
Ces helpers produisent les structures `CrudManyToOneRelation` et `CrudManyToManyRelation` du contexte.

## 3. Contextes d'utilisation

- **Génération CRUD** : alimenter les *builders* en relations résolues.
- **Sélecteurs** : préparer les choix des champs reliés.

## 4. Voir aussi

- [Le contexte du générateur](context.md) : structures de relations produites.
- [Le builder de modèle](model_builder.md) : consommateur des relations.
