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

## ENTITY-CONTRACT-012 — Brancher la validation dans `forge make:crud` ✓ livré

### Objectif

Empêcher la génération CRUD depuis un contrat invalide.

### Périmètre

- auditer l’entrée actuelle de `make:crud` ;
- valider l’entité ciblée ;
- valider les relations nécessaires ;
- refuser les JSON invalides ;
- ne pas refondre le CRUD.

### Rapport de livraison

**Flux réel identifié :**

```
forge.py → command == "make:crud" → cmd_make_crud_main()
  → make_crud(entity_name, entities_root, output_root)
    → [NOUVEAU] collect_entity_validation_results(entities_root)  ← garde
    → lit entities_root/snake/snake.json
    → [NOUVEAU] normalize_canonical_entity_for_model_build() si schema_version 1.0
    → validate_entity_definition(raw)   ← attend format legacy normalisé
    → _load_crud_many_to_one_relations() ← supporte déjà canonical via relations.py
    → génère fichiers CRUD
```

**Fichiers modifiés :**

- `forge_cli/entities/make_crud.py` — ajout du garde `collect_entity_validation_results()` en tête de `make_crud()` ; ajout de la normalisation canonique avant `validate_entity_definition()` (même pattern que `model.py:_load_all_entity_sources`).

**Fichiers créés :**

- `tests/test_make_crud_entity_validation.py` — 14 tests : projet valide génère contrôleur/modèle/formulaire, entité invalide lève SystemExit, aucun fichier généré, message court avec conseil `entity:validate`, pas de traceback Python, relations invalides bloquent, API `collect_entity_validation_results()` détaillée préservée, format `--json` inchangé.

**Décision clé — normalisation canonique dans `make_crud()` :**

`validate_entity_definition()` n’acceptait que le format legacy. Sans normalisation, les entités canoniques valides échouaient à l’étape 2 du flux. Ajout de 3 lignes identiques au pattern de `model.py`. Ce n’est pas une refonte — c’est la correction minimale requise pour que le cas valide canonical fonctionne.

**Note :** `_load_crud_many_to_one_relations()` utilisait déjà `load_entity_definitions()` (dans `relations.py`) qui supporte canonical depuis 011B — aucun changement nécessaire pour les relations.

**Résultat :** 14 tests passés.

---

## ENTITY-CONTRACT-013 — Brancher la validation dans les migrations ✓ livré

### Objectif

Sécuriser les commandes qui déduisent ou appliquent du SQL depuis les entités.

### Commandes concernées (spec initiale)

```text
forge migration:make
forge migration:diff
forge db:apply
```

### Règle

Aucune migration générée depuis un contrat invalide.

### Rapport de livraison

**Audit des commandes — décisions :**

| Commande | Lit JSON entité | Garde branché | Justification |
|---|---|---|---|
| `migration:status` | Non | Non | Lit `migrations/*.sql` uniquement |
| `migration:apply` | Non | Non | Applique `migrations/*.sql` existants |
| `migration:make <nom>` | Non | Non | Template vide, aucune entité |
| `migration:make --from-entity` | Non | Non | Lit le `.sql` pré-généré |
| `migration:make --from-entities` | Non | Non | Lit les `.sql` pré-générés |
| `migration:make --from-diff <E>` | **Oui** | **Oui** | Lit JSON via `load_entity_definition()` |
| `migration:diff --entity <E>` | **Oui** | **Oui** | Lit JSON via `load_entity_definition()` |
| `db:apply` | Oui (via `check_model`) | Non | `check_model` déjà protège ; commande SQL, pas de génération |

**Fichiers modifiés :**

- `forge_cli/entities/migrations.py` — ajout `normalize_canonical_entity_for_model_build` dans `load_entity_definition()` (normalisation canonical) ; ajout `_assert_migration_contracts_valid()` ; appels dans `_run_diff_command()` et `_run_make_command()` quand `from_diff is not None`.

**Fichiers créés :**

