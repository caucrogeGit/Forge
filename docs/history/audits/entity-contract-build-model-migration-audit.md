# Audit — Migration build:model vers le format canonique

**Ticket** : ENTITY-CONTRACT-011A-BUILDMODEL-MIGRATION-AUDIT  
**Date** : 2026-05  
**Statut** : livré

---

## 1. Contexte

Le ticket ENTITY-CONTRACT-011 visait à brancher la validation JSON Schema dans
`forge build:model`. Il a été arrêté car les deux systèmes utilisent des formats
d'entité mutuellement exclusifs.

Ce document recense précisément l'incompatibilité et propose un plan de migration
découpé en tickets atomiques.

---

## 2. Blocage constaté

| Couche | Fichier | Format attendu | Clé de détection |
|---|---|---|---|
| `build:model` / `validation.py` | `mvc/entities/media/media.json` | Legacy | `format_version: 1` |
| `entity:validate` / `entity.schema.json` | même fichier | Canonique | `schema_version: "1.0"` |

Un fichier valide pour l'un est invalide pour l'autre.
Les deux validations sont activement incompatibles (`entity` vs `name`, `sql_type` vs `type`, etc.).

---

## 3. Flux actuel de build:model

```
forge.py
└─ command == "build:model"
   └─ model_main(args)                            forge_cli/entities/model.py:main()
      └─ build_model(entities_root)               model.py:build_model()
         └─ _validate_model_or_raise(entities_root)
            ├─ _load_all_entity_sources()
            │   └─ for each mvc/entities/<name>/ :
            │       └─ validate_entity_definition(json_data)  validation.py
            │           └─ normalize_entity_definition()
            │               ├─ _validate_root_structure()     lit entity, fields, format_version
            │               └─ _normalize_field_data()        lit sql_type, python_type, column
            ├─ _validate_global_entity_consistency()
            └─ validate_relations_definition()    relations.py
         └─ for each entity_source:
             ├─ build_entity_sql(definition)      make_entity.py   lit column, sql_type
             └─ build_entity_base(definition)     make_entity.py   lit python_type, entity
```

**Structure de répertoire** : `mvc/entities/<snake_name>/<snake_name>.json`  
(contrairement à `entity:validate` qui lit `mvc/entities/**/*.json` via `rglob`)

---

## 4. Format legacy actuel (format_version: 1)

| Clé racine | Exemple | Utilisé par | Rôle |
|---|---|---|---|
| `format_version` | `1` | `validation.py` | Version du format |
| `entity` | `"Media"` | génération `_base.py`, SQL | Nom logique PascalCase |
| `table` | `"media"` | SQL | Table MariaDB |
| `description` | `"..."` | documentation | Description libre |
| `fields` | `[...]` | validation, génération | Liste des champs |
| `media` | `[...]` | génération media | Déclaration uploads |
| `rbac` | `{...}` | génération RBAC | Permissions |

| Clé de champ | Exemple | Utilisé par | Rôle |
|---|---|---|---|
| `name` | `"entity_name"` | SQL, Python | Nom du champ |
| `column` | `"EntityName"` | SQL | Nom de colonne (PascalCase) |
| `python_type` | `"str"` | `_base.py` | Type Python |
| `sql_type` | `"VARCHAR(100)"` | SQL brut | Type SQL complet |
| `nullable` | `false` | SQL | NULL autorisé |
| `primary_key` | `true` | SQL | Clé primaire |
| `auto_increment` | `true` | SQL | AUTO_INCREMENT |
| `constraints` | `{"not_empty": true, "max_length": 100}` | validation | Contraintes métier |
| `default` | `"default"` | SQL, Python | Valeur par défaut |
| `unique` | `false` | SQL | UNIQUE KEY |
| `form.field` | `"string"` | génération CRUD | Widget formulaire |
| `list.filter` | `true` | génération CRUD | Filtre liste |

