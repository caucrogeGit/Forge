# Valider les contrats JSON : forge entity:validate

`forge entity:validate` est la **commande officielle de diagnostic** des fichiers JSON canoniques Forge. Elle vérifie chaque entité et `relations.json` avant toute génération.

Elle ne génère pas de fichiers — elle diagnostique.

```
forge entity:validate
    │
    ├── vérifie chaque mvc/entities/<entité>/<entité>.json
    ├── vérifie mvc/entities/relations.json
    ├── applique la validation JSON Schema (structure)
    └── applique la validation sémantique Forge (cohérence)
```

---

## Commandes

```bash
python forge.py entity:validate
```

Sortie humaine — diagnostic lisible par un développeur.

```bash
python forge.py entity:validate --json
```

Sortie JSON machine — exploitable par un outil, un CI, ou un script.

Dans un projet installé, la commande peut aussi s'invoquer directement avec `forge entity:validate`.

---

## Sortie humaine

```
[OK] Entité Media valide.
[OK] relations.json valide.

Validation terminée : 2 fichiers valides, 0 erreur.
```

En cas d'erreur :

```
[ERREUR] mvc/entities/article/article.json
  - $.fields[0].type : 'VARCHAR(255)' n'est pas un type Forge valide.
    Conseil : Corrigez le fichier selon schemas/entity.schema.json.

Validation terminée : 1 fichier invalide, 1 erreur.
```

La sortie humaine est destinée au développeur. Elle ne doit pas être parsée par des outils.

---

## Sortie JSON machine

```bash
python forge.py entity:validate --json
```

```json
{
  "valid": true,
  "files_checked": 2,
  "files_valid": 2,
  "errors_count": 0,
  "warnings_count": 0,
  "errors": [],
  "warnings": []
}
```

| Champ | Rôle |
|---|---|
| `valid` | `true` si aucune erreur, `false` sinon |
| `files_checked` | nombre de fichiers vérifiés |
| `files_valid` | nombre de fichiers sans erreur |
| `errors_count` | nombre total d'erreurs |
| `warnings_count` | nombre total d'avertissements |
| `errors` | liste d'objets d'erreur structurés |
| `warnings` | liste d'avertissements |

### Structure d'une erreur JSON

```json
{
  "code": "FORGE_ENTITY_SCHEMA_INVALID",
  "file": "mvc/entities/article/article.json",
  "path": "$.fields[0].type",
  "message": "'VARCHAR(255)' n'est pas valide sous l'un des schémas indiqués.",
  "hint": "Corrigez le fichier selon schemas/entity.schema.json.",
  "phase": "schema"
}
```

| Champ | Rôle |
|---|---|
| `code` | code stable — préfixé `FORGE_` |
| `file` | chemin relatif du fichier concerné |
| `path` | chemin JSON vers la valeur en erreur (`$.fields[0].type`) |
| `message` | message humain de la violation |
| `hint` | conseil de correction |
| `phase` | étape de validation (`json`, `schema`, `semantic`, `runtime`) |

---

## Phases de validation

| Phase | Ce qui est vérifié |
|---|---|
| `json` | fichier JSON syntaxiquement invalide (illisible, mal formé) |
| `schema` | non-conformité au JSON Schema (`entity.schema.json`, `relations.schema.json`) |
| `semantic` | incohérences Forge entre fichiers ou règles métier du framework |
| `runtime` | erreur d'exécution de la validation elle-même (ex : projet manquant) |

La validation s'arrête sur la première phase en erreur pour chaque fichier.

---

## Codes d'erreur stables

Les codes sont préfixés `FORGE_` et organisés par famille.

### FORGE_ENTITY_*

| Code | Déclencheur |
|---|---|
| `FORGE_ENTITY_JSON_INVALID` | fichier JSON syntaxiquement invalide |
| `FORGE_ENTITY_SCHEMA_MISSING` | `schema_version` absente ou non reconnue |
| `FORGE_ENTITY_SCHEMA_INVALID` | violation du JSON Schema (`entity.schema.json`) |
| `FORGE_ENTITY_DUPLICATE_FIELD` | deux champs avec le même nom dans `fields[]` |
| `FORGE_ENTITY_RESERVED_PYTHON_NAME` | nom de champ réservé par Python |
| `FORGE_ENTITY_DUPLICATE_TABLE` | deux entités partagent le même nom de table |
| `FORGE_ENTITY_INVALID_INDEX` | index déclaré sur un champ inexistant dans `fields[]` |

### FORGE_RELATION_*

| Code | Déclencheur |
|---|---|
| `FORGE_RELATION_SCHEMA_INVALID` | violation du JSON Schema (`relations.schema.json`) |
| `FORGE_RELATION_UNKNOWN_ENTITY` | relation vers une entité non déclarée |
| `FORGE_RELATION_DUPLICATE` | deux relations avec le même nom sur la même entité |
| `FORGE_RELATION_INVALID_ON_DELETE` | valeur `on_delete` non autorisée |
| `FORGE_RELATION_FK_COLLISION` | deux clés étrangères portent le même nom de colonne |

