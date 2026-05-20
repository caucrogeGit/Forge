# Audit — RELEASE-AUDIT-002 post-corrections terrain

**Ticket** : RELEASE-AUDIT-002
**Date** : 2026-05-21
**Objectif** : Vérifier l'état de Forge après les corrections issues de FIELD-TEST-APP-001.

---

## 1. Résumé

Les trois frictions détectées lors du test terrain ont été corrigées et
validées. Aucun bloquant détecté. Forge est dans un état propre.

**Verdict : AUDIT OK — corrections terrain validées, prêt pour RELEASE-BETA-NEXT-001.**

---

## 2. Contexte

| Friction | Description | Ticket correctif |
|---|---|---|
| F-001 | Confusion documentaire `"entity"` vs `"name"` comme clé racine | FIELD-FIX-001 |
| F-002 | Structure `mvc/entities/<nom>/<nom>.json` insuffisamment documentée | FIELD-FIX-001 |
| F-003 | Garde `make:crud` many-to-many trop strict (côté inverse bloqué) | FIELD-FIX-M2M-GUARD-001 |

---

## 3. Méthode d'audit

Commandes exécutées :

```bash
git status / git log --oneline -8
python forge.py --version
python forge.py schema:list
python forge.py schema:doctor
python forge.py entity:validate          # sur forge-field-test-app
python forge.py build:model              # sur forge-field-test-app
python forge.py rbac:validate            # sur forge-field-test-app
python forge.py rbac:audit               # sur forge-field-test-app

pytest tests/meta/test_field_test_app_001.py -q
pytest tests/meta/test_field_fix_entity_docs_001.py -q
pytest tests/meta/test_field_audit_m2m_guard_001.py -q
pytest tests/test_make_crud_pivot_fields_guard.py -q
pytest tests/test_make_crud_many_to_many.py -q
pytest tests/test_make_crud_many_to_many_canonical.py -q
pytest tests/test_make_pivot_crud.py -q
pytest tests/test_pivot_advanced_e2e.py -q
pytest (complet)
python -m compileall -q .
ruff check .
mkdocs build --strict
git diff --check
```

Zones auditées :

- Documentation entités (`json-canonique.md`, `entity_architecture.md`, `15-minutes.md`,
  `app-complete-tutorial.md`)
- Implémentation du garde M2M (`relations_loader.py`)
- Rapport terrain (`field-test-app-001.md`)
- Rapport audit M2M (`field-audit-m2m-guard-001.md`)
- Tests meta et tests unitaires

---

## 4. Corrections terrain vérifiées

### F-001 — Clé canonique `"name"`

- `docs/entities/json-canonique.md` : clé `"name"` documentée clairement, exemple avec `"name": "Article"`.
- `docs/entity_architecture.md` : exemple legacy corrigé vers le format canonique (`"name"`, `schema_version`, types Forge).
- `docs/15-minutes.md` : exemple entièrement mis à jour (clé `"name"`, types Forge, `build:model`).
- `docs/app-complete-tutorial.md` : banner `!!! warning` ajouté signalant le format legacy.

Cas légitimes de `"entity"` conservés :

- `docs/starter-author-guide.md` : `"entity"` est une clé du format starter (distinct du JSON entité) — correct.
- `docs/entities/migration-legacy-vers-canonique.md` : montre intentionnellement l'ancien format — correct.
- `docs/starters/02-utilisateurs-auth/index.md` : format starter — correct.

**Verdict F-001 : OK.**

### F-002 — Structure `mvc/entities/<nom>/<nom>.json`

- `docs/entities/json-canonique.md` : section "Structure des fichiers" ajoutée avec :
  - arborescence `mvc/entities/article/article.json`
  - règle `mvc/entities/relations.json` à la racine
  - comportement `build:model` (scan sous-dossiers, ignore `__*`)
  - exemples de chemins valides

**Verdict F-002 : OK.**

### F-003 — Garde `make:crud` many-to-many côté inverse

