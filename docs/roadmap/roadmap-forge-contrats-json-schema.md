# Roadmap Forge — Contrats canoniques JSON Schema

> Roadmap autonome à ouvrir après la Phase 12 de consolidation Forge.
>
> Point de départ prévu : après `v1.0.0-beta.5`.
>
> Objectif : verrouiller les fichiers JSON canoniques des entités et relations Forge avec des contrats JSON Schema, une validation sémantique Forge, des erreurs stables, une sortie machine exploitable, une documentation complète et un branchement progressif dans les générateurs.

---

## 1. Positionnement

Cette roadmap est une roadmap autonome.

Elle ne remplace pas la roadmap générale de Forge et ne doit pas être intégrée à la consolidation en cours.

Elle démarre après :

```text
v1.0.0-beta.5
```

Elle prépare probablement une ou plusieurs bêtas suivantes, par exemple :

```text
v1.0.0-beta.6 — Contrats JSON Schema : schémas + validation
v1.0.0-beta.7 — Contrats JSON Schema : générateurs + documentation + clôture
```

Le découpage exact en versions sera décidé au moment de l’ouverture de cette roadmap, selon l’état réel du dépôt après Phase 12.

---

## 2. Pourquoi cette roadmap existe

Forge repose sur des fichiers JSON canoniques :

```text
mvc/entities/*.json
mvc/entities/relations.json
```

Ces fichiers décrivent les entités, les champs et les relations à partir desquels Forge génère :

```text
SQL
modèles _base.py
CRUD
migrations
documentation technique
futurs contrats consommables par Forge Design
```

Ces fichiers ne doivent donc pas rester des JSON libres.

Ils doivent devenir des contrats vérifiables :

```text
JSON canonique
↓
JSON Schema
↓
validation sémantique Forge
↓
génération SQL
↓
génération modèles
↓
génération CRUD
↓
futur Forge Design
```

---

## 3. Objectif général

Mettre en place une couche officielle de contrats JSON Schema autour des fichiers canoniques Forge afin de garantir que :

- les entités JSON sont strictement validées ;
- les clés inconnues sont refusées ;
- les types Forge sont bornés et documentés ;
- l’identifiant technique `id` est généré automatiquement ;
- le champ `id` est interdit dans `fields[]` ;
- les relations `many_to_one` sont déclarées proprement ;
- les relations `many_to_many` utilisent des tables pivot explicites ;
- les tables pivot ont un `id` technique ;
- les deux clés étrangères des pivots ont une contrainte `UNIQUE` ;
- les attributs spécifiques aux tables pivot sont autorisés mais contrôlés ;
- les générateurs refusent les JSON invalides ;
- les erreurs sont lisibles pour un humain ;
- les erreurs sont aussi exploitables par une interface future ;
- la documentation explique les règles et les limites ;
- Forge Design pourra plus tard consommer ces contrats sans les redéfinir.

---

## 4. Principes directeurs

- Le JSON d’entité reste la source canonique.
- JSON Schema verrouille la forme.
- Le validateur Forge vérifie la cohérence réelle.
- Le générateur SQL produit un SQL visible et auditable.
- Les fichiers générés restent lisibles.
- Les fichiers utilisateur ne sont pas écrasés brutalement.
- Les commandes doivent échouer clairement en cas de contrat invalide.
- Les erreurs doivent être exploitables par un humain et par une interface future.
- La documentation fait partie du contrat.
- Forge Design consommera les contrats, mais ne les définira pas.

Formule de synthèse :

```text
Le JSON décrit.
Le schéma verrouille.
Forge valide.
Le générateur produit.
La documentation explique.
Le développeur garde la main.
```

---

## 5. Emplacement recommandé dans le dépôt

Fichier de roadmap :

```text
docs/roadmap/forge-json-schema-contracts-roadmap.md
```

Schémas JSON :

```text
schemas/
├── common.schema.json
├── field.schema.json
├── entity.schema.json
├── pivot.schema.json
├── relations.schema.json
└── forge.schema.index.json
```

Tests :

```text
tests/
├── test_entity_json_schema.py
├── test_relations_json_schema.py
├── test_entity_validate_command.py
├── test_entity_semantic_validation.py
├── test_entity_contract_generators.py
├── test_many_to_many_pivot_contracts.py
└── fixtures/
    └── entity_contracts/
        ├── valid/
        └── invalid/
```

Documentation :

```text
docs/entities/json-schema.md
docs/entities/entity-json.md
docs/entities/relations-json.md
docs/entities/pivot-tables.md
docs/entities/types-mariadb.md
docs/entities/entity-validation.md
docs/guides/vscode-json-schema.md
```

---

## 6. Décisions structurantes

### 6.1 Identifiant technique des entités

Chaque entité Forge possède automatiquement un identifiant technique :

```sql
id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT
```

Règles :

- `id` est généré par Forge ;
- `id` n’est pas déclaré dans `fields[]` ;
- `id` est réservé ;
- les relations pointent par défaut vers `id`.

### 6.2 Champs système

Les champs système doivent être gérés par options, pas comme des champs métier ordinaires.

Exemple :

