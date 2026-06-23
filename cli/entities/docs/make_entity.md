# La commande make:entity dans Forge

Ce document décrit la commande `forge make:entity`.

Le fichier de code correspondant est `cli/entities/make_entity.py`.

## 1. À quoi sert cette commande ?

`make:entity` génère la définition JSON canonique d'une entité Forge et son arborescence.
Elle fonctionne en mode interactif ou avec un nom passé en argument (`--no-input` pour le non interactif).

Le nom d'entité est validé (PascalCase) avant génération.
La génération suit le mode write-if-new : un fichier existant n'est jamais écrasé (principe 9).

## 2. L'API

| Symbole | Rôle |
|---|---|
| `validate_entity_name(name)` | valide le nom d'entité fourni |
| `build_entity_json_canonical(entity_name, table=None)` | construit la définition JSON canonique |
| `to_snake(name)` | convertit un nom en `snake_case` |
| `entities_dir(root=None)` / `project_root()` | localisent le dossier d'entités |

## 3. Contextes d'utilisation

- **Démarrage d'un modèle** : créer la définition d'une nouvelle entité.
- **Mode batch** : générer sans interaction avec `--no-input`.

## 4. Voir aussi

- [La commande make:crud](make_crud.md) : scaffolding CRUD à partir de l'entité.
- [La commande entity:validate](entity_validate.md) : validation des entités.
