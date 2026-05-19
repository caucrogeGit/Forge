# Audit — Reclassification des tests legacy Forge

**Ticket** : LEGACY-TESTS-RECLASSIFY-001-AUDIT-AND-CLASSIFY-LEGACY-TESTS
**Date** : 2026-05-19
**Auteur** : Forge (audit pré-migration)
**Périmètre** : `tests/` (fichiers Python contenant `format_version: 1` ou des clés legacy)

---

## 1. Résumé

L'audit identifie **57 fichiers de tests runtime** utilisant des fixtures au format legacy
(`format_version: 1`, `sql_type`, `python_type`, `primary_key`, `auto_increment`, etc.)
pour un total de **268 occurrences** de `format_version` dans les tests.

La majorité des tests legacy (catégorie B) utilisent le format legacy uniquement parce
qu'ils ont été écrits avant l'introduction du format canonique `schema_version: "1.0"`.
Ils testent des fonctionnalités (CRUD, filtres, médias, public) sans valeur de rétrocompatibilité.

**9 fichiers** sont des tests de compatibilité legacy explicites à conserver (catégorie A).
**44 fichiers** doivent être migrés progressivement vers des fixtures canoniques (catégorie B).
**4 fichiers** seraient à dupliquer temporairement (catégorie C).
**0 fichier** n'est clairement obsolète à ce stade (catégorie D non peuplée).

Aucun test n'est migré ni supprimé dans ce ticket.

---

## 2. Contexte

Le format `schema_version: "1.0"` est officiel depuis ADR-012. Les starters sont 100 %
canoniques. `build:model` et `make:crud` avertissent désormais sur les entités legacy.

L'audit de support legacy (`legacy-support-core-audit-001.md`) avait identifié ~55 à 75
fichiers concernés. Ce chiffre est confirmé : **57 fichiers runtime** avec des fixtures
`format_version: 1`, hors fichiers meta.

---

## 3. Méthode d'audit

Commandes utilisées :

```bash
grep -rl '"format_version": 1' tests/ --include="*.py" | grep -v __pycache__
# → 57 fichiers runtime, 1 fichier meta

grep -rh 'format_version' tests/ --include="*.py" | wc -l
# → 268 occurrences totales
```