```json
{
  "options": {
    "timestamps": true,
    "soft_delete": false
  }
}
```

Règles :

- `options.timestamps: true` génère `created_at` et `updated_at` ;
- `options.soft_delete: true` génère `deleted_at` ;
- ces champs restent visibles dans le SQL généré ;
- leur génération doit être documentée.

### 6.3 Relations séparées des entités

Les champs métier restent dans :

```text
mvc/entities/*.json
```

Les relations restent dans :

```text
mvc/entities/relations.json
```

Règle :

```text
L’entité décrit ce qu’elle est.
La relation décrit comment elle est liée.
```

### 6.4 Many-to-one

Une relation `many_to_one` génère une clé étrangère dans la table source.

Exemple :

```json
{
  "type": "many_to_one",
  "from": "Article",
  "to": "Category",
  "name": "category",
  "inverse_name": "articles",
  "nullable": false,
  "on_delete": "restrict"
}
```

SQL attendu :

```sql
category_id BIGINT UNSIGNED NOT NULL
```

avec une contrainte de clé étrangère vers :

```sql
categories(id)
```

### 6.5 Many-to-many

Une relation `many_to_many` génère une table pivot.

Règle Forge :

```text
Une table pivot many_to_many possède :
- un id technique ;
- deux clés étrangères ;
- une contrainte UNIQUE sur le couple des deux clés étrangères ;
- des attributs pivot optionnels.
```

Exemple SQL attendu :

```sql
CREATE TABLE article_tags (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    article_id BIGINT UNSIGNED NOT NULL,
    tag_id BIGINT UNSIGNED NOT NULL,

    position INT NULL,

    PRIMARY KEY (id),

    CONSTRAINT uq_article_tags_article_id_tag_id
        UNIQUE (article_id, tag_id),

    CONSTRAINT fk_article_tags_article_id
        FOREIGN KEY (article_id)
        REFERENCES articles(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_article_tags_tag_id
        FOREIGN KEY (tag_id)
        REFERENCES tags(id)
        ON DELETE CASCADE
);
```

Important :

```text
On n’utilise pas PRIMARY KEY(article_id, tag_id).
Le couple est unique, mais la clé primaire reste id.
```

---

# Bloc 1 — Socle des schémas JSON

## ENTITY-CONTRACT-001 — Créer `schemas/common.schema.json` — **livré**

### Objectif

Créer les définitions communes réutilisables par les autres schémas.

### Périmètre

À inclure :

- identifiant SQL ;
- nom d’entité PascalCase ;
- nom de champ snake_case ;
- nom de relation snake_case ;
- valeurs `on_delete` ;
- version de contrat ;
- définitions communes réutilisables.

### Hors périmètre

- ne pas créer encore `entity.schema.json` complet ;
- ne pas modifier les générateurs ;
- ne pas valider les fichiers projet.

### Validation

```bash
pytest
python -m compileall -q .
mkdocs build --strict
git diff --check
```

---

## ENTITY-CONTRACT-002 — Créer `schemas/field.schema.json` — **livré**

### Objectif

Créer le contrat réutilisable pour les champs Forge.

### Types Forge initiaux

```text
string
text
integer
big_integer
float
decimal
boolean
date
datetime
email
password
json
```

### Règles

- `name` obligatoire ;
- `type` obligatoire ;
- clés inconnues interdites ;
- `id` interdit ;
- `max_length` contrôlé ;
- `decimal` exige `precision` et `scale` ;
- `password` stocke un hash, jamais un mot de passe brut ;
- `json` reste un type Forge, mappé ensuite côté MariaDB.

### Hors périmètre

- ne pas ajouter `file`, `image`, `money`, `uuid`, `slug` ;
- ne pas intégrer de logique métier ;
- ne pas gérer les relations dans ce schéma.

---

## ENTITY-CONTRACT-003 — Créer `schemas/entity.schema.json` — **livré**

### Objectif

Créer le schéma officiel des fichiers :

```text
mvc/entities/*.json
```

### Structure cible

```json
{
  "$schema": "../../schemas/entity.schema.json",
  "schema_version": "1.0",
  "name": "Article",
  "table": "articles",
  "label": "Article",
  "plural_label": "Articles",
  "description": "Articles publiés sur le site.",
  "fields": [
    {
      "name": "title",
      "type": "string",
      "max_length": 255,
      "required": true
    }
  ],
  "options": {
    "timestamps": true,
    "soft_delete": false
  }
}
```

### Règles

- `schema_version`, `name`, `table`, `fields` obligatoires ;
- `additionalProperties: false` ;
- `fields[]` utilise `field.schema.json` ;
- `id` interdit dans `fields[]` ;
- `options.timestamps` autorise `created_at` et `updated_at` générés ;
- `options.soft_delete` autorise `deleted_at` généré.

---

## ENTITY-CONTRACT-004 — Créer `schemas/pivot.schema.json` — **livré**

### Objectif

Créer le contrat des tables pivot `many_to_many`.

### Structure cible

```json
{
  "table": "article_tags",
  "from_key": "article_id",
  "to_key": "tag_id",
  "id": true,
  "unique_pair": true,
  "on_delete": "cascade",
  "fields": [
    {
      "name": "position",
      "type": "integer",
      "nullable": true
    }
  ]
}
```

