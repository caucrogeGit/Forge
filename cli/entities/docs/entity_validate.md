# La commande entity:validate dans Forge

Ce document décrit la commande `forge entity:validate`.

Le fichier de code correspondant est `cli/entities/entity_validate.py`.

## 1. À quoi sert cette commande ?

`entity:validate` valide les fichiers d'entités et de relations d'un projet en deux passes :

1. validation structurelle JSON Schema (`entity.schema.json`, `relations.schema.json`) ;
2. validation sémantique Forge (doublons, noms réservés, cohérence relationnelle).

La passe sémantique est portée par [`entity_semantic_validate`](entity_semantic_validate.md).
Les codes d'erreur stables sont définis dans [`entity_validation_errors`](entity_validation_errors.md).

## 2. L'API

| Symbole | Rôle |
|---|---|
| `main(args=None)` | point d'entrée de la commande `forge entity:validate` |

La commande gère les deux passes et restitue une sortie humaine ou machine selon les options.

## 3. Contextes d'utilisation

- **Garde-fou** : vérifier les entités avant génération ou application SQL.
- **CI** : faire échouer un pipeline sur une entité invalide.

## 4. Voir aussi

- [La validation sémantique](entity_semantic_validate.md) : seconde passe.
- [Les codes d'erreur](entity_validation_errors.md) : codes stables `FORGE_*`.