**Entités actuelles dans le dépôt** : `mvc/entities/media/media.json` — 11 champs.  
**Relations actuelles** : `mvc/entities/relations.json` — vide (`relations: []`), clé `format_version: 1`.

---

## 5. Format canonique cible (schema_version: "1.0")

| Clé racine | Exemple | Rôle |
|---|---|---|
| `schema_version` | `"1.0"` | Version du contrat |
| `name` | `"Media"` | Nom PascalCase |
| `table` | `"media"` | Table MariaDB |
| `label` | `"Média"` | Libellé UI (optionnel) |
| `description` | `"..."` | Description (optionnel) |
| `fields` | `[...]` | Champs métier |
| `indexes` | `[...]` | Index SQL supplémentaires (optionnel) |
| `options.timestamps` | `true` | `created_at` / `updated_at` auto (optionnel) |
| `options.soft_delete` | `true` | `deleted_at` soft-delete (optionnel) |

| Clé de champ | Exemple | Rôle |
|---|---|---|
| `name` | `"entity_name"` | Nom snake_case (pas `id`) |
| `type` | `"string"` | Type Forge (12 valeurs) |
| `label` | `"Nom entité"` | Libellé UI (optionnel) |
| `required` | `true` | Obligatoire côté formulaire |
| `nullable` | `false` | NULL en SQL |
| `unique` | `false` | UNIQUE KEY |
| `default` | `"default"` | Valeur par défaut |
| `max_length` | `100` | Longueur max (string, email, password) |
| `min` | `0` | Valeur min (integer, float, decimal) |
| `max` | `100` | Valeur max |
| `precision` | `10` | Chiffres totaux (decimal) |
| `scale` | `2` | Décimales (decimal) |

**Types Forge disponibles** : `string`, `text`, `integer`, `big_integer`, `float`,
`decimal`, `boolean`, `date`, `datetime`, `email`, `password`, `json`.

**La clé `id` est interdite** dans `fields[]` — Forge génère automatiquement la clé primaire.

---

## 6. Table de correspondance legacy → canonique

| Legacy | Canonique | Conversion | Risque |
|---|---|---|---|
| `format_version: 1` | `schema_version: "1.0"` | Remplacement | Faible |
| `entity` | `name` | Renommage | Faible |
| `table` | `table` | Identique | Nul |
| `description` | `description` | Identique | Nul |
| `column` | *(absent)* | Supprimé — dérivé du `name` à la génération | Faible |
| `sql_type: "INT"` | `type: "integer"` | Mapping SQL → Forge | Moyen |
| `sql_type: "BIGINT"` | `type: "big_integer"` | Mapping SQL → Forge | Moyen |
| `sql_type: "VARCHAR(n)"` | `type: "string"` + `max_length: n` | Parsing | Moyen |
| `sql_type: "TEXT"` | `type: "text"` | Direct | Faible |
| `sql_type: "FLOAT"/"DOUBLE"` | `type: "float"` | Mapping | Faible |
| `sql_type: "DECIMAL(p,s)"` | `type: "decimal"` + `precision` + `scale` | Parsing | Moyen |
| `sql_type: "BOOLEAN"` | `type: "boolean"` | Direct | Faible |
| `sql_type: "DATE"` | `type: "date"` | Direct | Nul |
| `sql_type: "DATETIME"` | `type: "datetime"` | Direct | Nul |
| `python_type` | *(absent)* | Supprimé — dérivé du type Forge | Faible |
| `primary_key: true` + `auto_increment: true` | *(absent — `id` auto)* | Suppression | Moyen |
| `nullable` | `nullable` | Identique | Nul |
| `unique` | `unique` | Identique | Nul |
| `default` | `default` | Identique | Faible |
| `constraints.not_empty` | `required: true` | Mapping | Faible |
| `constraints.max_length` | `max_length` | Déplacement | Faible |
| `constraints.min_value` | `min` | Renommage | Faible |
| `constraints.max_value` | `max` | Renommage | Faible |
| `constraints.pattern` | *(absent en canonique v1.0)* | Non supporté | Élevé |
| `form.field: "email"` | `type: "email"` | Fusion dans le type | Moyen |
| `form.field: "datetime"` | `type: "datetime"` | Fusion dans le type | Faible |
| `list.*` | *(absent en canonique v1.0)* | Non supporté | Faible |
| `media` | *(absent en canonique v1.0)* | Hors périmètre | Élevé |
| `rbac` | *(absent en canonique v1.0)* | Hors périmètre | Élevé |

