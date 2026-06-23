# La validation sémantique des entités dans Forge

Ce document décrit la validation sémantique des entités et relations.

Le fichier de code correspondant est `cli/entities/entity_semantic_validate.py`.

## 1. À quoi sert ce module ?

Cette couche s'exécute après la validation JSON Schema (structurelle).
Elle vérifie la cohérence que le schéma seul ne peut pas garantir :

- doublons de champs dans une entité ;
- noms de champs réservés Python ;
- doublons de table entre entités ;
- cohérence des relations (`many_to_one`, `many_to_many`).

Elle complète donc [`entity:validate`](entity_validate.md), qui l'orchestre.

## 2. L'API

| Symbole | Rôle |
|---|---|
| `validate_semantic(...)` | exécute les contrôles sémantiques et retourne les erreurs |
| `SemanticError` | erreur sémantique unitaire (code, message, chemin) |

## 3. Contextes d'utilisation

- **Cohérence du modèle** : détecter une incohérence qu'un schéma ne voit pas.
- **Relations** : valider la pertinence des liens déclarés entre entités.

## 4. Voir aussi

- [La commande entity:validate](entity_validate.md) : orchestration des deux passes.
- [Les codes d'erreur](entity_validation_errors.md) : codes stables `FORGE_*`.
