# Audit — Plan de suppression accélérée du legacy Forge

**Ticket** : LEGACY-REMOVE-PLAN-001-ACCELERATED-LEGACY-REMOVAL-PLAN
**Date** : 2026-05-19
**Auteur** : Forge (audit de suppression)
**Périmètre** : `forge_cli/entities/`, `forge_cli/starters/`, `tests/`, `docs/`

---

## 1. Résumé

Cet audit établit le plan de suppression accélérée du support legacy (`format_version: 1`)
dans Forge. Aucune application réelle Forge n'est à préserver. Les starters sont 100 %
canoniques. Le CRUD M2M canonique vient d'être corrigé (CRUD-M2M-CANONICAL-001).

La stratégie de compatibilité longue devient obsolète. Elle est remplacée par une
bascule directe : le format canonique `schema_version: "1.0"` devient le seul format
accepté.

Le présent ticket est un plan. Aucune suppression n'est effectuée ici.

---

## 2. Contexte stratégique

| Fait | Valeur |
|---|---|
| Applications Forge en production à préserver | 0 |
| Starters migrés en canonique | 100 % |
| Runtime canonique consolidé | Oui |
| CRUD M2M canonique corrigé | Oui (CRUD-M2M-CANONICAL-001) |
| Tests encore en format legacy | ~57 fichiers runtime, ~268 occurrences |
| Politique actuelle | Dépréciation (ADR-012) |
| Nouvelle politique cible | Suppression accélérée |

---

## 3. Méthode d'audit

```bash
grep -RInE 'format_version|sql_type|python_type|primary_key|auto_increment|\
from_entity|to_entity|foreign_key_name|pivot_table|source_key|target_key|legacy' \
  forge_cli/ tests/ docs/ 2>/dev/null

python forge.py schema:list
python forge.py schema:doctor
python forge.py entity:validate
python forge.py build:model

pytest tests/test_build_model_legacy_warning.py \
       tests/test_make_crud_legacy_warning.py \
       tests/test_make_crud_many_to_many_canonical.py \
       tests/meta/test_legacy_policy_002.py \
       tests/meta/test_legacy_migration_guide_001.py -q
```

Résultat des commandes runtime : toutes passent (11 894 tests, 0 erreur).

---

## 4. Chemins legacy restants dans le core

### 4.1 `forge_cli/entities/validation.py`

**Zone legacy** : entrée principale du format `format_version: 1`.

| Ligne | Objet | Legacy concerné | Action future |
|---|---|---|---|
| 55 | `ALLOWED_ROOT_KEYS` inclut `format_version`, `entity` | Clés racine du format legacy | LEGACY-REMOVE-001 : retirer ces clés ; lever une erreur claire si détectées |
| 228–229 | Validation de `format_version` comme entier | Permissivité legacy | LEGACY-REMOVE-001 : supprimer |
| 410 | `format_version` dans le dict normalisé retourné | Propagation legacy interne | LEGACY-REMOVE-001 : supprimer |
| 509–510 | Vérification `format_version == 1` | Double entrée | LEGACY-REMOVE-001 : supprimer |

### 4.2 `forge_cli/entities/model.py`

**Zone legacy** : détection, normalisation et warning legacy dans `build:model`.

| Ligne | Objet | Legacy concerné | Action future |
|---|---|---|---|
| 38 | `EntitySource.is_legacy: bool` | Flag legacy | LEGACY-REMOVE-001 : supprimer |
| 47 | `BuildModelResult.legacy_warnings` | Liste de warnings | LEGACY-REMOVE-001 : supprimer |
| 115–120 | Génération des warnings legacy | Message dépréciation | LEGACY-REMOVE-001 : supprimer |
| 346–356 | Branche `is_legacy` : normalisation canonique→interne | Chemin de compatibilité | LEGACY-REMOVE-001 : remplacer par erreur si `format_version` détecté |

### 4.3 `forge_cli/entities/relations.py`

**Zone legacy** : format legacy des relations (`format_version: 1`, `source`/`target`, `ValidatedManyToManyRelation`).

