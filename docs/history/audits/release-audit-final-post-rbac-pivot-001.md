# Audit final — Forge post-RBAC et post-Pivot advanced

**Ticket** : RELEASE-AUDIT-001-FINAL-FORGE-AUDIT-POST-RBAC-PIVOT
**Date** : 2026-05-20
**Statut** : AUDIT OK — aucun bloquant détecté avant test terrain

---

## 1. Résumé

Audit final de l'état de Forge après intégration des blocs :
legacy removal, JSON Schema, RBAC contractuel, RBAC applicatif opt-in,
Pivot advanced, VS Code DX et documentation consolidée.

**Verdict : AUDIT OK** — aucun bloquant détecté.
Forge est prêt pour `FIELD-TEST-APP-001` puis `RELEASE-BETA-NEXT-001`.

---

## 2. Contexte

### Blocs livrés avant cet audit

| Bloc | Statut |
|---|---|
| Legacy removal | Terminé — `test_legacy_close_001.py` |
| RBAC contractuel | Terminé — `test_rbac_contract_close_001.py` |
| RBAC applicatif opt-in | Terminé — `test_rbac_module_close_001.py` |
| Pivot advanced | Terminé — `test_pivot_advanced_close_001.py` |
| VS Code DX | Terminé — `test_vscode_dx_002.py` |
| Documentation consolidée | Terminé — mkdocs strict OK |

---

## 3. Méthode d'audit

### Commandes exécutées

```bash
git status && git log --oneline -10 && git tag --list 'v*'

python forge.py --version
python forge.py schema:list
python forge.py schema:doctor
python forge.py entity:validate
python forge.py rbac:validate
python forge.py rbac:validate --json
python forge.py rbac:audit
python forge.py rbac:audit --json
python forge.py build:model
python forge.py make:pivot-crud Article tags

pytest tests/test_rbac_validate_command.py tests/test_rbac_audit_command.py \
  tests/test_rbac_contract_loader.py tests/test_rbac_contract_permissions.py \
  tests/test_rbac_contract_guards.py -q
pytest tests/test_pivot_advanced_service.py tests/test_make_pivot_crud.py \
  tests/test_pivot_advanced_e2e.py tests/test_pivot_advanced_constraints.py \
  tests/test_pivot_advanced_error_ux.py -q
pytest tests/meta/test_rbac_module_close_001.py tests/meta/test_pivot_advanced_close_001.py \
  tests/meta/test_legacy_close_001.py -q
pytest
python -m compileall -q .
ruff check .
mkdocs build --strict
```

### Zones auditées

- `pyproject.toml` — version, classifiers, packages
- `forge.py` — entry points, version affichée
- `core/pivot_advanced.py` — API Pivot advanced
- `forge_cli/entities/make_crud.py` — neutralité
- `forge_cli/entities/make_pivot_crud.py` — commande pivot
- `forge_cli/entities/entity_validate.py` — validation canonique
- `forge_cli/entities/validation.py` — code legacy validator
- `schemas/` — 7 fichiers schémas
- `packages/` — 5 paquets opt-in
- `docs/` — pages mkdocs
- `tests/meta/` — 224 fichiers meta

---

## 4. État Git

| Critère | Résultat |
|---|---|
| Branche | `main` |
| État copie de travail | propre |
| Cohérence des 10 derniers commits | OK — PIVOT-ADVANCED-*, RBAC-MODULE-CLOSE-001 |
| Tags existants | `v1.0.0-beta.1` à `v1.0.0-beta.5` — aucun tag non intentionnel |
| Push non autorisé | aucun |
| Fichiers temporaires commités | aucun |

---

## 5. Version et packaging

| Critère | Résultat |
|---|---|
| Version `pyproject.toml` | `1.0.0b5` |
| Version affichée `forge.py --version` | `Forge 1.0.0b5` — cohérent |
| Classifier stable | absent — `1.0.0b5` est correctement bêta |
| Packages opt-in | 5 présents : `forge-mvc-media`, `forge-mvc-mfa`, `forge-mvc-rbac`, `forge-mvc-stats`, `forge-mvc-workflow` |
| Schémas inclus | 7 schémas dans `schemas/` |
| Publication PyPI | non effectuée dans ce bloc |

---

## 6. Contrats JSON Schema

| Schéma | Statut |
|---|---|
| `common.schema.json` | OK |
| `field.schema.json` | OK |
| `entity.schema.json` | OK — ne contient pas de clé `rbac` |
| `pivot.schema.json` | OK |
| `relations.schema.json` | OK |
| `rbac.schema.json` | OK |
| `forge.schema.index.json` | OK |

- `schema:list` : 6 schémas actifs — OK
- `schema:doctor` : 0 erreur
- `entity:validate` : requiert `schema_version: "1.0"` — OK
- `rbac:validate` : fonctionne, retourne JSON valide avec `--json`
- `rbac:audit` : fonctionne, retourne JSON valide avec `--json`

---

## 7. Legacy removal

- `entity:validate` ignore les fichiers sans `schema_version: "1.0"` — OK
- `validation.py` contient encore du code `format_version` — code legacy conservé
  pour la compatibilité interne. Non exposé à l'utilisateur via `entity:validate`.
  **Non-bloquant** — voir section 14.
- Tests meta `test_legacy_close_001.py` : passent — OK
- 57 tests du groupe clôture legacy : passent — OK

---

## 8. RBAC contractuel et applicatif