### Règles

- `id` technique obligatoire ;
- `unique_pair` obligatoire à `true` pour Forge 1.x ;
- `from_key` et `to_key` contrôlés ;
- `fields[]` accepte des attributs pivot ;
- `fields[]` ne peut pas contenir `id`, `from_key`, `to_key` ;
- pas de clé primaire composite.

---

## ENTITY-CONTRACT-005 — Créer `schemas/relations.schema.json` — **livré**

### Objectif

Créer le schéma officiel de :

```text
mvc/entities/relations.json
```

### Types supportés

```text
many_to_one
many_to_many
```

### Structure cible

```json
{
  "$schema": "../../schemas/relations.schema.json",
  "schema_version": "1.0",
  "relations": [
    {
      "type": "many_to_one",
      "from": "Article",
      "to": "Category",
      "name": "category",
      "inverse_name": "articles",
      "nullable": false,
      "on_delete": "restrict"
    },
    {
      "type": "many_to_many",
      "from": "Article",
      "to": "Tag",
      "name": "tags",
      "inverse_name": "articles",
      "pivot": {
        "table": "article_tags",
        "from_key": "article_id",
        "to_key": "tag_id",
        "id": true,
        "unique_pair": true,
        "on_delete": "cascade",
        "fields": []
      }
    }
  ]
}
```

### Hors périmètre

- pas de `one_to_one` ;
- pas de relation polymorphique ;
- pas de clé primaire composite ;
- pas de pivot historisé avec doublons autorisés.

---

## ENTITY-CONTRACT-006 — Créer `schemas/forge.schema.index.json` — **livré**

### Objectif

Créer un registre local des schémas Forge disponibles.

### Exemple

```json
{
  "schema_version": "1.0",
  "schemas": {
    "common": "./common.schema.json",
    "field": "./field.schema.json",
    "entity": "./entity.schema.json",
    "pivot": "./pivot.schema.json",
    "relations": "./relations.schema.json"
  }
}
```

### Usage

Ce registre pourra être utilisé par :

- la documentation ;
- les commandes de diagnostic ;
- Forge Design ;
- les tests de packaging.

---

# Bloc 2 — Validation Forge

## ENTITY-CONTRACT-007 — Ajouter `forge entity:validate` — **livré**

> Dépendance `jsonschema` officialisée dans `pyproject.toml` par ENTITY-CONTRACT-007-FIX-DEPENDENCY.

### Objectif

Ajouter une commande CLI de validation des fichiers canoniques.

### Commande

```bash
forge entity:validate
```

### Comportement attendu

- charger `mvc/entities/*.json` ;
- charger `mvc/entities/relations.json` si présent ;
- valider les entités contre `entity.schema.json` ;
- valider les relations contre `relations.schema.json` ;
- afficher un rapport humain clair ;
- retourner un code non nul si invalide.

### Exemple de sortie valide

```text
[OK] Entité Article valide.
[OK] Entité Category valide.
[OK] relations.json valide.

Validation terminée : 3 fichiers valides, 0 erreur.
```

### Exemple d’erreur

```text
[ERREUR] mvc/entities/article.json

Chemin :
$.fields[0].name

Valeur :
"id"

Raison :
Le champ "id" est réservé.

Conseil :
Supprimez ce champ. Forge génère automatiquement l’identifiant technique.
```

---

## ENTITY-CONTRACT-008 — Ajouter la validation sémantique Python ✓ livré

### Objectif

Compléter JSON Schema par des contrôles que le schéma ne peut pas garantir seul.

### Contrôles attendus

- doublons de champs ;
- noms réservés Python ;
- noms SQL dangereux ;
- index pointant vers des champs inexistants ;
- relations pointant vers des entités inexistantes ;
- collision entre FK générée et champ métier ;
- collision entre table pivot et table d’entité ;
- `set_null` interdit si `nullable = false` ;
- doublon de `many_to_many` déclaré dans les deux sens ;
- `pivot.unique_pair` obligatoire à `true` ;
- `pivot.fields[]` ne peut pas redéclarer `id`, `from_key` ou `to_key`.

### Livraison

Module `forge_cli/entities/entity_semantic_validate.py` — `SemanticError` + `validate_semantic()` — 15 contrôles.
Intégré dans `forge entity:validate` (Passe 2 après JSON Schema).
41 tests dans `tests/test_entity_semantic_validation.py`.

---

## ENTITY-CONTRACT-009 — Ajouter des codes d’erreur stables ✓ livré

### Objectif

Normaliser les erreurs de validation avec des codes stables.

### Codes livrés (18)