| Ligne | Objet | Legacy concerné | Action future |
|---|---|---|---|
| 95 | Dataclass `ValidatedManyToManyRelation` | Type M2M legacy | LEGACY-REMOVE-002 : supprimer |
| 523 | `_generate_many_to_many_sql()` | Génération SQL M2M legacy | LEGACY-REMOVE-002 : supprimer |
| 570–578 | Validation `format_version` dans la racine relations | Compatibilité relations legacy | LEGACY-REMOVE-002 : supprimer |
| 854 | `_validate_many_to_many()` | Validateur M2M legacy | LEGACY-REMOVE-002 : supprimer |
| 174, 179 | Type hints incluant `ValidatedManyToManyRelation` | Propagation du type legacy | LEGACY-REMOVE-002 : simplifier |

### 4.4 `forge_cli/entities/make_crud.py`

**Zone legacy** : détection + warning dans `make:crud`.

| Ligne | Objet | Legacy concerné | Action future |
|---|---|---|---|
| 170–191 | Détection `is_legacy`, emission warning | Warning non bloquant | LEGACY-REMOVE-001 : remplacer par erreur bloquante |

### 4.5 `forge_cli/entities/make_relation.py`

**Zone legacy** : acceptation de `format_version` dans la racine relations.

| Ligne | Objet | Legacy concerné | Action future |
|---|---|---|---|
| 135–136 | Accepte `format_version` ou `schema_version` | Double entrée | LEGACY-REMOVE-002 : n'accepter que `schema_version: "1.0"` |

### 4.6 `forge_cli/entities/crud/relations_loader.py`

**Zone legacy** : branche `ValidatedManyToManyRelation` maintenue après CRUD-M2M-CANONICAL-001.

| Ligne | Objet | Legacy concerné | Action future |
|---|---|---|---|
| Import | `ValidatedManyToManyRelation` importé | Type M2M legacy | LEGACY-REMOVE-002 : supprimer branche legacy |
| ~113 | Branche `isinstance(relation, ValidatedManyToManyRelation)` | Normalisation legacy→canonique | LEGACY-REMOVE-002 : supprimer, ne garder que le canonique |

### 4.7 `forge_cli/entities/migrations.py`

**Zone legacy** : lecture d'entités — vérification `schema_version == "1.0"`.

| Ligne | Objet | Legacy concerné | Action future |
|---|---|---|---|
| 351 | Branche `if schema_version == "1.0"` (implicitement, les autres sont legacy) | Chemin dual | LEGACY-REMOVE-001 : supprimer la branche non-canonique |

### 4.8 `forge_cli/entities/canonical_model_normalizer.py` — NOTE

Ce fichier traduit les entités canoniques en représentation **interne** (avec `sql_type`,
`python_type`, `primary_key`, `auto_increment`). Ce ne sont pas des clés du format
utilisateur — elles constituent la représentation interne de Forge utilisée par
`validation.py`, `model.py` et les générateurs.

Ce fichier doit être **conservé** après suppression du support legacy utilisateur : il
reste le traducteur canonique→interne. Sa suppression (ou le remplacement de la
représentation interne) est hors scope de la série LEGACY-REMOVE.

---

## 5. Tests legacy restants

### Rappel : catégories du nouveau plan

Le plan accéléré supprime la catégorie « compatibilité à conserver » de l'audit précédent.
Trois catégories seulement :

- **A** — supprimer (test de compatibilité legacy devenu inutile)
- **B** — convertir vers le canonique (teste une vraie fonctionnalité)
- **C** — remplacer par un test de refus clair (doit vérifier que le legacy est rejeté)

### Groupe A — Supprimer (4 fichiers)

| Fichier | Tests | Motif |
|---|---:|---|
| `tests/test_make_crud_many_to_many.py` | 11 | Couvert par `test_make_crud_many_to_many_canonical.py` |
| `tests/meta/test_legacy_warnings_audit_001.py` | ~8 | Audite des warnings qui n'existeront plus |
| `tests/meta/test_legacy_warnings_close_001.py` | ~6 | Clôture de warnings obsolètes |
| `tests/meta/test_legacy_warnings_makecrud_makerelation_audit_001.py` | ~7 | Audite des warnings à supprimer |

### Groupe B — Convertir vers le canonique (51 fichiers)

**Famille CRUD (make:crud, vues, formulaires)** — 17 fichiers :