| Critère | Résultat |
|---|---|
| `entity.schema.json` ne contient pas `rbac` | OK — vérifié |
| Emplacement contractuel `mvc/security/rbac.json` | confirmé |
| `rbac:validate` fonctionne | OK — `exists: false` attendu (pas de projet applicatif) |
| `rbac:audit` fonctionne | OK — sortie JSON valide |
| `forge-mvc-rbac` exposé dans `packages/` | OK |
| `make:crud` ne lit pas `rbac.json` | OK — confirmé |
| Routes non protégées automatiquement | OK |
| Documentation `rbac-usage.md` | présente dans docs |
| 146 tests RBAC | passent — OK |

**Observation** : `make:crud` lit un `rbac` optionnel depuis l'entité JSON (inline,
via `definition.get("rbac")`) pour générer des vues conditionnelles. Ce mécanisme
est distinct de `rbac.json` applicatif et de `forge-mvc-rbac`. Il n'est pas couvert
par `entity.schema.json`. **Non-bloquant** — comportement documenté, testé, stable.

---

## 9. Pivot advanced

| Critère | Résultat |
|---|---|
| `PivotAdvancedService` | présent dans `core/pivot_advanced.py` |
| `PivotFieldConstraint` | présent |
| `PivotConstraintError` avec `code`/`field` | présent |
| `PivotFormError` | présent |
| `pivot_error_to_form_error` | présent |
| `make:pivot-crud` | fonctionne (erreur attendue sans relation Article.tags) |
| Tests E2E SQLite in-memory | 15 tests — passent |
| Contraintes required / nullable / unique_pair / id_field | 34 tests — passent |
| Erreurs UX | 27 tests — passent |
| Documentation `pivot-advanced.md` | présente, 12 sections |
| `make:crud` neutre | confirmé — PivotAdvancedService absent de make_crud.py |
| Routes pivot non branchées automatiquement | confirmé |
| 119 tests Pivot advanced | passent — OK |

---

## 10. make:crud et neutralité du core

- `make_crud.py` : contient `_RBAC_ACTION_TO_METHOD` (inline RBAC pour vues) — distinct de `rbac.json`
- `make_crud.py` : ne contient pas `PivotAdvancedService`, `PivotConstraintError`, `PivotFormError`, `pivot_error_to_form_error`, `make:pivot-crud`
- `make:crud` ne lit pas `rbac.json`
- `make:crud` ne lit pas `pivot.fields[]`
- Le garde-fou PIVOT-CRUD-002 bloque `make:crud` si `pivot.fields[]` contient des champs NOT NULL

---

## 11. Documentation

| Critère | Résultat |
|---|---|
| `mkdocs build --strict` | OK |
| `docs/entities/pivot-advanced.md` | présente, référencée dans mkdocs.yml |
| Pages RBAC | présentes (`rbac-contract.md`, `rbac-usage.md`) |
| Pages pivot | présentes (`pivots-many-to-many.md`, `pivot-advanced.md`) |
| Pages legacy | retirées ou alignées |
| Roadmap | cohérente |
| Aucune mention de routes automatiques RBAC/Pivot | confirmé |

---

## 12. Tests et validations

| Validation | Résultat |
|---|---|
| `pytest` complet | 12 486 passed, 6 skipped |
| `python -m compileall -q .` | OK |
| `ruff check .` | All checks passed |
| `mkdocs build --strict` | OK |
| `git diff --check` | OK |
| Tests meta | 224 fichiers, tous passent |
| Tests RBAC ciblés | 146 passent |
| Tests Pivot advanced ciblés | 119 passent |
| Tests meta clôture (legacy + RBAC + Pivot) | 57 passent |

---

## 13. Blocages

**Aucun blocage détecté.**

---

## 14. Non-bloquants

| Observation | Impact | Recommandation |
|---|---|---|
| `validation.py` contient du code `format_version` | nul — non exposé via `entity:validate` canonique | Peut être nettoyé dans un ticket dédié si souhaité |
| `make:crud` lit un `rbac` inline optionnel depuis entity JSON via `_RBAC_ACTION_TO_METHOD` | nul — comportement stable, testé, distinct de `rbac.json` | Documenter explicitement dans un ticket dédié si nécessaire |
| 6 tests `skipped` | nul — skips intentionnels | Aucune action requise |

---

## 15. Décision

**Verdict : AUDIT OK — aucun bloquant détecté avant test terrain.**

Forge est fonctionnellement complet sur les blocs suivants :
- contrats JSON Schema stricts
- legacy removal
- RBAC contractuel + applicatif opt-in
- Pivot advanced avec service, contraintes et erreurs UX
- documentation utilisateur

Les deux non-bloquants identifiés sont cosmétiques et sans impact sur le fonctionnement.

---

## 16. Prochains tickets recommandés

| Ticket | Objectif |
|---|---|
| **FIELD-TEST-APP-001** | Créer une vraie application terrain avec Forge — valider le workflow développeur complet |
| **RELEASE-BETA-NEXT-001** | Préparer la prochaine bêta — version, CHANGELOG, tag |
| **PYPI-OPTINS-001** | Publier les paquets opt-in avec prudence |
| `MAKE-CRUD-RBAC-INLINE-DOC-001` *(optionnel)* | Documenter le mécanisme inline RBAC dans `make:crud` |

Aucune publication PyPI ni création de tag n'a été effectuée dans ce ticket.
