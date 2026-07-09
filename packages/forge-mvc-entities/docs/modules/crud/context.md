# Le contexte du générateur CRUD dans Forge

Ce document décrit les constantes et structures partagées du générateur CRUD.

Le fichier de code correspondant est `cli/entities/crud/context.py`.

## 1. À quoi sert ce module ?

Il porte les structures de données et les helpers partagés par les *builders* de `make:crud`.
C'est le socle commun : les autres modules CRUD importent leurs types depuis ici.

Il décrit notamment le résultat de génération et les relations exploitées par le CRUD.

## 2. L'API

| Symbole | Rôle |
|---|---|
| `MakeCrudResult` | résultat de génération (fichiers créés, préservés) |
| `CrudManyToOneRelation` | relation `many_to_one` exploitée par le CRUD |
| `CrudManyToManyRelation` | relation `many_to_many` exploitée par le CRUD |

## 3. Contextes d'utilisation

- **Socle des builders** : fournir les types partagés du générateur CRUD.
- **Permissions** : appliquer les gardes de permission aux blocs générés.

## 4. Voir aussi

- [Le builder de contrôleur](controller_builder.md) : génération du contrôleur.
- [Le chargeur de relations](relations_loader.md) : construction des relations CRUD.