- `forge_cli/entities/crud/relations_loader.py` : le `raise ValueError` a été déplacé après
  le filtre `if m2m_source.lower() not in current_names: continue`.
- Résultat :
  - `make:crud Article` : bloqué si `Article.tags` contient des `pivot.fields[]` incompatibles ✓
  - `make:crud Tag` : autorisé même quand le pivot appartient à `Article` ✓
  - `make:pivot-crud Article tags` : inchangé, toujours fonctionnel ✓
- Message d'erreur : mentionne désormais `make:pivot-crud` explicitement.

**Verdict F-003 : OK.**

---

## 5. Documentation entités

| Point | État |
|---|---|
| Clé `"name"` documentée comme canonique | OK |
| Aucun exemple canonique utilisant `"entity"` comme clé racine | OK |
| Structure `mvc/entities/article/article.json` documentée | OK |
| `mvc/entities/relations.json` à la racine documenté | OK |
| `build:model` — comportement sous-dossiers expliqué | OK |
| `entity:validate` — commande de diagnostic référencée | OK |

---

## 6. Garde make:crud many-to-many

| Point | État |
|---|---|
| `make:crud Article` bloqué si `position` nullable: false | OK |
| `make:crud Tag` autorisé malgré pivot d'Article | OK |
| `make:pivot-crud Article tags` fonctionnel | OK |
| Message d'erreur mentionne `make:pivot-crud` | OK |
| Fix limité à `relations_loader.py` | OK |
| Rapport FIELD-AUDIT-M2M-GUARD-001 mis à jour | OK |

---

## 7. Commandes Forge (sur forge-field-test-app)

| Commande | Résultat |
|---|---|
| `forge --version` | Forge 1.0.0b5 |
| `forge schema:list` | 6 schémas OK |
| `forge schema:doctor` | 0 erreur |
| `forge entity:validate` | 3 fichiers valides, 0 erreur |
| `forge build:model` | 5 régénérés, 4 préservés |
| `forge rbac:validate` | 2 rôles, 2 entités, OK |
| `forge rbac:audit` | 0 avertissement, OK |

---

## 8. Tests et validations

| Validation | Résultat |
|---|---|
| `test_field_test_app_001.py` | 22 passed |
| `test_field_fix_entity_docs_001.py` | 29 passed |
| `test_field_audit_m2m_guard_001.py` | 18 passed |
| `test_make_crud_pivot_fields_guard.py` | 19 passed |
| `test_make_crud_many_to_many.py` | passé |
| `test_make_crud_many_to_many_canonical.py` | passé |
| `test_make_pivot_crud.py` | passé |
| `test_pivot_advanced_e2e.py` | passé |
| Ciblés terrain + pivot | 131 passed |
| pytest complet | **12 573 passed, 6 skipped, 0 failed** |
| `python -m compileall -q .` | OK |
| `ruff check .` | OK |
| `mkdocs build --strict` | OK |
| `git diff --check` | OK |
| `git status` | copie propre |

---

## 9. Bloquants

**Aucun.**

---

## 10. Non-bloquants

- `docs/app-complete-tutorial.md` conserve des exemples en format legacy (banner d'avertissement
  présent). Refonte complète prévue dans un ticket documentaire dédié.
- La refonte de `docs/15-minutes.md` est partielle (seul l'exemple principal a été mis à jour ;
  le reste du tutoriel reste cohérent avec la correction apportée).

---

## 11. Décision

**Verdict : AUDIT OK — corrections terrain validées, prêt pour RELEASE-BETA-NEXT-001.**

---

## 12. Prochains tickets recommandés

| Priorité | Ticket | Objectif |
|---|---|---|
| 1 | **RELEASE-BETA-NEXT-001** | Préparer la prochaine bêta Forge |
| 2 | (optionnel) Refonte complète `app-complete-tutorial.md` | Aligner sur le format canonique |

---

## 13. Publication PyPI différée

- Publication PyPI tentée : NON
- forge-mvc republié : NON
- Tag modifié : NON
- Opt-ins publiés : NON
