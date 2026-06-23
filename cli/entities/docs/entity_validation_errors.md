# Les codes d'erreur de validation d'entité dans Forge

Ce document décrit les codes d'erreur stables de `forge entity:validate`.

Le fichier de code correspondant est `cli/entities/entity_validation_errors.py`.

## 1. À quoi sert ce module ?

Il centralise les codes d'erreur stables, préfixés `FORGE_`, de la validation d'entités.
Ces codes servent de base partagée pour plusieurs usages :

- la sortie humaine de `forge entity:validate` ;
- les tests ciblés ;
- la future sortie `--json` ;
- la documentation et les traductions éventuelles.

La stabilité de ces codes est un contrat : ils ne changent pas au gré des évolutions internes.

## 2. L'API

| Symbole | Rôle |
|---|---|
| Constantes `FORGE_*` | codes d'erreur stables de validation d'entité |

## 3. Contextes d'utilisation

- **Outillage** : identifier une erreur de validation par un code stable.
- **Tests** : asserter sur un code plutôt que sur un message.

## 4. Voir aussi

- [La commande entity:validate](entity_validate.md) : émetteur de ces codes.
- [La validation sémantique](entity_semantic_validate.md) : seconde passe.