### FORGE_PIVOT_*

| Code | Déclencheur |
|---|---|
| `FORGE_PIVOT_SCHEMA_INVALID` | violation du JSON Schema (`pivot.schema.json`) |
| `FORGE_PIVOT_TABLE_COLLISION` | deux tables pivot portent le même nom |
| `FORGE_PIVOT_RESERVED_FIELD` | `pivot.fields[]` redéclare `id`, `from_key` ou `to_key` |
| `FORGE_PIVOT_KEY_COLLISION` | `from_key` et `to_key` portent le même nom |
| `FORGE_PIVOT_UNIQUE_PAIR_REQUIRED` | `unique_pair` n'est pas `true` |

---

## Erreurs fréquentes

**Oublier `schema_version` :**

```json
{ "name": "Article", "table": "article", "fields": [...] }
```

Erreur : `FORGE_ENTITY_SCHEMA_MISSING` — `schema_version` est obligatoire.

---

**Utiliser `format_version` :**

```json
{ "format_version": 1, ... }
```

Le format `format_version: 1` est **refusé** — `build:model` et `make:crud` lèvent une erreur.
Migrer vers le format canonique `schema_version: "1.0"` (voir `docs/entities/migration-legacy-vers-canonique.md`).

---

**Déclarer `id` dans `fields[]` :**

```json
{ "name": "id", "type": "integer" }
```

Erreur : `FORGE_ENTITY_SCHEMA_INVALID` — `id` est interdit dans `fields[]`.

---

**Utiliser `sql_type` ou `python_type` :**

```json
{ "name": "title", "sql_type": "VARCHAR(255)" }
```

Erreur : `FORGE_ENTITY_SCHEMA_INVALID` — clés inconnues interdites (`additionalProperties: false`).

---

**Utiliser un type SQL comme `type` :**

```json
{ "name": "title", "type": "VARCHAR(255)" }
```

Erreur : `FORGE_ENTITY_SCHEMA_INVALID` — `VARCHAR(255)` n'est pas un type Forge.

---

**Déclarer une relation vers une entité inexistante :**

```json
{ "type": "many_to_one", "from": "Article", "to": "NonExistant", "name": "ref" }
```

Erreur : `FORGE_RELATION_UNKNOWN_ENTITY` — l'entité cible doit être déclarée.

---

**Déclarer un index sur un champ inexistant :**

```json
"indexes": [{ "name": "idx_x", "fields": ["nonexistent"] }]
```

Erreur : `FORGE_ENTITY_INVALID_INDEX` — le champ ciblé doit exister dans `fields[]`.

---

**Redéclarer `id` ou les clés étrangères dans `pivot.fields[]` :**

```json
"fields": [{ "name": "article_id", "type": "integer" }]
```

Erreur : `FORGE_PIVOT_RESERVED_FIELD` — `id`, `from_key` et `to_key` sont réservés.

---

## Utilisation par les autres commandes

Certaines commandes Forge utilisent les contrats JSON comme garde-fou automatique. En cas d'erreur de validation, elles s'arrêtent et renvoient vers `entity:validate` pour le détail.

| Commande | Comportement en cas d'erreur |
|---|---|
| `forge build:model` | arrêt et message court — lancer `entity:validate` pour le détail |
| `forge make:crud` | arrêt et message court — lancer `entity:validate` pour le détail |
| `forge migration:diff --entity` | arrêt sur erreur de contrat |
| `forge migration:make --from-diff` | arrêt sur erreur de contrat |

Ces commandes doivent rester courtes en cas d'erreur. La commande `entity:validate` est le point d'entrée officiel pour le diagnostic complet.

---

## Usage en validation continue

La commande peut être intégrée dans un workflow CI sans configuration particulière :

```bash
python forge.py entity:validate
```

Code de retour : `0` si valide, non-zéro si erreur.

```bash
python forge.py entity:validate --json
```

La sortie JSON peut être exploitée par un outil ou un script pour extraire les erreurs et les présenter dans un rapport. La commande humaine suffit pour une validation simple ou une revue manuelle.

---

## Limites

- VS Code peut aider à la saisie via `$schema`, mais ne remplace pas `entity:validate` — les erreurs sémantiques (entités inconnues, collisions, doublons) ne sont pas détectées par l'éditeur.
- Les starters Forge utilisent tous le format canonique `schema_version: "1.0"`. Le format `format_version: 1` est refusé par `build:model` et `make:crud`.
- `entity:validate` valide les contrats JSON, pas l'état réel d'une base MariaDB déjà déployée — utiliser les commandes de migration pour comparer avec la base.
- La sortie JSON (`--json`) est un contrat d'outil maintenu par les tests — ne pas la parser manuellement en production sans vérifier la compatibilité de version.