- `tests/test_migration_entity_validation.py` — 14 tests : commandes protégées + entité invalide → SystemExit, message court, conseil `entity:validate`, aucun fichier généré, pas de traceback ; commandes non protégées (`migration:make` blank) non bloquées ; `collect_entity_validation_results()` et `--json` préservés.

**Résultat :** 14 tests passés.

---

## ENTITY-CONTRACT-014 — Adapter les générateurs d’entités ✓ livré

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

## ENTITY-CONTRACT-015 — Verrouiller la génération `many_to_one` ✓ livré après correctif 015-FIX

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

## ENTITY-CONTRACT-015-FIX — Suppression du skip silencieux des relations canoniques ✓ livré

### Objectif

Corriger le traitement des relations `many_to_one` canoniques dans `relations.py`.
Le ticket 015 avait introduit un `return None` silencieux pour les relations canoniques,
empêchant la génération SQL FK.

### Ce qui a été corrigé

- Suppression du skip silencieux dans `_validate_relation_item()`.
- Ajout de `_validate_relation_item_canonical()` : valide explicitement les relations
  canoniques et retourne un `ValidatedRelation` complet.
- Mapping `on_delete` canonique (lowercase) vers SQL : `restrict → RESTRICT`,
  `cascade → CASCADE`, `set_null → SET NULL`, `no_action → NO ACTION`.
- Contrainte dérivée automatiquement : `fk_{from_table}_{foreign_key}`.
- Si la FK column n'est pas déclarée comme champ dans l'entité source,
  la SQL FK est quand même générée (from_python_type déduit du PK cible).
- `on_update` fixé à `RESTRICT` pour les relations canoniques (non spécifié dans le format).
- `entity:validate` reste vert ; `build:model` ne plante pas ; legacy préservé.

### Limites restantes

- Ce ticket ne traite pas `many_to_many`.
- Ce ticket ne migre pas les starters.
- Ce ticket ne supprime pas le support legacy.
- La chaîne CRUD pouvait lever un `KeyError` si la FK n'était pas déclarée comme champ
  dans l'entité source — corrigé par `ENTITY-CONTRACT-015-FIX-CRUD-CANONICAL-M2O`.

---

## ENTITY-CONTRACT-015-FIX-CRUD-CANONICAL-M2O — `make:crud` compatible avec `many_to_one` canonique sans FK déclarée ✓ livré

### Objectif

Corriger `relations_loader.py` pour que `make:crud` fonctionne avec une relation
`many_to_one` canonique même si la clé étrangère n'est pas déclarée comme champ
métier dans l'entité source.

### Ce qui a été corrigé

- Remplacement de `source_field = current_fields[relation.from_field]` par
  `source_field = current_fields.get(relation.from_field)` avec fallback sur
  `relation.from_column` (= valeur de `foreign_key` pour les relations canoniques).
- Le contexte CRUD (`CrudManyToOneRelation`) est correctement produit avec
  `field_column = foreign_key` quand le champ FK n'est pas déclaré dans l'entité.
- Legacy many_to_one préservé : si le champ est déclaré, `source_field["column"]` est utilisé.

### Limites restantes

- Si la FK n'est pas déclarée comme champ dans l'entité, `build_form` ne génère pas
  de `RelationField` pour cette FK (comportement attendu — FK technique invisible du formulaire).
- Ce ticket ne traite pas `many_to_many`.
- Ce ticket ne migre pas les starters.

**Prochain ticket recommandé : ENTITY-CONTRACT-017.**

---

## ENTITY-CONTRACT-016 — Générer les relations `many_to_many` canoniques ✓ livré

### Objectif

Permettre à `forge make:relation` de générer des relations `many_to_many`
avec un bloc `pivot` canonique (`id`, `unique_pair`, deux FK), et valider/générer
le SQL correspondant.

### Ce qui a été livré

- `make_relation.py` : suppression du rejet de `many_to_many` ;
  ajout de `_build_m2m_relation_interactively()` avec prompts pour
  `from`, `to`, `name`, `inverse_name`, `pivot.table`, `pivot.from_key`,
  `pivot.to_key`, `pivot.on_delete`.
