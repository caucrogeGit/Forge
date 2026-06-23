# La commande make:relation dans Forge

Ce document décrit la commande `forge make:relation`.

Le fichier de code correspondant est `cli/entities/make_relation.py`.

## 1. À quoi sert cette commande ?

`make:relation` déclare une relation entre entités dans `mvc/entities/relations.json`.
Elle fonctionne en mode interactif : elle guide le choix du type de relation, des entités et des actions.

Elle prend en charge les relations `many_to_one` et `many_to_many` (pivot canonique).
Elle ajoute la relation au document existant sans détruire les relations déjà déclarées (principe 9).

## 2. L'API

Le module est principalement interactif.
Son point d'entrée assemble la relation à partir des réponses de l'utilisateur, puis l'écrit dans `relations.json`.

## 3. Contextes d'utilisation

- **Modélisation** : relier deux entités existantes.
- **Pivot** : déclarer une relation `many_to_many` enrichie.

## 4. Voir aussi

- [La commande entity:validate](entity_validate.md) : validation des relations déclarées.
- [Les relations globales](relations.md) : validation et génération du SQL de relations.
