# Les codes d'erreur de validation d'entité dans Forge

Ce document décrit les codes d'erreur stables émis par `forge entity:validate`.
Ce sont des constantes Python, pas une commande.

Le module correspondant est `forge_mvc_entities.entity_validation_errors`.

## 1. Rôle

Ce module centralise les codes d'erreur stables, préfixés `FORGE_`, de la validation d'entités.
Ces codes servent de base partagée pour plusieurs usages :

- la sortie humaine de `forge entity:validate` ;
- les tests ciblés ;
- la future sortie `--json` ;
- la documentation et les traductions éventuelles.

La stabilité de ces codes est un contrat : ils ne changent pas au gré des évolutions internes.

## 2. Vue d'ensemble rapide

| Élément | Valeur |
|---|---|
| Commande forge | aucune (constantes consommées par `entity:validate`) |
| Module Python | `forge_mvc_entities.entity_validation_errors` |
| Catégorie | validation du modèle de données |
| Rôle | exposer les codes d'erreur stables de validation |
| Entrées | aucune |
| Sorties | constantes `str` et liste `ALL_CODES` |
| Fichiers touchés | aucun |
| Mode Forge | lit |
| Convention | `FORGE_ENTITY_*`, `FORGE_RELATION_*`, `FORGE_PIVOT_*` |

## 3. Codes disponibles

Les codes sont regroupés par famille.

### 3.1 Erreurs d'entité

| Code | Sens |
|---|---|
| `FORGE_ENTITY_JSON_INVALID` | fichier JSON d'entité non analysable |
| `FORGE_ENTITY_SCHEMA_MISSING` | schéma d'entité introuvable |
| `FORGE_ENTITY_SCHEMA_INVALID` | entité non conforme au JSON Schema |
| `FORGE_ENTITY_DUPLICATE_FIELD` | champ déclaré deux fois dans une entité |
| `FORGE_ENTITY_RESERVED_PYTHON_NAME` | nom de champ réservé en Python |
| `FORGE_ENTITY_DUPLICATE_TABLE` | table partagée par deux entités |
| `FORGE_ENTITY_INVALID_INDEX` | index pointant vers un champ inexistant |
| `FORGE_ENTITY_RESERVED_SQL_NAME` | table ou entité portant un mot réservé SQL |
| `FORGE_ENTITY_INVALID_SLUG_SOURCE` | source de slug inexistante ou auto-référence |
| `FORGE_ENTITY_INVALID_DEFAULT` | valeur par défaut incompatible avec le type du champ |

### 3.2 Erreurs de relation

| Code | Sens |
|---|---|
| `FORGE_RELATION_SCHEMA_INVALID` | relation non conforme au JSON Schema |
| `FORGE_RELATION_UNKNOWN_ENTITY` | relation visant une entité inconnue |
| `FORGE_RELATION_DUPLICATE` | relation déclarée en double |
| `FORGE_RELATION_INVALID_ON_DELETE` | action `on_delete` invalide |
| `FORGE_RELATION_FK_COLLISION` | collision de clé étrangère |

### 3.3 Erreurs de table pivot

| Code | Sens |
|---|---|
| `FORGE_PIVOT_SCHEMA_INVALID` | pivot non conforme au JSON Schema |
| `FORGE_PIVOT_TABLE_COLLISION` | table de pivot en collision |
| `FORGE_PIVOT_RESERVED_FIELD` | champ réservé dans le pivot |
| `FORGE_PIVOT_KEY_COLLISION` | collision de clé dans le pivot |
| `FORGE_PIVOT_UNIQUE_PAIR_REQUIRED` | paire unique requise sur le pivot |

## 4. API publique

| Symbole | Type | Rôle |
|---|---|---|
| Constantes `FORGE_*` | `str` | codes d'erreur stables de validation d'entité |
| `ALL_CODES` | `list[str]` | liste exhaustive des codes, utile aux tests et à la documentation |

## 5. Contextes d'utilisation

| Besoin | Commande / Élément |
|---|---|
| Identifier une erreur par un code stable | constante `FORGE_*` |
| Asserter sur un code plutôt qu'un message | `FORGE_*` dans un test |
| Vérifier l'exhaustivité des codes | `ALL_CODES` |

## 6. Exemples d'utilisation

Référencer un code stable dans un test :

```python
from forge_mvc_entities.entity_validation_errors import (
    FORGE_ENTITY_DUPLICATE_FIELD,
    ALL_CODES,
)

assert FORGE_ENTITY_DUPLICATE_FIELD in ALL_CODES
```

## 7. Stabilité contractuelle

!!! note "Codes stables"
    Ces codes constituent un contrat.
    Ils ne doivent pas changer au fil des évolutions internes, afin de rester exploitables par les tests, l'outillage et la documentation.

## Voir aussi

- [La commande entity:validate](entity_validate.md) : émetteur de ces codes.
- [La validation sémantique des entités](entity_semantic_validate.md) : seconde passe qui produit ces codes.