---

## 7. Conversions simples (risque faible)

- `format_version: 1` → `schema_version: "1.0"`
- `entity` → `name`
- `table` → `table` (inchangé)
- `description` → `description` (inchangé)
- `column` → supprimé (la génération peut dériver depuis `name`)
- `python_type` → supprimé (la génération peut dériver depuis le type Forge)
- `nullable` → `nullable` (inchangé)
- `unique` → `unique` (inchangé)
- `default` → `default` (inchangé)
- `constraints.not_empty: true` → `required: true`
- `constraints.max_length: n` → `max_length: n`
- `sql_type: "INT"` → `type: "integer"`
- `sql_type: "BIGINT"` → `type: "big_integer"`
- `sql_type: "TEXT"` → `type: "text"`
- `sql_type: "BOOLEAN"/"BOOL"` → `type: "boolean"`
- `sql_type: "DATE"` → `type: "date"`
- `sql_type: "DATETIME"` → `type: "datetime"`
- `sql_type: "FLOAT"/"DOUBLE"` → `type: "float"`

---

## 8. Conversions risquées

| Conversion | Risque | Explication |
|---|---|---|
| `sql_type: "VARCHAR(n)"` → `type: "string"` + `max_length: n` | Moyen | Parsing de la longueur dans `"VARCHAR(100)"` |
| `sql_type: "DECIMAL(p,s)"` → `type: "decimal"` + `precision`/`scale` | Moyen | Parsing de deux valeurs |
| `sql_type: "CHAR(n)"` → `type: "string"` + `max_length: n` | Moyen | Perte de la sémantique CHAR vs VARCHAR |
| `primary_key + auto_increment` → suppression du champ `id` | Moyen | `id` est maintenant géré automatiquement — le retirer des fichiers JSON |
| `constraints.min_value` / `max_value` → `min` / `max` | Faible | Renommage de clé |
| `constraints.pattern` | Élevé | Pas d'équivalent en canonique v1.0 |
| `form.field: "email"` → `type: "email"` | Moyen | Fusion du widget dans le type : change la sémantique |
| `form.field: "string"` → `type: "string"` (idem) | Faible | Pas de conflit |
| `media` | Élevé | Hors périmètre canonique v1.0 — ticket séparé requis |
| `rbac` | Élevé | Hors périmètre canonique v1.0 — ticket séparé requis |
| Génération depuis `column` → dérivation | Moyen | SQL actuel utilise `column` (PascalCase), le canonique dérive de `name` |

---

## 9. Tests impactés

| Fichier | Dépendance | Impact |
|---|---|---|
| `tests/test_entity_model_cli.py` (18 tests) | Format legacy exclusivement (`format_version: 1`, `entity`, `sql_type`, `python_type`) | Tous à réécrire en format canonique |
| `tests/test_entity_validate_command.py` (23 tests) | Format canonique — projets tmp | Aucun |
| `tests/test_entity_semantic_validation.py` (41 tests) | Format canonique — projets tmp | Aucun |
| `tests/test_entity_validation_error_codes.py` (58 tests) | Format canonique — projets tmp | Aucun |
| `tests/test_entity_validate_json_output.py` (48 tests) | Format canonique — projets tmp | Aucun |

**Total tests impactés** : 18 (dans `test_entity_model_cli.py`).

---

## 10. Entités impactées dans le dépôt