Fichiers triés par nombre d'occurrences (top 5) :
- `test_make_crud.py` — 16 occurrences
- `test_entity_list_filter.py` — 14 occurrences
- `test_entity_model_cli.py` — 13 occurrences
- `test_starter_suivi_comportement_eleves_canonical.py` — 10 (assertions d'absence)
- `test_starter_communes_sejours_canonical.py` — 10 (assertions d'absence)

**Distinction clé** : certains fichiers mentionnent `format_version` dans des assertions
d'absence (`assert "format_version" not in ...`). Ces fichiers sont canoniques, pas legacy.

---

## 4. Volume de tests legacy

| Périmètre | Fichiers | Occurrences |
|---|---:|---:|
| Runtime — fixtures legacy réelles | **57** | ~260 |
| Meta — assertions documentaires | 1 | ~8 |
| Starters canoniques — assertions d'absence | 5 | 22 (faux positifs) |
| **Total** | **63** | **268** |

---

## 5. Catégories de classification

### Catégorie A — Compatibilité legacy à conserver

Tests qui vérifient **volontairement** que Forge continue d'accepter les anciens projets.
À conserver tant que le support legacy existe.

### Catégorie B — Tests historiques à migrer

Tests qui utilisent le format legacy uniquement parce qu'ils ont été écrits avant
`schema_version: "1.0"`. Ils testent des fonctionnalités sans valeur de rétrocompatibilité.
À migrer progressivement vers des fixtures canoniques.

### Catégorie C — Tests à dupliquer temporairement

Tests qui couvrent un comportement critique : une version legacy (compatibilité) et une
version canonique (comportement officiel) doivent coexister pendant la transition.

### Catégorie D — Tests obsolètes ou à supprimer plus tard

Tests qui vérifient un comportement interne legacy sans valeur une fois le canonical adopté.
Non peuplée à ce stade — tous les tests legacy actuels restent pertinents pour la période de transition.

---

## 6. Matrice des fichiers concernés

### Catégorie A — Compatibilité legacy (9 fichiers)

| Fichier | Rôle | Décision |
|---|---|---|
| `test_build_model_legacy_warning.py` | Vérifie le warning legacy de `build:model` (LEGACY-WARNINGS-002) | Conserver |
| `test_make_crud_legacy_warning.py` | Vérifie le warning legacy de `make:crud` (LEGACY-WARNINGS-004) | Conserver |
| `test_build_model_canonical_routing.py` | Vérifie la coexistence legacy + canonique dans `build:model` | Conserver |
| `test_starter_scaffold_empty_relations.py` | Vérifie que le scaffold reconnaît `format_version: 1` et `schema_version: "1.0"` | Conserver |
| `test_entity_json_validation.py` | Vérifie que la validation JSON accepte le format legacy | Conserver |
| `test_entity_semantic_validation.py` | Vérifie les règles sémantiques sur des entités legacy | Conserver |
| `test_entity_relations.py` | Vérifie que les relations legacy sont reconnues | Conserver |
| `test_entity_model_cli.py` | Vérifie que le CLI (`sync:entity`, `build:model`) fonctionne sur du legacy | Conserver |
| `test_entity_sync_command.py` | Vérifie que `sync:entity` fonctionne sur une entité legacy | Conserver |

### Catégorie B — Tests historiques à migrer (44 fichiers)

**Famille CRUD (make:crud, vues, formulaires)** — 17 fichiers :

| Fichier | Occurrences | Module testé | Décision |
|---|---:|---|---|
| `test_make_crud.py` | 16 | make:crud — génération CRUD complète | Migrer — LEGACY-TESTS-MIGRATE-001 |
| `test_make_crud_empty_states.py` | 4 | make:crud — états vides | Migrer |
| `test_make_crud_htmx_delete.py` | 2 | make:crud — HTMX delete | Migrer |
| `test_make_crud_htmx_pagination.py` | 2 | make:crud — HTMX pagination | Migrer |
| `test_make_crud_htmx_search.py` | 2 | make:crud — HTMX recherche | Migrer |
| `test_make_crud_many_to_many.py` | 4 | make:crud — M2M | Migrer |
| `test_make_crud_many_to_one_canonical.py` | 5 | make:crud — M21 (canonique mais relations legacy) | Migrer |
| `test_make_crud_pagination.py` | 2 | make:crud — pagination | Migrer |
| `test_make_crud_partials.py` | 4 | make:crud — vues partielles | Migrer |
| `test_make_crud_rbac.py` | 2 | make:crud — RBAC | Migrer |
| `test_make_crud_search.py` | 7 | make:crud — recherche | Migrer |
| `test_make_crud_sort.py` | 3 | make:crud — tri | Migrer |
| `test_crud_bulk_delete.py` | 2 | CRUD — suppression en masse | Migrer — LEGACY-TESTS-MIGRATE-002 |
| `test_crud_filters.py` | 1 | CRUD — filtres | Migrer |
| `test_crud_filters_htmx.py` | 2 | CRUD — filtres HTMX | Migrer |
| `test_crud_filter_whitelist_001.py` | 1 | CRUD — whitelist filtres | Migrer |
| `test_crud_htmx.py` | 2 | CRUD — HTMX général | Migrer |
| `test_crud_sort.py` | 2 | CRUD — tri | Migrer |

**Famille Média** — 12 fichiers :

| Fichier | Occurrences | Module testé | Décision |
|---|---:|---|---|
| `test_make_crud_media.py` | 2 | make:crud — média | Migrer — LEGACY-TESTS-MIGRATE-003 |
| `test_make_crud_media_alt.py` | 1 | make:crud — média alt | Migrer |
| `test_make_crud_media_context.py` | 1 | make:crud — contexte média | Migrer |
| `test_make_crud_media_destroy.py` | 2 | make:crud — suppression média | Migrer |
| `test_make_crud_media_gallery_add.py` | 3 | make:crud — galerie ajout | Migrer |
| `test_make_crud_media_gallery_context.py` | 2 | make:crud — galerie contexte | Migrer |
| `test_make_crud_media_gallery_delete.py` | 2 | make:crud — galerie suppression | Migrer |
| `test_make_crud_media_gallery_multiupload.py` | 4 | make:crud — galerie multi | Migrer |
| `test_make_crud_media_gallery_order.py` | 2 | make:crud — galerie ordre | Migrer |
| `test_make_crud_media_runtime.py` | 2 | make:crud — média runtime | Migrer |
| `test_entity_media_declaration.py` | 4 | déclaration média entité | Migrer |
| `test_entity_form_field.py` | 2 | champs de formulaire | Migrer |

**Famille Public (public:form, public:list)** — 4 fichiers :

| Fichier | Occurrences | Module testé | Décision |
|---|---:|---|---|
| `test_make_public_form.py` | 3 | public form | Migrer — LEGACY-TESTS-MIGRATE-004 |
| `test_make_public_i18n.py` | 2 | public i18n | Migrer |
| `test_make_public_list.py` | 2 | public list | Migrer |
| `test_make_public_list_media.py` | 5 | public list média | Migrer |

**Famille Relations** — 4 fichiers :

| Fichier | Occurrences | Module testé | Décision |
|---|---:|---|---|
| `test_relations_ordered.py` | 4 | relations ordonnées | Migrer — LEGACY-TESTS-MIGRATE-001 |
| `test_relations_many_to_many.py` | 7 | relations M2M | Migrer |
| `test_relations_many_to_one_canonical_sql.py` | 6 | relations M21 SQL | Migrer |
| `test_entity_list_filter.py` | 14 | filtres liste entité | Migrer |

**Famille Outils / Diagnostic** — 4 fichiers :

| Fichier | Occurrences | Module testé | Décision |
|---|---:|---|---|
| `test_doctor.py` | 4 | forge doctor | Migrer — LEGACY-TESTS-MIGRATE-005 |
| `test_project_audit.py` | 1 | audit projet | Migrer |
| `test_project_check.py` | 5 | vérification projet | Migrer |
| `test_entity_db_apply.py` | 4 | db:apply | Migrer |

**Famille RBAC / Sécurité** — 2 fichiers :

| Fichier | Occurrences | Module testé | Décision |
|---|---:|---|---|
| `test_rbac_security.py` | 1 | RBAC sécurité | Migrer — LEGACY-TESTS-MIGRATE-005 |
| `test_rbac_sql.py` | 1 | RBAC SQL | Migrer |

**Divers** — 1 fichier :

| Fichier | Occurrences | Module testé | Décision |
|---|---:|---|---|
| `test_make_relation_command.py` | 1 | make:relation CLI | Migrer |

### Catégorie C — À dupliquer temporairement (4 fichiers)

Tests qui couvrent un comportement critique avec les deux formats.

| Fichier | Raison | Décision |
|---|---|---|
| `test_many_to_many_canonical_generation.py` | Teste la génération M2M avec les deux formats — couverture critique | Dupliquer : conserver version legacy + ajouter version canonique |
| `test_many_to_many_pivot_integration.py` | Intégration pivot avec legacy | Dupliquer pendant la transition |
| `test_pivot_fields_controlled.py` | Champs pivot avec format legacy | Dupliquer |
| `test_media_entity_canonical.py` | Vérifie canonique mais repose sur fixtures legacy pour les relations | Dupliquer |

### Catégorie D — Obsolètes / à supprimer plus tard (0 fichier)

Aucun fichier clairement obsolète identifié à ce stade. La classification D sera peuplée
lors du ticket LEGACY-REMOVE-001, une fois la décision de suppression du support legacy prise.

---

## 7. Tests à conserver

Les 9 fichiers de catégorie A constituent le **socle minimal de tests de compatibilité
legacy**. Ils doivent être maintenus actifs tant que le support legacy (`format_version: 1`)
reste dans le code.

Critères de conservation :
- Le test vérifie **explicitement** qu'une entité legacy est acceptée.
- Ou le test vérifie qu'un warning est bien émis pour une entité legacy.
- Ou le test vérifie la **coexistence** des deux formats.

---

## 8. Tests à migrer

Les 44 fichiers de catégorie B peuvent être migrés progressivement. La migration consiste
à remplacer les fixtures `format_version: 1` par des fixtures `schema_version: "1.0"`.

**Ordre recommandé** :

1. CRUD (`test_make_crud_*.py`, `test_crud_*.py`) — famille la plus grande, migration par blocs
2. Média (`test_make_crud_media_*.py`) — directement liée au CRUD
3. Public (`test_make_public_*.py`) — peu d'occurrences
4. Relations (`test_relations_*.py`) — quelques dépendances croisées
5. Outils / Diagnostic — peu d'occurrences, migration simple

---

## 9. Tests à dupliquer temporairement

Les 4 fichiers de catégorie C couvrent des comportements critiques (M2M, pivot, médias)
qui doivent fonctionner dans les deux formats pendant la période de transition.

Stratégie : ajouter une classe ou une fonction `_canonical_*` dans chaque fichier, sans
supprimer les fixtures legacy existantes.

---

## 10. Tests obsolètes ou à supprimer plus tard

Aucun fichier identifié comme obsolète à ce stade. La catégorie D sera peuplée lors du
ticket LEGACY-REMOVE-001, conditionné à la décision de suppression totale du format legacy.

---

## 11. Stratégie recommandée

1. **Conserver** les 9 fichiers de catégorie A sans modification.
2. **Ne pas migrer** dans ce ticket — migration progressive, par famille, dans des tickets dédiés.
3. **Migrer en priorité** les fichiers CRUD (`test_make_crud.py`, `test_crud_filters.py`, etc.)
   car ils concentrent le plus d'occurrences et ne testent pas de compatibilité legacy.
4. **Dupliquer** les 4 fichiers de catégorie C lors de la migration des familles CRUD/Média.
5. **Supprimer** uniquement après la décision LEGACY-REMOVE-001 — pas avant.

---

## 12. Tickets futurs proposés

| Ticket | Objectif | Priorité |
|---|---|---|
| `LEGACY-TESTS-MIGRATE-001` | Migrer fixtures legacy — famille CRUD (`test_make_crud.py` et variants) | Haute |
| `LEGACY-TESTS-MIGRATE-002` | Migrer fixtures legacy — famille CRUD bulk/filters/sort | Moyenne |
| `LEGACY-TESTS-MIGRATE-003` | Migrer fixtures legacy — famille Média | Moyenne |
| `LEGACY-TESTS-MIGRATE-004` | Migrer fixtures legacy — famille Public | Faible |
| `LEGACY-TESTS-MIGRATE-005` | Migrer fixtures legacy — Outils, RBAC, Relations | Faible |
| `LEGACY-TESTS-COMPAT-001` | Définir et documenter le socle minimal de tests legacy | Moyenne |
| `LEGACY-TESTS-CLEANUP-001` | Supprimer tests legacy obsolètes — après LEGACY-REMOVE-001 | Différé |