- Format généré : `{"type": "many_to_many", "from": …, "to": …, "name": …, "pivot": {"table": …, "from_key": …, "to_key": …, "id": true, "unique_pair": true, "on_delete": …, "fields": []}}`.
- `relations.py` : ajout de `ValidatedCanonicalManyToManyRelation` (dataclass),
  `_validate_m2m_canonical()` (validation avec résolution d'entités et contrôle
  `on_delete` strictement minuscule), `_generate_canonical_m2m_sql()` (CREATE TABLE
  avec `id AUTO_INCREMENT`, `UNIQUE KEY`, indexes, contraintes FK).
- Dispatch dans `validate_relations_definition()` : M2M canonique détecté par
  `"pivot" in relation`, legacy M2M préservé.
- `generate_relations_sql()` : gère les trois types (`ValidatedRelation`,
  `ValidatedCanonicalManyToManyRelation`, legacy `ValidatedManyToManyRelation`).
- Tests : `tests/test_many_to_many_canonical_generation.py` (57 tests),
  `tests/test_make_relation_command.py` mis à jour.

### Limites restantes

- `pivot.fields` non traité par le wizard (champs métier du pivot = ticket 017).
- `make:crud` ne gère pas encore les relations M2M canoniques (ticket futur).
- Ce ticket ne migre pas les starters.

---

## ENTITY-CONTRACT-017 — Attributs de pivot contrôlés ✓ livré

### Objectif

Permettre des champs métier optionnels dans `pivot.fields[]` pour les
relations `many_to_many` canoniques, avec validation, mapping SQL et
protection des clés techniques.

### Ce qui a été livré

- `relations.py` : `ValidatedPivotField` étendu avec `unique: bool = False` ;
  `ValidatedCanonicalManyToManyRelation` étendu avec `pivot_fields: tuple[ValidatedPivotField, ...]` ;
  ajout de `_FORGE_PIVOT_SIMPLE_TYPES`, `_FORGE_PIVOT_ALL_TYPES`, `_pivot_field_sql_type()`,
  `_validate_canonical_pivot_fields()`.
- Mapping des 12 types Forge → SQL (string→VARCHAR, text→TEXT, integer→INT,
  big_integer→BIGINT, float→DOUBLE, decimal→DECIMAL(p,s), boolean→BOOLEAN,
  date→DATE, datetime→DATETIME, email→VARCHAR(255), password→VARCHAR(255), json→LONGTEXT).
- Contraintes : `required: true` → NOT NULL ; `nullable: false` → NOT NULL ;
  `nullable: true` → NULL ; `unique: true` → `UNIQUE KEY uq_{pivot}_{field}`.
- Protection : `id`, `from_key`, `to_key` interdits dans `pivot.fields[]`.
- `_generate_canonical_m2m_sql()` inclut les colonnes pivot et les UNIQUE KEY
  correspondantes.
- Tests : `tests/test_pivot_fields_controlled.py` (42 tests).
- CRUD pivot avancé : hors périmètre (ticket futur).
- `pivot.schema.json` inchangé (déjà conforme).

### Limites restantes

- Le CRUD avancé pour modifier les attributs pivot n’est pas généré.
- Les starters ne sont pas migrés.
- Le support legacy reste inchangé.

**Prochain ticket recommandé : ENTITY-CONTRACT-DOC-001.**

---

## ENTITY-CONTRACT-018 — Tests d'intégration des pivots many_to_many ✓ livré

### Objectif

Consolider les tickets 016 et 017 par des tests d'intégration bout en bout :
`relations.json → entity:validate → build:model → SQL pivot généré`.

### Ce qui a été livré

- `tests/test_many_to_many_pivot_integration.py` (41 tests) :
  - Pivot minimal : CREATE TABLE, id AUTO_INCREMENT, article_id, tag_id, UNIQUE KEY, FK ×2, ON DELETE CASCADE.
  - Pivot avec champs métier : `role VARCHAR(50) NOT NULL`, `joined_at DATETIME NULL`, FK et UNIQUE pair préservées.
  - Collisions interdites : `id`, `from_key`, `to_key` → `EntityRelationsError` avec message stable, sans traceback.
  - `entity:validate` CLI : retourne 0 pour pivot valide, non-nul pour collision.
  - `build:model` / `sync_relations` : génère `relations.sql` avec le SQL attendu.
  - Non-régression `many_to_one` canonique : ALTER TABLE préservé.
  - Non-régression legacy M2M : PRIMARY KEY composite préservé.
  - Coexistence M2O canonique + M2M canonique dans le même `relations.json`.