| Fichier | Format | Champs | Difficultés |
|---|---|---|---|
| `mvc/entities/media/media.json` | Legacy | 11 champs dont `id` (à supprimer), `column`, `sql_type`, `constraints` | `constraints.min_value` sur `entity_id`, `size`, `position` |
| `mvc/entities/relations.json` | Legacy (`format_version: 1`, vide) | — | Simple : changer `format_version` → `schema_version`, retirer la clé |

---

## 11. Stratégie recommandée

**Option retenue : normaliseur canonique → legacy (adaptateur interne)**

L'approche consiste à créer une couche de traduction `canonical → legacy_normalized` qui
permet à `build_entity_sql()` et `build_entity_base()` de continuer à fonctionner
sans modification, pendant une phase de transition.

```
Canonique (schema_version 1.0)
    ↓ normalize_canonical_to_legacy()  [nouveau module]
Legacy normalisé (même dict que normalize_entity_definition() produit)
    ↓ build_entity_sql() / build_entity_base()  [inchangé]
Fichiers générés
```

**Pourquoi cet ordre ?**

1. Risque minimal : aucune réécriture du générateur SQL/Python dans un premier temps.
2. Réversible : si la traduction échoue, le legacy reste disponible.
3. Testable : les tests de l'adaptateur sont indépendants de la génération.
4. Progressif : permet de migrer un fichier à la fois.

**Alternatives écartées :**

- *Migration directe de `build_entity_sql`* : trop large, trop risquée, plusieurs centaines de lignes à modifier simultanément.
- *Double support dans `validation.py`* : cache la migration, viole le principe "ne pas ajouter de compatibilité cachée".
- *Compatibilité par détection automatique du format* : même problème.

---

## 12. Tickets proposés

| Ticket | Objectif | Priorité | Dépendances |
|---|---|---|---|
| **ENTITY-CONTRACT-011B** | Créer `normalize_canonical_to_legacy()` — traducteur canonique → legacy | Haute | 011A |
| **ENTITY-CONTRACT-011C** | Adapter `build:model` pour utiliser l'adaptateur si `schema_version` détecté | Haute | 011B |
| **ENTITY-CONTRACT-011D** | Migrer `tests/test_entity_model_cli.py` vers format canonique | Haute | 011B |
| **ENTITY-CONTRACT-011E** | Migrer `mvc/entities/media/media.json` vers format canonique | Moyenne | 011B |
| **ENTITY-CONTRACT-011F** | Migrer `mvc/entities/relations.json` vers format canonique | Faible | 011E |
| **ENTITY-CONTRACT-011G** | Brancher `entity:validate` dans `build:model` (reprendre 011) | Haute | 011C, 011D, 011E |

**Chemin minimal vers ENTITY-CONTRACT-011G** :
011A → 011B → 011C + 011D + 011E + 011F → 011G

---

## 13. Points délicats supplémentaires

- **`column` PascalCase** : le legacy stocke explicitement `column: "EntityName"`. Le canonique n'a pas de clé `column` — la génération devra dériver le nom de colonne depuis `name`. La convention actuelle (`_column_from_field_name()` dans `validation.py`) fait déjà ce dérivation. À utiliser dans le normaliseur.
- **`media` et `rbac`** : ces deux sections legacy n'ont pas d'équivalent dans `entity.schema.json` v1.0. La migration de `media.json` nécessitera de décider si ces sections doivent être archivées ou portées dans un futur `options.media` / `options.rbac`. Ces sections ne doivent pas être couvertes dans 011B-011G — tickets séparés recommandés.
- **`constraints.pattern`** : aucun équivalent en canonique v1.0. À déprécier ou à ajouter comme extension dans un ticket futur.
- **Structure de répertoire** : `build:model` lit `mvc/entities/<name>/<name>.json`, `entity:validate` lit tous les fichiers `rglob("*.json")`. Ils couvrent les mêmes fichiers mais via des méthodes différentes — pas de conflit.