| Fichier | Ticket |
|---|---|
| `test_make_crud.py` | LEGACY-REMOVE-003 |
| `test_make_crud_empty_states.py` | LEGACY-REMOVE-003 |
| `test_make_crud_htmx_delete.py` | LEGACY-REMOVE-003 |
| `test_make_crud_htmx_pagination.py` | LEGACY-REMOVE-003 |
| `test_make_crud_htmx_search.py` | LEGACY-REMOVE-003 |
| `test_make_crud_many_to_one_canonical.py` | LEGACY-REMOVE-003 |
| `test_make_crud_pagination.py` | LEGACY-REMOVE-003 |
| `test_make_crud_partials.py` | LEGACY-REMOVE-003 |
| `test_make_crud_rbac.py` | LEGACY-REMOVE-003 |
| `test_make_crud_search.py` | LEGACY-REMOVE-003 |
| `test_make_crud_sort.py` | LEGACY-REMOVE-003 |
| `test_crud_bulk_delete.py` | LEGACY-REMOVE-003 |
| `test_crud_filters.py` | LEGACY-REMOVE-003 |
| `test_crud_filters_htmx.py` | LEGACY-REMOVE-003 |
| `test_crud_filter_whitelist_001.py` | LEGACY-REMOVE-003 |
| `test_crud_htmx.py` | LEGACY-REMOVE-003 |
| `test_crud_sort.py` | LEGACY-REMOVE-003 |

**Famille Média** — 12 fichiers :

| Fichier | Ticket |
|---|---|
| `test_make_crud_media.py` | LEGACY-REMOVE-003 |
| `test_make_crud_media_alt.py` | LEGACY-REMOVE-003 |
| `test_make_crud_media_context.py` | LEGACY-REMOVE-003 |
| `test_make_crud_media_destroy.py` | LEGACY-REMOVE-003 |
| `test_make_crud_media_gallery_add.py` | LEGACY-REMOVE-003 |
| `test_make_crud_media_gallery_context.py` | LEGACY-REMOVE-003 |
| `test_make_crud_media_gallery_delete.py` | LEGACY-REMOVE-003 |
| `test_make_crud_media_gallery_multiupload.py` | LEGACY-REMOVE-003 |
| `test_make_crud_media_gallery_order.py` | LEGACY-REMOVE-003 |
| `test_make_crud_media_runtime.py` | LEGACY-REMOVE-003 |
| `test_entity_media_declaration.py` | LEGACY-REMOVE-003 |
| `test_entity_form_field.py` | LEGACY-REMOVE-003 |

**Famille Public** — 4 fichiers :

| Fichier | Ticket |
|---|---|
| `test_make_public_form.py` | LEGACY-REMOVE-003 |
| `test_make_public_i18n.py` | LEGACY-REMOVE-003 |
| `test_make_public_list.py` | LEGACY-REMOVE-003 |
| `test_make_public_list_media.py` | LEGACY-REMOVE-003 |

**Famille Relations** — 4 fichiers :

| Fichier | Ticket |
|---|---|
| `test_relations_ordered.py` | LEGACY-REMOVE-002 |
| `test_relations_many_to_many.py` | LEGACY-REMOVE-002 |
| `test_relations_many_to_one_canonical_sql.py` | LEGACY-REMOVE-002 |
| `test_entity_list_filter.py` | LEGACY-REMOVE-003 |

**Famille Entités / Validation** — 7 fichiers (ancienne catégorie A, désormais à convertir) :

| Fichier | Ticket |
|---|---|
| `test_entity_json_validation.py` | LEGACY-REMOVE-001 |
| `test_entity_semantic_validation.py` | LEGACY-REMOVE-001 |
| `test_entity_relations.py` | LEGACY-REMOVE-002 |
| `test_entity_model_cli.py` | LEGACY-REMOVE-001 |
| `test_entity_sync_command.py` | LEGACY-REMOVE-001 |
| `test_build_model_canonical_routing.py` | LEGACY-REMOVE-001 |
| `test_starter_scaffold_empty_relations.py` | LEGACY-REMOVE-001 |

**Famille Outils / Diagnostic** — 4 fichiers :