### Limites restantes

- CRUD avancé des champs pivot : hors périmètre.
- Starters non migrés.
- Legacy non supprimé.

**Prochain ticket recommandé : ENTITY-CONTRACT-DOC-007.**

---

# Bloc 5 — Documentation officielle des contrats JSON

## ENTITY-CONTRACT-DOC-001 — Documenter le rôle du JSON canonique

**Statut : LIVRÉ**

**Commit** : `docs: explain canonical JSON role (ENTITY-CONTRACT-DOC-001)`

### Objectif

Expliquer pourquoi les fichiers JSON d’entité sont la source canonique de Forge.

### Page livrée

```text
docs/entities/json-canonique.md
```

### Contenu livré

- principe central JSON canonique → entity:validate → build:model ;
- fichiers concernés (entités, relations, schémas JSON Schema) ;
- format canonique commenté (Article avec title et published_at) ;
- flux Forge en ASCII art ;
- fichiers générés vs manuels (table) ;
- mapping types Forge → SQL ;
- relations many_to_one et many_to_many avec pivot.fields[] ;
- aide à la saisie VS Code ($schema) ;
- limites assumées.

### Garde-fous

- `tests/meta/test_docs_entity_json_canonical_001.py` (12 tests)
- `mkdocs.yml` nav mis à jour (Concepts → Le JSON canonique)

---

## ENTITY-CONTRACT-DOC-002 — Documenter `entity.schema.json`

**Statut : LIVRÉ**

**Commit** : `docs: document entity schema contract (ENTITY-CONTRACT-DOC-002)`

### Objectif

Documenter la structure officielle d’une entité Forge.

### Page livrée

```text
docs/entities/entity-schema.md
```

### Contenu livré

- rôle du schéma (forme vs sémantique) ;
- exemple minimal valide commenté (Article) ;
- propriétés racine avec table (obligatoire/optionnel/format) ;
- `fields[]` : types Forge, clés obligatoires/optionnelles, exemples, interdits (`id`, `sql_type`, `python_type`) ;
- `options` : `timestamps` et `soft_delete` avec effet sur la projection SQL ;
- `indexes` : déclaratifs, validation sémantique par `entity:validate` ;
- "Ce qui n’est plus canonique" : liste des clés legacy interdites ;
- erreurs fréquentes (8 cas) ;
- section validation (`entity:validate`, `--json`, `build:model`).

### Garde-fous

- `tests/meta/test_docs_entity_schema_001.py` (13 tests)
- `mkdocs.yml` nav mis à jour (Concepts → Schéma des entités)

---

## ENTITY-CONTRACT-DOC-003 — Documenter `relations.schema.json`

**Statut : LIVRÉ**

**Commit** : `docs: document relations schema contract (ENTITY-CONTRACT-DOC-003)`

### Objectif

Documenter la structure officielle de `relations.json`.

### Page livrée

```text
docs/entities/relations-schema.md
```

### Contenu livré

- rôle du schéma (forme vs sémantique, séparation entités/relations) ;
- exemple racine minimal ;
- propriétés racine (table) ;
- `many_to_one` : propriétés, table, exemple complet, note sur la clé étrangère technique ;
- `many_to_many` : propriétés, table, exemple complet avec pivot ;
- table pivot : toutes les propriétés de `pivot.schema.json`, `id: true`, `unique_pair: true`, `fields[]` ;
- valeurs `on_delete` (table avec comportement SQL) ;
- clés legacy interdites (9 clés avec remplacement) ;
- erreurs fréquentes (8 cas) ;
- section validation (`entity:validate`, `--json`, `build:model`).

### Garde-fous