```text
FORGE_ENTITY_JSON_INVALID
FORGE_ENTITY_SCHEMA_MISSING
FORGE_ENTITY_SCHEMA_INVALID
FORGE_ENTITY_DUPLICATE_FIELD
FORGE_ENTITY_RESERVED_PYTHON_NAME
FORGE_ENTITY_DUPLICATE_TABLE
FORGE_ENTITY_INVALID_INDEX
FORGE_RELATION_SCHEMA_INVALID
FORGE_RELATION_UNKNOWN_ENTITY
FORGE_RELATION_DUPLICATE
FORGE_RELATION_INVALID_ON_DELETE
FORGE_RELATION_FK_COLLISION
FORGE_PIVOT_SCHEMA_INVALID
FORGE_PIVOT_TABLE_COLLISION
FORGE_PIVOT_RESERVED_FIELD
FORGE_PIVOT_KEY_COLLISION
FORGE_PIVOT_UNIQUE_PAIR_REQUIRED
```

### Usage

Ces codes doivent pouvoir servir :

- aux tests ;
- à la documentation ;
- à la sortie JSON ;
- à Forge Design ;
- aux futures traductions.

### Livraison

Module `forge_cli/entities/entity_validation_errors.py` — liste centrale `ALL_CODES`.
`SemanticError` porte désormais `code`, `file`, `path`, `message`, `hint`.
Sortie humaine affiche `Code :` pour toutes les erreurs (JSON Schema + sémantiques).
58 tests dans `tests/test_entity_validation_error_codes.py`.

---

## ENTITY-CONTRACT-010 — Ajouter `forge entity:validate --json` ✓ livré

### Objectif

Ajouter une sortie machine exploitable par des outils.

### Format livré

```json
{
  "valid": false,
  "files_checked": 2,
  "files_valid": 0,
  "errors_count": 3,
  "warnings_count": 0,
  "errors": [
    {
      "code": "FORGE_ENTITY_SCHEMA_INVALID",
      "file": "mvc/entities/article.json",
      "path": "$.fields.0.name",
      "message": "'id' should not be valid under {'const': 'id'}",
      "hint": "Corrigez le fichier selon schemas/entity.schema.json.",
      "phase": "schema"
    }
  ],
  "warnings": []
}
```

### Règles

- la sortie JSON doit être stable ;
- elle ne doit pas contenir de traces inutiles ;
- elle doit être exploitable par Forge Design plus tard.

### Livraison

Option `--json` dans `forge entity:validate`.
Refactorisation de `entity_validate.py` : collecte structurée → sortie humaine ou JSON.
Phases : `json`, `schema`, `semantic`, `runtime`.
48 tests dans `tests/test_entity_validate_json_output.py`.

---

# Bloc 3 — Branchement dans les générateurs

## ENTITY-CONTRACT-011 — Brancher la validation dans `forge build:model` ✓ CLÔTURÉ (011A–011G livrés)

> **Note de structure** : ENTITY-CONTRACT-011 est le ticket parent.
> Il a été découpé en sous-tickets 011A–011G pour lever les préconditions une par une.
> ENTITY-CONTRACT-012 reprend la numérotation normale (make:crud).
>
> | Sous-ticket | Sujet | État |
> |---|---|---|
> | 011A | Audit migration build:model vers canonique | ✓ livré |
> | 011B | Normaliseur canonique pour build:model | ✓ livré |
> | 011C | Routage build:model vers normaliseur canonique | ✓ livré |
> | 011D | Tests build:model canoniques | ✓ livré |
> | 011E | Migrer media.json vers canonique | ✓ livré |
> | 011F | Migrer relations.json vers canonique | ✓ livré |
> | 011G | Reprendre le branchement strict entity:validate dans build:model | ✓ livré |

### Objectif

Empêcher la génération de modèles depuis des entités invalides.

### Comportement attendu

Avant génération :

```text
1. validation JSON Schema ;
2. validation sémantique Forge ;
3. génération seulement si tout est valide.
```

### Erreur attendue

```text
Erreur : les entités Forge sont invalides.
Conseil : lancez forge entity:validate pour obtenir le détail.
```

### Blocage identifié (2026-05)

`build:model` et `entity:validate` utilisent deux systèmes de validation incompatibles :

| Système | Clé détection | Champs | Usage |
|---|---|---|---|
| Legacy (`model.py`, `validation.py`) | `format_version: 1` | `entity`, `sql_type`, `python_type` | `build:model` actuel |
| Canonique (`entity_validate.py`) | `schema_version: "1.0"` | `name`, `fields[].type` (Forge types) | `entity:validate` |

Un fichier valide pour l'un est invalide pour l'autre.
Brancher la validation JSON Schema avant `build:model` bloquerait :
- Le dépôt réel (`mvc/entities/media/media.json` est en format legacy → `entity:validate` le rejette)
- Tous les tests existants de `build:model` (`test_entity_model_cli.py` utilise le format legacy)

Même si la validation JSON Schema passait, la génération échouerait : `build_entity_sql`,
`build_entity_base`, etc. lisent `sql_type`, `python_type`, `column` — absents du format canonique.

### Précondition requise

Un ticket de migration doit précéder ENTITY-CONTRACT-011. Plan détaillé dans :
`docs/history/audits/entity-contract-build-model-migration-audit.md`

---

## ENTITY-CONTRACT-011A — Audit migration build:model vers format canonique ✓ livré

### Objectif

Documenter précisément l'incompatibilité entre `build:model` (format legacy) et
`entity:validate` (format canonique) et proposer un plan de migration découpé.

### Livraison