| Fichier | Ticket |
|---|---|
| `test_entity_db_apply.py` | LEGACY-REMOVE-001 |
| `test_doctor.py` | LEGACY-REMOVE-001 |
| `test_migrations.py` | LEGACY-REMOVE-001 |
| `test_entity_relations.py` | LEGACY-REMOVE-002 |

### Groupe C — Remplacer par un test de refus clair (3 fichiers)

| Fichier actuel | Fichier futur | Comportement attendu |
|---|---|---|
| `test_build_model_legacy_warning.py` | `test_build_model_legacy_rejection.py` | `build:model` lève une erreur claire sur `format_version: 1` |
| `test_make_crud_legacy_warning.py` | `test_make_crud_legacy_rejection.py` | `make:crud` lève une erreur claire sur `format_version: 1` |
| `tests/meta/test_legacy_migration_guide_001.py` | `test_legacy_format_removal_001.py` | La doc indique que le format legacy n'est plus accepté |

---

## 6. Documentation à corriger

| Document | Action future |
|---|---|
| `docs/adr/012-legacy-format-deprecation-policy.md` | Réécrire en ADR de suppression : « le format legacy n'est plus accepté depuis X.X » |
| `docs/entities/migration-legacy-vers-canonique.md` | Remplacer par : « le format canonique est obligatoire — voici comment écrire un fichier canonique valide » |
| `docs/entities/limites-contrats-json.md` | Supprimer les sections sur la compatibilité legacy temporaire |
| `docs/15-minutes.md` | Retirer les exemples `format_version: 1` ou les remplacer par des exemples canoniques |
| `docs/guide.md` | Vérifier et remplacer les exemples legacy |
| `docs/concepts.md` | Si des références à `format_version` y existent |
| `docs/history/audits/legacy-support-core-audit-001.md` | Archiver — supersédé par ce plan |
| `docs/history/audits/legacy-tests-reclassification-audit-001.md` | Archiver — classification supersédée |
| `mkdocs.yml` nav | `Migration legacy vers canonique` → renommer ou retirer selon la rédaction finale |

---

## 7. Risques de suppression

### Risque 1 — Volume des tests à convertir

57 fichiers de tests utilisent des fixtures legacy. La conversion est mécaniquement
répétitive mais large. Elle doit se faire fichier par fichier dans LEGACY-REMOVE-003.

**Mitigation** : fixer une convention canonique partagée (`_canonical_entity()` helper)
et l'appliquer systématiquement.

### Risque 2 — Représentation interne

`canonical_model_normalizer.py` génère des dicts internes avec `sql_type`, `python_type`,
`primary_key`, `auto_increment`. Ces clés **ne sont pas** le format legacy utilisateur.
Supprimer le support legacy utilisateur ne touche pas cette représentation interne.

**Mitigation** : ne pas toucher à `canonical_model_normalizer.py` dans les tickets LEGACY-REMOVE.

### Risque 3 — `ValidatedManyToManyRelation` dans `relations_loader.py`

Après CRUD-M2M-CANONICAL-001, `relations_loader.py` contient une branche pour chaque
type. La suppression de `ValidatedManyToManyRelation` et de sa branche dans LEGACY-REMOVE-002
est propre et isolée.

**Mitigation** : supprimer en même temps le type, le validateur, le générateur SQL et la
branche dans `relations_loader.py`.

### Risque 4 — Tests `test_entity_json_validation.py` et `test_entity_semantic_validation.py`

Ces fichiers testent que les entités legacy sont acceptées. Après suppression, la moitié
des tests devient des tests de rejet, l'autre moitié devient des tests canoniques.
Le refactoring est plus complexe que la plupart des fichiers du groupe B.

**Mitigation** : traiter ces fichiers en tête du plan LEGACY-REMOVE-001 avec des tickets
dédiés.

---

## 8. Plan court recommandé

| Ticket | Objectif | Scope principal |
|---|---|---|
| LEGACY-REMOVE-001 | Supprimer le support legacy des entités | `validation.py`, `model.py`, `make_crud.py`, `migrations.py`, tests validation |
| LEGACY-REMOVE-002 | Supprimer le support legacy des relations | `relations.py`, `make_relation.py`, `relations_loader.py`, tests relations |
| LEGACY-REMOVE-003 | Nettoyer les tests legacy et les warnings | 44 fichiers B + 3 fichiers C ; supprimer les 4 fichiers A |
| LEGACY-REMOVE-004 | Mettre à jour docs et ADR | ADR-012, migration guide, limites, mkdocs.yml |
| LEGACY-CLOSE-001 | Clôturer la suppression : audit final + garantie zéro legacy | grep final, meta test de clôture |