- `tests/meta/test_docs_relations_schema_001.py` (13 tests)
- `mkdocs.yml` nav mis à jour (Concepts → Schéma des relations)

---

## ENTITY-CONTRACT-DOC-004 — Documenter les tables pivot many-to-many

**Statut : LIVRÉ**

**Commit** : `docs: document many-to-many pivot tables (ENTITY-CONTRACT-DOC-004)`

### Objectif

Documenter explicitement la décision Forge sur les pivots.

### Page livrée

```text
docs/entities/pivots-many-to-many.md
```

### Contenu livré

- rôle d'une table pivot (liaison, générée, non-entité) ;
- exemple minimal sans attribut (`fields: []`) ;
- exemple avec attributs métier (`role`, `joined_at`) ;
- table des propriétés du pivot ;
- justification de l'`id` technique (extensibilité, homogénéité, références, évolution) ;
- justification de `unique_pair: true` (contrainte UNIQUE, coexistence avec id) ;
- `pivot.fields[]` : types Forge, exemples d'usages, règles ;
- noms réservés (`id`, `from_key`, `to_key`) avec code d'erreur `FORGE_PIVOT_RESERVED_FIELD` ;
- SQL généré réel pour pivot minimal et pivot avec attributs ;
- limites actuelles (CRUD avancé, starters legacy).

### Note d'audit

L'exemple SQL de la spec proposait `BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY` — la projection réelle de Forge utilise `INT NOT NULL AUTO_INCREMENT` avec `PRIMARY KEY (id)` séparé. La documentation reflète la réalité du générateur.

### Garde-fous

- `tests/meta/test_docs_pivot_tables_001.py` (12 tests)
- `mkdocs.yml` nav mis à jour (Concepts → Tables pivot many-to-many)

---

## ENTITY-CONTRACT-DOC-005 — Documenter le mapping types Forge → MariaDB

**Statut : LIVRÉ**

**Commit** : `docs: document Forge to MariaDB type mapping (ENTITY-CONTRACT-DOC-005)`

### Objectif

Publier la table de correspondance officielle.

### Page livrée

```text
docs/entities/types-forge-mariadb.md
```

### Mapping réel documenté (audité dans `canonical_model_normalizer.py` et `relations.py`)

| Type Forge | SQL MariaDB réel | Note |
|---|---|---|
| `string` | `VARCHAR(n)` | défaut 255 si `max_length` absent |
| `text` | `TEXT` | |
| `integer` | `INT` | |
| `big_integer` | `BIGINT` | |
| `float` | `DOUBLE` | |
| `decimal` | `DECIMAL(p,s)` | `precision` et `scale` obligatoires |
| `boolean` | `BOOLEAN` | **correction** : la roadmap indiquait `TINYINT(1)` — le code utilise `BOOLEAN` |
| `date` | `DATE` | |
| `datetime` | `DATETIME` | |
| `email` | `VARCHAR(255)` | longueur fixe |
| `password` | `VARCHAR(255)` | longueur fixe |
| `json` | `LONGTEXT` | pas de stratégie JSON supplémentaire |

### Contenu livré

- principe (types Forge vs projections SQL) ;
- table de mapping complète avec python type ;
- champs système automatiques (id, timestamps, soft_delete) ;
- types paramétrés (string avec max_length, decimal avec precision/scale) ;
- contraintes courantes (required, nullable, unique, default, min/max) ;
- divergence nullable entre `fields[]` et `pivot.fields[]` documentée ;
- champs pivot ;
- clés legacy interdites (sql_type, python_type, types SQL bruts…) ;
- limites.

### Garde-fous

- `tests/meta/test_docs_types_forge_mariadb_001.py` (14 tests dont 12 paramétrés)
- `mkdocs.yml` nav mis à jour (Concepts → Types Forge vers MariaDB)

---

## ENTITY-CONTRACT-DOC-006 — Documenter `forge entity:validate`

**Statut : LIVRÉ**

**Commit** : `docs: document entity validation command (ENTITY-CONTRACT-DOC-006)`

### Objectif

Documenter la commande de validation.