Document d'audit complet dans :
`docs/history/audits/entity-contract-build-model-migration-audit.md`

Contenu : flux build:model, format legacy (8 clés racine, 12 clés de champ),
format canonique (12 types Forge), table de correspondance complète,
stratégie recommandée (normaliseur canonique→legacy), 6 tickets proposés.

---

## ENTITY-CONTRACT-011B — Créer normalize_canonical_to_legacy() ✓ livré

### Objectif

Créer un traducteur interne `canonical → legacy_normalized` permettant à
`build_entity_sql()` et `build_entity_base()` de fonctionner sans modification.

### Résultat

- module `forge_cli/entities/canonical_model_normalizer.py` ;
- fonction `normalize_canonical_entity_for_model_build()` ;
- mapping complet des 12 types Forge → sql_type + python_type ;
- id technique généré automatiquement (BIGINT UNSIGNED, PK, AUTO_INCREMENT) ;
- timestamps et soft_delete gérés comme champs système DATETIME ;
- indexes ignorés (non supportés par build:model) ;
- `CanonicalNormalizationError` pour les types inconnus ou decimal sans precision/scale ;
- string sans max_length → VARCHAR(255) par défaut (documenté) ;
- boolean → BOOLEAN (et non TINYINT(1) — incompatible avec python_type='bool' dans _sql_family) ;
- 72 tests dans `tests/test_build_model_canonical_normalizer.py` ;
- dont une classe `TestLegacyCompatibility` qui passe la sortie dans validate_entity_definition().

---

## ENTITY-CONTRACT-011C — Adapter build:model pour le format canonique ✓ livré

### Objectif

Détection automatique du format (`schema_version` vs `format_version`) dans
`build:model` et appel du normaliseur canonique si nécessaire.

### Résultat

- `_load_all_entity_sources()` dans `model.py` : routage schema_version "1.0" → normaliseur ;
- `load_entity_definitions()` dans `relations.py` : même routage (relations lit aussi les entités) ;
- `_safe_load_entities()` dans `relations.py` : attrape aussi `CanonicalNormalizationError` ;
- support legacy préservé strictement inchangé ;
- 35 tests dans `tests/test_build_model_canonical_routing.py` ;
- `build:model` accepte désormais le format canonique via normalisation interne ;
- `entity:validate` n'est pas encore branché comme garde-fou global (→ 011G).

---

## ENTITY-CONTRACT-011D — Migrer tests/test_entity_model_cli.py ✓ livré

### Objectif

Réécrire les 18 tests de `test_entity_model_cli.py` en format canonique
(`schema_version: "1.0"`) pour valider que `build:model` fonctionne
end-to-end avec le nouveau format via le normaliseur.

### Résultat

- `tests/test_entity_model_cli.py` réécrit : 18 tests → 20 tests (20/20 passent).
- Fixtures canoniques : `_article()`, `_commande()`, `_relations_vides()`.
- Fixtures legacy conservées : `_legacy_contact()`, `_legacy_commande()`, `_legacy_relations()`.
- 2 tests maintenus en legacy : `test_sync_relations_writes_only_relations_sql` (FK complexe),
  `test_sync_entity_does_not_touch_manual_py` (sync_entity non migré).
- 2 nouveaux tests de non-régression legacy : `test_legacy_build_model_validates_then_writes`,
  `test_legacy_check_model_preserves_entity_name`.
- `test_build_model_accepts_short_and_mixed_entity_json` → renommé
  `test_build_model_generates_correct_sql_and_base_py`, vérifie `Id BIGINT UNSIGNED NOT NULL`.
- Suite complète : 0 régression.

---

## ENTITY-CONTRACT-011E — Migrer mvc/entities/media/media.json ✓ livré

### Objectif

Convertir `mvc/entities/media/media.json` (11 champs, format legacy) vers
le format canonique `schema_version: "1.0"`.

### Résultat

- `mvc/entities/media/media.json` migré vers `schema_version: "1.0"`.
- Champ `id` supprimé (auto-injecté par le normaliseur comme BIGINT UNSIGNED PK AI).
- 10 champs métier conservés, tous convertis avec leur type Forge.
- `created_at` déclaré comme champ `datetime` explicite (sans `options.timestamps` qui
  ajouterait `updated_at` absent du legacy).
- `constraints.min_value` → `min`, `constraints.not_empty` non représentable
  dans le schéma canonique (perte documentée, conservatrice).
- `role.default: "default"` et `position.default: 0` conservés via `default`.
- `alt_text` conservé avec `nullable: true`.
- `entity:validate` : `[OK] Entité Media valide.` — seul `relations.json` encore legacy.
- `build:model --dry-run` : fonctionne via le routage canonique → normaliseur.
- 15 tests dans `tests/test_media_entity_canonical.py` (15/15 passent).
- Suite complète : 0 régression.

---

## ENTITY-CONTRACT-011F — Migrer mvc/entities/relations.json ✓ livré

### Objectif

Convertir `mvc/entities/relations.json` (vide, `format_version: 1`) vers
`schema_version: "1.0"`.

### Résultat

