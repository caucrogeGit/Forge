# ADR-013 — Politique nullable / required dans les contrats JSON Forge

## Statut

Acceptée — Forge 3.x (ticket `NULLABLE-CONTRACT-002-DECIDE-NULLABLE-REQUIRED-RULE`).

---

## Date

2026-05-19

---

## Contexte

L'audit NULLABLE-CONTRACT-001 a révélé trois incohérences dans le comportement de `nullable`
et `required` entre `fields[]` d'entité et `pivot.fields[]` :

1. **Défaut absent** : entité → `NOT NULL` ; pivot → `NULL` ; `field.schema.json` dit `default: true`.
2. **`required: false` sans `nullable`** : entité → `NOT NULL` ; pivot → `NULL`.
3. **`required: true + nullable: true`** : entité → `NULL` (`nullable` gagne) ; pivot → `NOT NULL` (`required` gagne).

Ces incohérences proviennent d'une règle implicite jamais formalisée :

- `canonical_model_normalizer.py` utilise `field.get("nullable", False)` (défaut NOT NULL).
- `relations.py` utilise `field.get("nullable", True)` + `required` inconditionnel (défaut NULL).
- `field.schema.json` déclare `nullable: default true` pour les deux contextes.

---

## Problème

Sans règle officielle, il est impossible de :

- écrire les tests de non-régression corrects ;
- documenter le comportement de façon cohérente ;
- corriger le runtime sans risque de rupture involontaire.

---

## Décision

**Forge adopte la règle : champ nullable par défaut, `required` prioritaire.**

---

## Règle officielle

| Cas | Résultat officiel |
|---|---|
| absent (ni `nullable` ni `required`) | `NULL` |
| `nullable: true` | `NULL` |
| `nullable: false` | `NOT NULL` |
| `required: true` (sans `nullable`) | `NOT NULL` |
| `required: false` (sans `nullable`) | `NULL` |
| `required: true + nullable: true` | `NOT NULL` (`required` gagne) |
| `required: true + nullable: false` | `NOT NULL` |

**Formule unifiée** :

```python
nullable = field.get("nullable", True)      # défaut True (NULL)
if field.get("required") is True:
    nullable = False                        # required gagne toujours
```

---

## Exemples

```json
{ "name": "titre", "type": "string", "max_length": 80 }
```
→ `NULL` (absent = nullable par défaut)

```json
{ "name": "titre", "type": "string", "max_length": 80, "required": true }
```
→ `NOT NULL` (`required` force)

```json
{ "name": "note", "type": "text", "nullable": true }
```
→ `NULL` (explicite)

```json
{ "name": "code", "type": "string", "max_length": 10, "required": true, "nullable": true }
```
→ `NOT NULL` (`required` prioritaire sur `nullable`)

---

## Justification

- **Cohérence avec `field.schema.json`** : le schéma déclare `nullable: default true`.
  La règle retenue respecte ce défaut.
- **Cohérence entre entité et pivot** : les deux contextes partagent `field.schema.json`.
  La règle doit être identique.
- **`required` comme signal SQL** : `required: true` signifie "obligatoire" — ce qui implique
  `NOT NULL`. Le laisser contredire par `nullable: true` est contre-intuitif.
- **Optionnel par défaut** : un champ non marqué `required` ou `nullable: false` est
  naturellement optionnel (`NULL`).

### Pourquoi rejeter les autres options

**Option A (conserver le comportement actuel)** : entérine trois incohérences sans règle.
Les correctifs futurs seraient imprévisibles. Rejetée.

**Option C (NOT NULL par défaut partout)** : contredit `field.schema.json` (`default: true`).
Imposerait de modifier le schéma. Rejetée.

**Option D partielle (nullable gagne sur required)** : laisser `nullable: true` écraser
`required: true` est surprenant — un champ obligatoire en formulaire peut accepter NULL
en base. Rejetée.

---

## Conséquences

### Sur le runtime (non corrigé dans ce ticket)

Le code actuel dévie de cette règle dans `canonical_model_normalizer.py` :

```python
# Actuel — déviant
nullable = bool(field.get("nullable", False))  # défaut NOT NULL — incorrect
if field.get("required") and not field.get("nullable"):
    nullable = False                            # required ne gagne pas si nullable=True
```

La correction sera apportée dans **NULLABLE-CONTRACT-003**.

### Sur la documentation (non corrigée dans ce ticket)

- `entity-schema.md` dit `nullable: défaut true` — c'est correct selon la règle retenue,
  mais le comportement runtime actuel est `False`. À corriger dans **NULLABLE-DOC-FIX-001**
  pour préciser l'écart temporaire.
- `pivots-many-to-many.md` ne précise pas la priorité de `required`. À corriger dans
  **NULLABLE-DOC-FIX-001**.

### Sur les tests (non modifiés dans ce ticket)

`test_build_model_canonical_normalizer.py::TestConstraints::test_default_nullable_is_false`
teste le comportement actuel (déviant). Ce test devra être mis à jour dans
**NULLABLE-CONTRACT-003** pour refléter la règle officielle (absent → NULL).

### Sur les starters et fixtures

Les starters sont déjà en format canonique avec `nullable` explicite sur les champs
concernés. Aucun impact attendu sur les starters existants lors de la correction runtime.

---

## Hors périmètre de ce ticket

- Modifier `canonical_model_normalizer.py` — voir `NULLABLE-CONTRACT-003`.
- Modifier `relations.py` (comportement pivot déjà conforme à la règle retenue).
- Modifier les schémas JSON.
- Modifier les fixtures de tests.
- Corriger la documentation utilisateur en détail.

---

## Tickets futurs

| Ticket | Objectif | Priorité |
|---|---|---|
| `NULLABLE-DOC-FIX-001` | Corriger `entity-schema.md`, `pivots-many-to-many.md`, `types-forge-mariadb.md` | Haute |
| `NULLABLE-CONTRACT-003` | Appliquer la règle officielle dans `canonical_model_normalizer.py` + tests | Haute |

---

## Référence

- Audit : `docs/history/audits/nullable-contract-audit-001.md`
- Décision héritière de NULLABLE-CONTRACT-001 (audit) et NULLABLE-CONTRACT-002 (décision)