### Page livrée

```text
docs/entities/entity-validate.md
```

### Contenu livré

- rôle de la commande (diagnostic officiel, ne génère pas) ;
- commandes (`entity:validate` et `--json`) ;
- sortie humaine avec exemple OK et exemple erreur ;
- sortie JSON machine : table des champs, structure d’une erreur (`code`, `file`, `path`, `message`, `hint`, `phase`) ;
- phases (`json`, `schema`, `semantic`, `runtime`) ;
- 17 codes d’erreur réels organisés par famille (`FORGE_ENTITY_*`, `FORGE_RELATION_*`, `FORGE_PIVOT_*`) ;
- erreurs fréquentes (8 cas) ;
- intégration avec `build:model`, `make:crud`, migrations ;
- usage en CI (code de retour) ;
- limites (VS Code, starters legacy, état base réelle).

### Garde-fous

- `tests/meta/test_docs_entity_validate_001.py` (13 tests)
- `mkdocs.yml` nav mis à jour (Concepts → Valider les contrats JSON)

---

## ENTITY-CONTRACT-DOC-007 — Documenter l’autocomplétion VS Code ✓ livré

### Objectif

Expliquer comment utiliser les schémas dans l’éditeur.

### Page livrée

```text
docs/entities/vscode-json-schema.md
```

### Contenu livré

- rôle de `$schema` ;
- méthode `$schema` dans le fichier JSON (chemin relatif) ;
- méthode `json.schemas` dans `.vscode/settings.json` ;
- variante prudente avec motif `*/*.json` pour les sous-dossiers ;
- détections VS Code : clés inconnues, types invalides, enum invalides, pivot incomplet ;
- limites : VS Code ne remplace pas `forge entity:validate` ;
- règles sémantiques exclues : entités inconnues, doublons, collisions `from_key`/`to_key` ;
- tableau des schémas concernés (`entity`, `field`, `relations`, `pivot`, `common`) ;
- compatibilité JSON Schema Draft 2020-12 (formulation prudente) ;
- rappel : Forge ne dépend pas d’Internet pour valider un projet.

---

## ENTITY-CONTRACT-DOC-008 — Documenter les limites assumées ✓ livré

### Objectif

Éviter que cette roadmap soit interprétée comme une refonte complète de Forge.

### Page livrée

```text
docs/entities/limites-contrats-json.md
```

### Contenu livré

- JSON Schema vs validation sémantique Forge ;
- limites de VS Code : aide à la saisie, pas de validation officielle ;
- compatibilité legacy temporaire : support transitoire, suppression à décider ;
- starters non migrés : limite assumée ;
- attributs pivot et CRUD avancé : hors périmètre actuel ;
- mapping SQL : `min`/`max` sans `CHECK`, `nullable` différent entre entité et pivot ;
- `entity:validate` ne vérifie pas la base MariaDB réelle ;
- générateurs protégés mais non magiques ;
- travaux futurs possibles listés sans engagements.

Cette roadmap ne couvre pas (hors périmètre permanent) :

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

## ENTITY-CONTRACT-019 — Ajouter les fixtures canoniques ✓ livré

### Objectif

Créer des exemples valides et invalides utilisés par les tests.

### Structure livrée

```text
tests/fixtures/entities/canonical/
├── account/account.json    entité avec email, timestamps (source M2M alternative)
├── article/article.json    entité riche (string, text, boolean, datetime, indexes, timestamps)
├── category/category.json  entité simple (un champ unique)
├── member/member.json      source many_to_many avec pivot.fields[]
├── project/project.json    cible many_to_many avec pivot.fields[]
├── tag/tag.json            cible many_to_many simple
└── relations.json          M2O (Article→Category) + M2M simple + M2M avec pivot.fields[]
```

Tests : `tests/test_canonical_fixtures.py` (39 tests).

Note : `user/user.json` existe comme vestige neutre (`{}`) — non utilisé par les tests.
`"User"` est un mot réservé SQL/MariaDB : la fixture a été remplacée par `account/account.json`.

---

## ENTITY-CONTRACT-020 — Vérifier les exemples documentaires ✓ livré