Chaque ticket = un commit. Pas de tunnel long.

---

## 9. Tickets proposés

### LEGACY-REMOVE-001 — Entités

Supprimer dans `validation.py` et `model.py` :
- `format_version` de `ALLOWED_ROOT_KEYS`
- Branche `is_legacy` dans `model.py`
- Warning legacy → erreur bloquante dans `make:crud`
- Branche non-canonique dans `migrations.py`

Convertir ou remplacer :
- `test_entity_json_validation.py`, `test_entity_semantic_validation.py`,
  `test_entity_model_cli.py`, `test_entity_sync_command.py`,
  `test_build_model_canonical_routing.py`, `test_entity_db_apply.py`,
  `test_doctor.py`, `test_starter_scaffold_empty_relations.py`

Créer :
- `test_build_model_legacy_rejection.py`
- `test_make_crud_legacy_rejection.py`

### LEGACY-REMOVE-002 — Relations

Supprimer dans `relations.py` :
- Dataclass `ValidatedManyToManyRelation`
- `_validate_many_to_many()` (validateur M2M legacy)
- `_generate_many_to_many_sql()` (générateur SQL M2M legacy)
- Validation `format_version` racine relations (lignes 570–578)

Simplifier `make_relation.py` (n'accepter que `schema_version: "1.0"`).

Simplifier `relations_loader.py` (supprimer branche `ValidatedManyToManyRelation`).

Convertir : `test_relations_many_to_many.py`, `test_relations_ordered.py`,
`test_entity_relations.py`, `test_relations_many_to_one_canonical_sql.py`.

### LEGACY-REMOVE-003 — Tests

Convertir les 44 fichiers du groupe B (CRUD, Média, Public, Diagnostic).
Supprimer les 4 fichiers du groupe A.
Créer le test meta de clôture.

### LEGACY-REMOVE-004 — Docs

Réécrire ADR-012 (suppression confirmée).
Réécrire `docs/entities/migration-legacy-vers-canonique.md`.
Nettoyer `docs/entities/limites-contrats-json.md`.
Purger les exemples legacy dans les tutoriels.

### LEGACY-CLOSE-001 — Clôture

Grep de vérification zéro `format_version` dans `forge_cli/` (hors tests de rejet).
Meta test de clôture (vérifie l'absence de format_version dans le core).
Mise à jour `CHANGELOG.md`.

---

## 10. Conclusion

Le plan de suppression accélérée est viable. Aucun projet réel n'est à préserver.
Les conditions sont réunies :

- Starters 100 % canoniques
- CRUD M2M canonique corrigé
- Fixtures de référence canoniques en place
- Pipeline de validation canonique consolidé

La suppression se déroule en 5 tickets courts et séquentiels. Le risque principal
est le volume de conversion des tests (57 fichiers), mitigé par des helpers partagés
et un plan ticket par ticket.

**Aucune suppression n'a été effectuée dans ce ticket. Ce document est le plan.**

---

## Mise en œuvre partielle — LEGACY-REMOVE-001A

LEGACY-REMOVE-001A refuse les entités `format_version: 1` dans `build:model`.

`forge_cli/entities/model.py` lève désormais une `ModelValidationError` si une entité JSON contient `format_version: 1`. Aucun SQL n'est généré pour cette entité. Le champ `is_legacy` sur `EntitySource` et la liste `legacy_warnings` sur `BuildModelResult` ont été supprimés.

`make:crud`, les relations legacy et les tests CRUD restent hors périmètre.

---

## Mise en œuvre partielle — LEGACY-REMOVE-001B

LEGACY-REMOVE-001B refuse les entités `format_version: 1` dans `make:crud`.

`forge_cli/entities/make_crud.py` lève désormais `SystemExit(1)` avec un message explicite si une entité JSON contient `format_version: 1`. Aucun fichier CRUD n'est généré. Le warning legacy de `LEGACY-WARNINGS-004` a été retiré.

`build:model` a déjà été traité par LEGACY-REMOVE-001A.
Les relations legacy restent hors périmètre et seront traitées dans LEGACY-REMOVE-002.

---

## Mise en œuvre — LEGACY-REMOVE-002

LEGACY-REMOVE-002 supprime le support du format `format_version: 1` dans les relations.

### Fichiers modifiés (core)

- **`forge_cli/entities/relations.py`** — suppression de `ValidatedManyToManyRelation`, des validateurs M2M legacy, de la génération SQL M2M legacy, et rejet explicite de `format_version` à la racine du document relations.
- **`forge_cli/entities/crud/relations_loader.py`** — suppression de la branche `isinstance(relation, ValidatedManyToManyRelation)`.
- **`forge_cli/entities/model.py`** — remplacement des type hints incluant `ValidatedManyToManyRelation`.
- **`forge_cli/entities/make_relation.py`** — `_load_existing_relations_doc()` lève une erreur si `format_version` est détecté ; `_ensure_no_obvious_duplicates()` n'accepte plus les clés legacy.

### Fichiers de tests convertis

- `tests/test_entity_relations.py` — réécriture complète : format canonique, tests de rejet du format legacy.
- `tests/test_relations_many_to_many.py` — réécriture : tests de rejet du format legacy + tests du format canonique M2M.
- `tests/test_relations_ordered.py` — réécriture : tous les tests deviennent des tests de rejet (feature `order_column` était exclusivement legacy).
- `tests/test_relations_many_to_one_canonical_sql.py` — `test_legacy_many_to_one_still_supported` → `test_legacy_many_to_one_is_rejected`.
- `tests/test_make_crud_many_to_one_canonical.py` — `test_legacy_m2o_still_supported` → test de rejet.
- `tests/test_many_to_many_canonical_generation.py` — tests legacy M2M → tests de rejet.
- `tests/test_many_to_many_pivot_integration.py` — `TestLegacyManyToManyNonRegression` → tests de rejet.
- `tests/test_pivot_fields_controlled.py` — `test_legacy_m2m_not_affected` → test de rejet.
- `tests/test_make_crud_many_to_many.py` — `_relations()` et extra relations convertis en format canonique.
- `tests/test_make_crud_partials.py`, `tests/test_make_crud_search.py` — relations.json legacy → canonique.
- `tests/meta/test_consolidation_non_overwrite_001.py`, `tests/test_build_model_canonical_routing.py`, `tests/test_entity_model_cli.py`, `tests/test_entity_db_apply.py`, `tests/test_doctor.py`, `tests/test_media_entity_canonical.py`, `tests/test_project_check.py`, `tests/test_project_audit.py` — relations.json vide legacy → canonique.

### Résultat

- 11 877 tests passent (0 échec).
- `pytest`, `compileall`, `ruff check`, `mkdocs build --strict`, `git diff --check` : tous verts.
- Format `format_version: 1` refusé dans `relations.json` par `validate_relations_definition`, `sync_relations`, `_load_crud_many_to_one_relations`, `_load_crud_many_to_many_relations`, `_load_existing_relations_doc`.
- Clés legacy (`from_entity`, `to_entity`, `foreign_key_name`, `source`, `target`, `pivot_table`, `source_key`, `target_key`) rejetées dans les documents `schema_version: "1.0"`.

---

## Mise en œuvre — LEGACY-REMOVE-003

LEGACY-REMOVE-003 nettoie les fixtures legacy restantes dans les fichiers de tests.

### Classification appliquée

- **Catégorie A (conservés)** — tests de rejet explicite du format legacy : `test_build_model_legacy_warning.py`, `test_make_crud_legacy_warning.py`, `test_build_model_canonical_routing.py`, `test_entity_semantic_validation.py` (1 test), `test_make_crud_many_to_one_canonical.py` (1 test), `test_entity_model_cli.py` (`_legacy_contact` / `_legacy_commande`), `test_entity_relations.py`, `test_relations_many_to_many.py`, `test_relations_ordered.py`, `test_many_to_many_canonical_generation.py`, `test_many_to_many_pivot_integration.py`, `test_pivot_fields_controlled.py`, `test_relations_many_to_one_canonical_sql.py`, `test_starter_scaffold_empty_relations.py`, méta-tests.
- **Catégorie B (convertis)** — fixtures entité avec `format_version: 1` dans des tests de fonctionnalité non-legacy : 31 fichiers CRUD, media, public, RBAC, form, entity.
- **Catégorie C (supprimés)** — aucun fichier entier supprimé.

### Fichiers de tests convertis (Catégorie B)

Suppression de `"format_version": 1,` dans les fixtures entité (passage à l'entité sans marqueur legacy) dans les 31 fichiers suivants :
`test_crud_bulk_delete.py`, `test_crud_filters.py`, `test_crud_filters_htmx.py`, `test_crud_filter_whitelist_001.py`, `test_crud_htmx.py`, `test_crud_sort.py`, `test_entity_form_field.py`, `test_entity_json_validation.py`, `test_entity_media_declaration.py`, `test_entity_sync_command.py`, `test_make_crud_empty_states.py`, `test_make_crud_htmx_delete.py`, `test_make_crud_htmx_pagination.py`, `test_make_crud_htmx_search.py`, `test_make_crud_media.py`, `test_make_crud_media_alt.py`, `test_make_crud_media_context.py`, `test_make_crud_media_destroy.py`, `test_make_crud_media_gallery_add.py`, `test_make_crud_media_gallery_context.py`, `test_make_crud_media_gallery_delete.py`, `test_make_crud_media_gallery_multiupload.py`, `test_make_crud_media_gallery_order.py`, `test_make_crud_media_runtime.py`, `test_make_crud_pagination.py`, `test_make_crud_sort.py`, `test_make_public_form.py`, `test_make_public_i18n.py`, `test_make_public_list.py`, `test_make_public_list_media.py`, `test_rbac_security.py`.

Conversion des fixtures relations legacy dans `test_starter_cli.py` (2 occurrences → format canonique).

### Résultat

- 11 877 tests passent (0 échec).
- `pytest`, `compileall`, `ruff check`, `mkdocs build --strict`, `git diff --check` : tous verts.
- Les fixtures entité dans les tests de fonctionnalité n'utilisent plus le marqueur `format_version: 1`.
- Les fichiers restants avec `format_version: 1` sont exclusivement des tests de rejet (Catégorie A) ou des méta-tests documentaires.

---

## Mise en œuvre — LEGACY-REMOVE-004

LEGACY-REMOVE-004 aligne la documentation sur la suppression du legacy. Le format canonique
`schema_version: "1.0"` est désormais le seul format d'entrée documenté comme accepté.

### Fichiers modifiés

- **`docs/adr/012-legacy-format-deprecation-policy.md`** — réécriture de la décision : "refusé" remplace "déprécié temporairement". Historique conservé.
- **`docs/entities/json-canonique.md`** — section Limites : "conservé temporairement" → "refusé".
- **`docs/entities/entity-validate.md`** — section erreurs et section Limites : "accepté mais non recommandé" → "refusé".
- **`docs/entities/limites-contrats-json.md`** — section "Compatibilité legacy temporaire" → "Format legacy refusé".
- **`docs/entities/migration-legacy-vers-canonique.md`** — titre et avertissement danger ajouté en tête de page (Option B du ticket).
- **`docs/entity_architecture.md`** — exemples d'entité et de `relations.json` legacy → format canonique.
- **`docs/guide.md`** — exemple d'entité et table Anatomie → format canonique.
- **`docs/crud.md`** — deux occurrences de `from_entity` dans le texte → `from`.
- **`docs/app-complete-tutorial.md`** — exemple `relations.json` et référence `from_entity` → format canonique.
- **`docs/starter-author-guide.md`** — exemple `relations.json` → format canonique.
- **`mkdocs.yml`** — titres de navigation mis à jour.

### Fichier créé

- **`tests/meta/test_legacy_remove_docs_001.py`** — tests meta documentaires.

### Résultat

- 11 877 tests passent (0 échec).
- `pytest`, `compileall`, `ruff check`, `mkdocs build --strict`, `git diff --check` : tous verts.
- Aucune page utilisateur ne présente plus `format_version: 1` comme format utilisable.
- Les audits historiques conservent les traces legacy par contexte.

---

## Mise en œuvre — LEGACY-STRICT-SCHEMA-001

LEGACY-STRICT-SCHEMA-001 ferme le dernier interstice : les entités sans aucun marqueur
de version (`format_version` ni `schema_version`) passaient silencieusement. Désormais,
`build:model` et `check:model` les refusent explicitement.

### Diagnostic

Le ticket LEGACY-REMOVE-003 avait converti les fixtures entité en supprimant
`format_version: 1`, les laissant sans marqueur de version. Ces entités circulaient
encore via le chemin interne de `validate_entity_definition` dans les deux pipelines.

### Changements apportés

- **`forge_cli/entities/model.py`** — `_load_all_entity_sources` : après le refus
  `format_version: 1`, ajout d'un refus explicite pour les entités sans
  `schema_version: "1.0"`. Le message indique le fichier et pointe le guide de
  migration. La branche `else` (chemin interne) est supprimée — seul le format
  canonique est désormais accepté par `build:model` / `check:model`.
- **`forge_cli/entities/make_crud.py`** — ajout d'un refus pour les entités sans
  `schema_version: "1.0"` et sans clé `entity` (format inconnu). Les entités en
  format interne pré-normalisé (clé `entity` présente) restent acceptées pour
  la compatibilité des tests utilisant des structures internes directement.

### Fichiers de tests créés

- **`tests/test_require_schema_version_entities.py`** — 7 tests : refus par
  `build_model` et `check_model`, acceptation du format canonique, refus par
  `make_crud`, acceptation canonique.
- **`tests/test_require_schema_version_relations.py`** — 4 tests : refus par
  `validate_relations_definition`, `sync_relations`, `build_model` ; acceptation
  du format canonique.

### Résultat

- `pytest`, `compileall`, `ruff check`, `mkdocs build --strict`, `git diff --check` : tous verts.
- Aucune entité sans `schema_version` ne peut plus franchir `build:model` ou `check:model`.
- Les relations sans `schema_version` étaient déjà refusées (LEGACY-REMOVE-002).

---

## Clôture — LEGACY-CLOSE-001

**Statut** : terminé.

Le bloc legacy est clôturé après livraison de :

- LEGACY-REMOVE-PLAN-001 ;
- LEGACY-REMOVE-001A ;
- LEGACY-REMOVE-001B ;
- LEGACY-REMOVE-002 ;
- LEGACY-REMOVE-003 ;
- LEGACY-REMOVE-004 ;
- LEGACY-STRICT-SCHEMA-001.

### État final

- Les entités utilisateur doivent déclarer `schema_version: "1.0"`.
- `relations.json` doit déclarer `schema_version: "1.0"`.
- `format_version: 1` est refusé par `build:model`, `check:model`, `make:crud`, `validate_relations_definition`.
- Les clés relationnelles legacy (`from_entity`, `to_entity`, `foreign_key_name`, `pivot_table`, `source_key`, `target_key`) sont refusées dans les documents `schema_version: "1.0"`.
- Les starters Forge sont canoniques — aucun fichier entité ou relations n'utilise `format_version: 1`.
- Les tests legacy inutiles ont été nettoyés (LEGACY-REMOVE-003) ; les tests de rejet sont conservés comme garde-fous.
- La documentation utilisateur est alignée — aucune page ne présente le legacy comme format accepté (LEGACY-REMOVE-004).
- Aucun tag ni publication PyPI n'a été effectué.

### Traces legacy restantes (intentionnelles)

| Trace | Localisation | Justification |
|---|---|---|
| Code de refus `format_version: 1` | `model.py`, `make_crud.py`, `relations.py`, `make_relation.py` | Guards de rejet — intentionnels |
| `ALLOWED_ROOT_KEYS` inclut `format_version` | `validation.py` | Pipeline interne pré-normalisé — interne uniquement |
| Fallback `from_entity` / `foreign_key_name` | `starters/relations.py` | Défense en profondeur dans le module starters |
| Vérification `format_version == 1` | `starters/scaffold.py` | Module starters — hors périmètre de ce bloc |
| Fixtures `format_version: 1` | Tests de rejet (LEGACY-REMOVE-001A/001B) | Tests de non-régression nécessaires |
| Mentions legacy | `docs/history/audits/` | Contexte historique — attendu |