- `mvc/entities/relations.json` migré : `format_version: 1` → `schema_version: "1.0"` + `$schema`.
- Aucune relation présente — liste `relations: []` conservée intacte.
- `entity:validate` : `valid: true, errors_count: 0` — dépôt entièrement propre.
- `build:model` : fonctionne via correction minimale de `_validate_relations_root()` dans
  `relations.py` — détecte `schema_version: "1.0"` et ne requiert plus `format_version`.
  (Déviation documentée : le ticket interdisait de modifier `relations.py`, mais l'exigence
  "build:model continue à fonctionner" l'imposait. Correction en 4 lignes, même pattern que 011C.)
- 14 tests dans `tests/test_relations_entity_canonical.py` (14/14 passent).
- Suite complète : 0 régression.

---

## ENTITY-CONTRACT-011G — Brancher entity:validate dans build:model (reprise de 011) ✓ livré

### Objectif

Reprendre ENTITY-CONTRACT-011 une fois 011C, 011D, 011E et 011F livrés.

### Comportement attendu

```text
Erreur : les entités Forge sont invalides.
Conseil : lancez forge entity:validate pour obtenir le détail.
```

### Rapport de livraison

**Fichiers modifiés :**

- `forge_cli/entities/entity_validate.py` — ajout de `collect_entity_validation_results(entities_root)` : valide uniquement les entités canoniques (`schema_version: "1.0"`) ; dégradation douce si `jsonschema` absent ; retourne `dict` avec `errors`, `warnings`, `files_checked`, `files_valid`.
- `forge_cli/entities/model.py` — ajout de `_assert_contracts_valid(entities_root)` ; appel en tête de `build_model()` avant `_validate_model_or_raise()`.
- `tests/test_media_entity_canonical.py`, `tests/test_relations_entity_canonical.py` — retrait d'imports `pytest` inutilisés détectés par ruff.

**Fichiers créés :**

- `tests/test_build_model_entity_validation.py` — 11 tests : projet valide génère, projet invalide lève `ModelValidationError`, aucun fichier généré, message court avec conseil `entity:validate`, pas de traceback Python, API `collect_entity_validation_results()` détaillée, format `--json` inchangé, non-régression sur dépôt réel.

**Décision clé — filtre canonique dans le garde :**

`collect_entity_validation_results()` ignore les entités au format legacy (`format_version: 1`) : elles sont validées par `_validate_model_or_raise()` à l'étape suivante. Ce filtre était nécessaire pour ne pas bloquer les tests meta qui utilisent des fixtures legacy en `tmp_path`.

**Résultat :** 10 961 tests passés, 6 ignorés, 0 régression.

---

## ENTITY-CONTRACT-012 — Brancher la validation dans `forge make:crud`

### Objectif

Empêcher la génération CRUD depuis un contrat invalide.

### Périmètre

- auditer l’entrée actuelle de `make:crud` ;
- valider l’entité ciblée ;
- valider les relations nécessaires ;
- refuser les JSON invalides ;
- ne pas refondre le CRUD.

---

## ENTITY-CONTRACT-013 — Brancher la validation dans les migrations

### Objectif

Sécuriser les commandes qui déduisent ou appliquent du SQL depuis les entités.

### Commandes concernées

```text
forge migration:make
forge migration:diff
forge db:apply
```

### Règle

Aucune migration générée depuis un contrat invalide.

---

## ENTITY-CONTRACT-014 — Adapter les générateurs d’entités

### Objectif

Faire produire aux générateurs Forge des fichiers déjà conformes.

### Règles

Les entités générées doivent contenir :

- `$schema` ;
- `schema_version` ;
- `name` ;
- `table` ;
- `fields` ;
- aucun champ `id`.

---

# Bloc 4 — Relations et pivots

## ENTITY-CONTRACT-015 — Verrouiller la génération `many_to_one`

### Objectif

Garantir que `many_to_one` génère une FK claire et valide.

### Règles

- FK générée dans la table source ;
- nom par défaut : `<relation_name>_id` ;
- type : `BIGINT UNSIGNED` ;
- référence vers `target_table(id)` ;
- `on_delete` contrôlé ;
- index selon règle Forge.

---

## ENTITY-CONTRACT-016 — Verrouiller la génération `many_to_many`

### Objectif

Garantir que `many_to_many` génère une table pivot conforme.

### Règles

- table pivot dédiée ;
- `id` technique ;
- deux FK ;
- `UNIQUE(from_key, to_key)` ;
- aucun `PRIMARY KEY(from_key, to_key)` ;
- attributs pivot optionnels.

---

## ENTITY-CONTRACT-017 — Autoriser les attributs de pivot contrôlés

### Objectif

Permettre des champs spécifiques sur la table pivot.

### Exemple

```json
"fields": [
  {
    "name": "position",
    "type": "integer",
    "nullable": true
  },
  {
    "name": "note",
    "type": "string",
    "max_length": 255,
    "nullable": true
  }
]
```

### Interdictions

- `id` ;
- `article_id` si c’est `from_key` ;
- `tag_id` si c’est `to_key` ;
- noms de champs en collision avec les colonnes techniques ;
- types non autorisés.

---

## ENTITY-CONTRACT-018 — Tester les pivots many-to-many

### Objectif

Ajouter des tests de non-régression sur les pivots.

### Tests minimaux

- pivot avec `id` généré ;
- pivot avec `PRIMARY KEY(id)` ;
- pivot avec `UNIQUE(from_key, to_key)` ;
- absence de `PRIMARY KEY(from_key, to_key)` ;
- attribut pivot généré ;
- collision avec clé technique refusée ;
- `unique_pair: false` refusé pour Forge 1.x.

---

# Bloc 5 — Documentation officielle des contrats JSON

## ENTITY-CONTRACT-DOC-001 — Documenter le rôle du JSON canonique

### Objectif

Expliquer pourquoi les fichiers JSON d’entité sont la source canonique de Forge.

### Page cible

```text
docs/entities/json-schema.md
```

### Contenu attendu

- rôle du JSON canonique ;
- différence entre JSON canonique, JSON Schema et validateur Forge ;
- place du SQL généré ;
- place des modèles `_base.py` ;
- limites assumées.

---

## ENTITY-CONTRACT-DOC-002 — Documenter `entity.schema.json`

### Objectif

Documenter la structure officielle d’une entité Forge.

### Page cible

```text
docs/entities/entity-json.md
```

### Contenu attendu

- exemple minimal valide ;
- exemple complet ;
- clés obligatoires ;
- clés optionnelles ;
- rôle de `schema_version` ;
- rôle de `$schema` ;
- règle du champ `id` automatique ;
- règle des champs système.

---

## ENTITY-CONTRACT-DOC-003 — Documenter `relations.schema.json`

### Objectif

Documenter la structure officielle de `relations.json`.

### Page cible

```text
docs/entities/relations-json.md
```

### Contenu attendu

- exemple minimal ;
- `many_to_one` ;
- `many_to_many` ;
- `from`, `to`, `name`, `inverse_name` ;
- `nullable` ;
- `on_delete` ;
- erreurs fréquentes.

---

## ENTITY-CONTRACT-DOC-004 — Documenter les tables pivot many-to-many

### Objectif

Documenter explicitement la décision Forge sur les pivots.

### Page cible

```text
docs/entities/pivot-tables.md
```

### Contenu attendu

- pourquoi la table pivot a un `id` technique ;
- pourquoi on utilise `UNIQUE(from_key, to_key)` ;
- pourquoi on refuse `PRIMARY KEY(from_key, to_key)` ;
- comment ajouter des attributs pivot ;
- exemples SQL ;
- exemples JSON ;
- limites assumées.

---

## ENTITY-CONTRACT-DOC-005 — Documenter le mapping types Forge → MariaDB

### Objectif

Publier la table de correspondance officielle.

### Page cible

```text
docs/entities/types-mariadb.md
```

### Mapping initial

| Type Forge | MariaDB généré | Remarque |
|---|---|---|
| `string` | `VARCHAR(n)` | `max_length` requis ou défaut Forge documenté |
| `text` | `TEXT` | contenu long |
| `integer` | `INT` | entier standard |
| `big_integer` | `BIGINT` | gros entier |
| `float` | `DOUBLE` | mesures, pas argent |
| `decimal` | `DECIMAL(p,s)` | précision obligatoire |
| `boolean` | `TINYINT(1)` | booléen MariaDB |
| `date` | `DATE` | date |
| `datetime` | `DATETIME` | date + heure |
| `email` | `VARCHAR(255)` | validation applicative |
| `password` | `VARCHAR(255)` | hash uniquement |
| `json` | `LONGTEXT` + stratégie JSON | selon choix Forge documenté |

---

## ENTITY-CONTRACT-DOC-006 — Documenter `forge entity:validate`

### Objectif

Documenter la commande de validation.

### Page cible

```text
docs/entities/entity-validation.md
```

### Contenu attendu

- usage simple ;
- usage avec `--json` ;
- exemples d’erreurs ;
- codes d’erreur ;
- différence entre erreur de schéma et erreur sémantique ;
- usage en CI.

---

## ENTITY-CONTRACT-DOC-007 — Documenter l’autocomplétion VS Code

### Objectif

Expliquer comment utiliser les schémas dans l’éditeur.

### Page cible

```text
docs/guides/vscode-json-schema.md
```

### Contenu attendu

- rôle de `$schema` ;
- schéma local prioritaire ;
- exemple de fichier entité ;
- aide à la saisie ;
- refus des clés inconnues ;
- limites de JSON Schema ;
- rappel : Forge ne dépend pas d’Internet pour valider un projet.

---

## ENTITY-CONTRACT-DOC-008 — Documenter les limites assumées

### Objectif

Éviter que cette roadmap soit interprétée comme une refonte complète de Forge.

### Contenu attendu

Cette roadmap ne couvre pas :

- Forge Design ;
- un éditeur graphique ;
- un ORM ;
- les relations polymorphiques ;
- `one_to_one` ;
- les clés primaires personnalisées ;
- le multi-SGBD ;
- les types métier avancés ;
- les migrations automatiques d’anciens formats non stabilisés.

---

# Bloc 6 — Expérience développeur et tests

## ENTITY-CONTRACT-019 — Ajouter les fixtures canoniques

### Objectif

Créer des exemples valides et invalides utilisés par les tests.

### Structure

```text
tests/fixtures/entity_contracts/
├── valid/
│   ├── article.json
│   ├── category.json
│   ├── tag.json
│   └── relations.json
└── invalid/
    ├── field_id_forbidden.json
    ├── unknown_type.json
    ├── duplicate_field.json
    ├── unknown_relation_target.json
    ├── pivot_without_unique_pair.json
    └── relation_set_null_not_nullable.json
```

---

## ENTITY-CONTRACT-020 — Vérifier les exemples documentaires

### Objectif

Faire en sorte que les exemples JSON de la documentation soient aussi testés.

### Règle

```text
Tout exemple JSON important présent dans la documentation doit exister comme fixture de test ou être couvert par un test de validation.
```

---

## ENTITY-CONTRACT-021 — Ajouter `forge schema:list`

### Objectif

Lister les schémas disponibles.

### Exemple

```bash
forge schema:list
```

Sortie :

```text
Schémas Forge disponibles :

- common      schemas/common.schema.json
- field       schemas/field.schema.json
- entity      schemas/entity.schema.json
- pivot       schemas/pivot.schema.json
- relations   schemas/relations.schema.json
```

### Priorité

Optionnel. À faire seulement si le socle principal est stable.

---

## ENTITY-CONTRACT-022 — Ajouter `forge schema:doctor`

### Objectif

Vérifier que les schémas Forge sont présents, lisibles et cohérents.

### Contrôles

- fichiers présents ;
- JSON valides ;
- `$ref` résolus ;
- `$id` cohérents ;
- schémas inclus dans le package ;
- chemins documentés corrects.

### Priorité

Optionnel mais utile avant publication.

---

# Bloc 7 — Clôture

## ENTITY-CONTRACT-023 — Clôturer la roadmap Contrats JSON Schema

### Objectif

Clôturer la roadmap autonome après validation complète.

### Vérifications finales

```bash
forge entity:validate
forge entity:validate --json
pytest
python -m compileall -q .
mkdocs build --strict
git diff --check
```

### Critères d’acceptation

- les schémas sont présents ;
- les schémas sont testés ;
- les entités générées sont conformes ;
- `relations.json` est conforme ;
- `id` est interdit dans `fields[]` ;
- `id` est généré automatiquement ;
- les pivots ont un `id` technique ;
- les pivots ont une contrainte `UNIQUE` sur les deux FK ;
- les attributs pivot sont possibles ;
- les générateurs refusent les JSON invalides ;
- les erreurs sont stables ;
- la sortie `--json` est exploitable ;
- la documentation est complète ;
- la roadmap générale pointe vers cette roadmap autonome ;
- Forge Design reste hors périmètre.

---

## 7. Validation finale globale

Commandes attendues à la fin de chaque ticket quand pertinent :

```bash
pytest
python -m compileall -q .
mkdocs build --strict
git diff --check
```

Commandes spécifiques à cette roadmap :

```bash
forge entity:validate
forge entity:validate --json
```

---

## 8. Ce que cette roadmap ne fait pas

Cette roadmap ne doit pas devenir une refonte générale de Forge.

Hors périmètre global :

- pas de Forge Design ;
- pas d’éditeur graphique ;
- pas d’ORM ;
- pas de relation polymorphique ;
- pas de `one_to_one` ;
- pas de clés primaires personnalisées ;
- pas de support multi-SGBD ;
- pas de paiement ;
- pas de logique métier applicative ;
- pas de refonte complète du CRUD ;
- pas de changement de philosophie SQL visible.

---

## 9. Dépendance future avec Forge Design

Forge Design devra consommer ces contrats, mais ne doit pas les définir.

Ordre correct :

```text
Forge Core définit les contrats.
Forge Core valide les contrats.
Forge Core génère depuis les contrats.
Forge Design lit les contrats.
Forge Design assiste l’utilisateur.
```

Cette séparation permet de garder Forge Core autonome et Forge Design optionnel.

---

## 10. Priorité recommandée après `v1.0.0-beta.5`

Ordre de démarrage recommandé :

1. `ENTITY-CONTRACT-001` — `common.schema.json`
2. `ENTITY-CONTRACT-002` — `field.schema.json`
3. `ENTITY-CONTRACT-003` — `entity.schema.json`
4. `ENTITY-CONTRACT-005` — `relations.schema.json`
5. `ENTITY-CONTRACT-007` — `forge entity:validate`
6. `ENTITY-CONTRACT-DOC-001` — rôle du JSON canonique

Les tickets optionnels `schema:list` et `schema:doctor` peuvent attendre.

---

## 11. Résumé exécutif

Cette roadmap transforme les fichiers JSON canoniques de Forge en véritables contrats vérifiables.

Elle renforce :

- la stabilité ;
- la lisibilité ;
- la génération SQL ;
- la génération CRUD ;
- la documentation ;
- les tests ;
- l’expérience développeur ;
- la préparation de Forge Design.

Elle ne grossit pas Forge inutilement : elle verrouille ce qui existe déjà et clarifie les règles du cœur.