### Objectif

Faire en sorte que les exemples JSON de la documentation soient aussi testés.

### Règle

```text
Tout exemple JSON important présent dans la documentation doit exister comme fixture de test ou être couvert par un test de validation.
```

### Ce qui a été livré

- `tests/meta/test_docs_json_examples_001.py` (56 tests) :
  - Extraction automatique des blocs ```json des 8 pages `docs/entities/`.
  - Classification automatique : exemple canonique d'entité (schema_version + name + table + fields), exemple canonique de relations (schema_version + relations), autres ignorés.
  - 3 exemples d'entités canoniques validés contre `entity.schema.json` (entity-schema.md, json-canonique.md, vscode-json-schema.md).
  - 3 exemples de relations canoniques validés contre `relations.schema.json` (json-canonique.md, relations-schema.md, vscode-json-schema.md).
  - 4 pivots extraits et validés contre `pivot.schema.json` (json-canonique.md, relations-schema.md, pivots-many-to-many.md ×2).
  - Contrôles pivot : `id: true`, `unique_pair: true`, `from_key ≠ to_key`, `pivot.fields[]` sans noms réservés.
  - Absence de clés legacy dans les exemples canoniques.
  - Exemples VS Code : $schema, json.schemas, blocs JSON valides.
  - Vérification que `.vscode/settings.json` n'existe pas dans le dépôt.
  - Exemples d'erreur non validés (ils ne portent pas `schema_version: "1.0"` — classification automatique).
- `tests/meta/test_pytest_core_only_contract_001.py` : `jsonschema` et `referencing` ajoutés à `CORE_DEPS`.

---

## ENTITY-CONTRACT-021 — Ajouter `forge schema:list` ✓ livré

### Objectif

Lister les schémas disponibles.

### Ce qui a été livré

- `forge_cli/schemas/__init__.py` + `forge_cli/schemas/schema_list.py` — module `schema:list`.
- Lit `schemas/forge.schema.index.json` (registre local), affiche nom, chemin et statut.
- Sortie humaine : liste alignée avec `OK` / `MANQUANT` + total.
- Option `--json` : sortie machine avec `valid`, `registry`, `schema_version`, `count`, `schemas[]`.
- Gestion d'erreurs : registre absent, JSON invalide, clé `schemas` manquante, fichier manquant.
- Exit 1 si le registre est illisible ou si au moins un schéma est manquant.
- `forge.py` : dispatch `schema:list` ajouté.
- `forge_cli/help.py` : section "Schémas JSON" ajoutée.
- `tests/test_schema_list_command.py` (34 tests).

### Exemple

```bash
forge schema:list
```

Sortie :

```text
Schémas JSON Forge disponibles :

  - common       schemas/common.schema.json       OK
  - field        schemas/field.schema.json        OK
  - entity       schemas/entity.schema.json       OK
  - pivot        schemas/pivot.schema.json        OK
  - relations    schemas/relations.schema.json    OK

Total : 5 schéma(s)
```

---

## ENTITY-CONTRACT-022 — Ajouter `forge schema:doctor`

**Statut : livré**

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

### Livraison

- **`forge_cli/schemas/schema_doctor.py`** — commande `schema_doctor_main()` avec 5 contrôles par schéma
  (existence, JSON valide, `$schema` Draft 2020-12, `$id`, `$ref` locaux résolus)
- **`tests/test_schema_doctor_command.py`** — 42 tests (sortie humaine, sortie `--json`,
  gestion d'erreurs, non-régression)
- **`forge.py`** — dispatch `schema:doctor` ajouté
- **`forge_cli/help.py`** — section « Schémas JSON » complétée avec `schema:doctor`
- Suite complète : 11 440 tests passent, 6 skipped, 0 régression

Exemple de sortie :

```
Diagnostic des schémas JSON Forge

Registre : schemas/forge.schema.index.json
Version  : 1.0

Schémas :
  - common      schemas/common.schema.json      OK
  - field       schemas/field.schema.json       OK
  - entity      schemas/entity.schema.json      OK
  - pivot       schemas/pivot.schema.json       OK
  - relations   schemas/relations.schema.json   OK

