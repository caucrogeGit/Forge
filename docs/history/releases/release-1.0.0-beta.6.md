# Release — Forge 1.0.0-beta.6

**Version** : `1.0.0b6` (PEP 440) / `1.0.0-beta.6` (SemVer)
**Tag** : `v1.0.0-beta.6`
**Date** : 2026-05-21

---

## Résumé

Forge 1.0.0-beta.6 consolide le cycle de tickets RBAC, Pivot advanced,
tests terrain et corrections DX issus du premier test terrain réel.

Aucune rupture d'API publique. `make:crud` reste neutre vis-à-vis du Pivot
advanced. Les routes pivot ne sont pas branchées automatiquement — elles
restent opt-in via `make:pivot-crud`.

---

## Nouveautés principales

### JSON Schema

- 6 schémas contractuels : `entity`, `field`, `relations`, `pivot`, `rbac`, `common`
- Validation via `entity:validate` (sémantique + structure)
- Autocomplétion VS Code avec `$schema`
- Registre `schemas/forge.schema.index.json`

### RBAC opt-in

- Contrat déclaratif dans `mvc/security/rbac.json`
- Commandes : `rbac:validate`, `rbac:audit`
- Intégration `make:crud` : permissions injectées dans le contrôleur généré
- Schéma `rbac.schema.json` contractuel

### Pivot advanced

- `PivotAdvancedService` : injectable, API `attach`, `detach`, `update`, `get_by_id`, etc.
- `PivotFieldConstraint` : contraintes déclaratives (required, nullable, unique_pair, id_field)
- `PivotConstraintError` / `PivotFormError` / `pivot_error_to_form_error` : couche UX
- `make:pivot-crud` : générateur opt-in de sous-CRUD pivot (contrôleur + templates)

### DX / VS Code

- Autocomplétion JSON Schema dans les fichiers d'entités et de relations
- Erreurs de structure détectées en temps réel dans l'éditeur

---

## Legacy removal

- Format `format_version: 1` refusé par `build:model` et `make:crud`
- Guide de migration `docs/entities/migration-legacy-vers-canonique.md`

---

## Test terrain

- **FIELD-TEST-APP-001** : premier test terrain Forge complet
  - Flux validé : `entity:validate` → `build:model` → `make:crud` × 2 → `make:pivot-crud` → `rbac:validate` → `rbac:audit`
  - 3 frictions détectées et tracées (F-001, F-002, F-003)

---

## Corrections issues du terrain

- **F-001** — Clé canonique `"name"` documentée clairement (`FIELD-FIX-001`)
  - Exemples legacy `"entity"` corrigés dans `entity_architecture.md` et `15-minutes.md`
  - Banner d'avertissement dans `app-complete-tutorial.md`

- **F-002** — Structure `mvc/entities/<nom>/<nom>.json` documentée (`FIELD-FIX-001`)
  - Section "Structure des fichiers" ajoutée dans `docs/entities/json-canonique.md`
  - Comportement `build:model` (scan sous-dossiers) expliqué
  - `mvc/entities/relations.json` à la racine documenté

- **F-003** — Garde `make:crud` many-to-many côté inverse corrigé (`FIELD-FIX-M2M-GUARD-001`)
  - Avant : `make:crud Tag` était bloqué même quand le pivot appartenait à `Article`
  - Après : le garde ne s'applique qu'au côté `from` de la relation
  - Message d'erreur amélioré : mentionne `make:pivot-crud` explicitement

---

## Validations

- pytest complet : **12 573 passed, 6 skipped, 0 failed**
- `python -m compileall -q .` : OK
- `ruff check .` : OK
- `mkdocs build --strict` : OK
- Commandes Forge (`schema:list`, `schema:doctor`, `entity:validate`, `build:model`, `rbac:validate`, `rbac:audit`) : toutes OK

---

## Limites connues

- `docs/app-complete-tutorial.md` conserve des exemples en format legacy (banner présent) — refonte complète prévue dans un ticket documentaire dédié.
- `forge-mvc-mfa` reste Pre-Alpha — `SEC-MFA-SECRET-ENCRYPTION-001` requis avant publication.
- `forge-mvc-media` reste source-only après extraction Phase 11.

---

## Publication PyPI

**Aucune publication PyPI dans cette release.**

- `forge-mvc` sera publié séparément.
- Les packages opt-ins (`forge-mvc-rbac`, `forge-mvc-workflow`, `forge-mvc-stats`) seront publiés dans **PYPI-OPTINS-001**.
- `forge-mvc-media` et `forge-mvc-mfa` restent non publiés.