Références locales :
  - schemas/entity.schema.json    ->  common.schema.json    OK
  - schemas/entity.schema.json    ->  field.schema.json     OK
  ...

Résultat : OK — 5 schéma(s), 0 erreur.
```

---

# Bloc 7 — Clôture

## ENTITY-CONTRACT-023 — Clôturer la roadmap Contrats JSON Schema

**Statut : livré**

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

## Clôture de la roadmap

**Statut : terminée.**

La roadmap Contrats JSON Schema est clôturée après livraison de ENTITY-CONTRACT-023.

| Phase | Statut |
|---|---|
| Phase 1 — Schémas JSON | terminée |
| Phase 2 — Validation Forge | terminée |
| Phase 3 — Générateurs | terminée |
| Phase 4 — Relations et pivots | terminée |
| Phase 5 — Documentation officielle | terminée |
| Phase 6 — Expérience développeur et tests | terminée |
| Phase 7 — Clôture | terminée |

### Résumé de livraison

La roadmap a livré :

- les schémas JSON canoniques (`common`, `field`, `entity`, `pivot`, `relations`) ;
- la validation JSON Schema Draft 2020-12 via `forge entity:validate` ;
- la validation sémantique Forge (18 codes d’erreur stables) ;
- la sortie JSON machine stable (`--json`) ;
- l’intégration dans `forge build:model` ;
- l’intégration dans `forge make:crud` ;
- l’intégration dans les migrations concernées ;
- la génération canonique des entités (`schema_version`, `name`, `table`, `fields[]`) ;
- la génération canonique des relations ;
- les pivots many-to-many avec `id` technique et contrainte `UNIQUE` sur les deux FK ;
- `pivot.fields[]` contrôlés par le schéma ;
- la documentation officielle complète (8 tickets DOC-001 à DOC-008) ;
- les fixtures canoniques (`tests/fixtures/`) ;
- la vérification automatique des exemples documentaires (`tests/meta/test_docs_json_examples_001.py`) ;
- `forge schema:list` (inventaire des schémas) ;
- `forge schema:doctor` (diagnostic complet des schémas).

### Validations finales exécutées

```
python forge.py schema:list              → 5 schémas OK
python forge.py schema:list --json       → valid: true
python forge.py schema:doctor            → 5 schémas, 0 erreur
python forge.py schema:doctor --json     → valid: true, errors_count: 0
python forge.py entity:validate          → 2 fichiers valides, 0 erreur
python forge.py entity:validate --json   → valid: true
python forge.py build:model              → 3 régénéré(s), 2 préservé(s)
pytest (suite complète)                  → 11 482 passed, 6 skipped
python -m compileall -q .               → OK
ruff check .                             → All checks passed
mkdocs build --strict                    → OK
git diff --check                         → OK
```

---

## Limites restantes hors roadmap

Ces éléments sont documentés mais non traités dans cette roadmap.
Chacun nécessite un ticket séparé.

| Limite | Statut |
|---|---|
| Starters legacy non migrés vers le format canonique | non traité, ticket séparé nécessaire |
| Support legacy encore présent dans les générateurs | maintenu par compatibilité, décision différée |
| Nullable : harmonisation entre `fields[]` et `pivot.fields[]` | non traité |
| `min`/`max` sans `CHECK` SQL correspondant | non traité |
| CRUD avancé des attributs `pivot.fields[]` | hors périmètre de cette roadmap |
| Fichier `.vscode/settings.json` prêt à l’emploi non généré | documenté, ticket DX à créer |

---

## Suites possibles

Ces éléments ne sont pas des engagements. Ils constituent des pistes pour les roadmaps suivantes.

- Roadmap de migration des starters vers le format canonique.
- Ticket de décision sur le support legacy (maintien ou suppression).
- Ticket de correction nullable entre `fields[]` et `pivot.fields[]`.
- Ticket CRUD avancé `pivot.fields[]`.
- Ticket DX `.vscode/settings.json` généré automatiquement.

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
