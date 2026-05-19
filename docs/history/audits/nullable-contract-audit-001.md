# Audit — Comportement nullable dans les contrats JSON Forge

**Ticket** : NULLABLE-CONTRACT-001-AUDIT-NULLABLE-BEHAVIOR
**Date** : 2026-05-19
**Auteur** : Forge (audit post-migration legacy)
**Périmètre** : `schemas/`, `forge_cli/entities/`, `tests/`, `docs/entities/`

---

## 1. Résumé

L'audit révèle **trois incohérences** dans le comportement de `nullable` :

1. **Défaut entité vs schéma** : `field.schema.json` déclare `nullable: default true`, mais
   le normaliseur canonique utilise `False` comme défaut pour les `fields[]` d'entité.

2. **Défaut entité vs pivot** : un champ sans `nullable` ni `required` génère `NOT NULL`
   dans une entité et `NULL` dans un pivot.

3. **Conflit `required: true + nullable: true`** : le comportement diverge selon le contexte —
   dans une entité, `nullable` gagne (`NULL`) ; dans un pivot, `required` gagne (`NOT NULL`).

La documentation `types-forge-mariadb.md` documente partiellement l'écart (cas 2), mais
`entity-schema.md` dit `nullable: défaut true` ce qui contredit le comportement réel.

Aucune correction n'est apportée dans ce ticket.

---

## 2. Contexte

La limite avait été notée pendant la roadmap JSON Schema :

> `fields[]` d'entité et `pivot.fields[]` ne semblent pas avoir exactement le même
> comportement `nullable` par défaut.

L'audit NULLABLE-CONTRACT-001 précise et quantifie cette ambiguïté.

---

## 3. Méthode d'audit

Fichiers lus directement :

```
schemas/field.schema.json
schemas/pivot.schema.json
forge_cli/entities/canonical_model_normalizer.py  — _normalize_field()
forge_cli/entities/relations.py                   — _validate_canonical_pivot_fields()
forge_cli/entities/make_entity.py                 — build_entity_sql()
docs/entities/entity-schema.md
docs/entities/types-forge-mariadb.md
docs/entities/limites-contrats-json.md
docs/entities/pivots-many-to-many.md
tests/test_build_model_canonical_normalizer.py
tests/test_pivot_fields_controlled.py
```

Vérification de l'identité des deux copies de `field.schema.json` :

```bash
diff schemas/field.schema.json forge_cli/schemas/field.schema.json
# → IDENTICAL
```

---

## 4. Ce que déclarent les schémas

### `field.schema.json`

```json
"nullable": {
  "description": "La colonne SQL accepte-t-elle NULL ?",
  "type": "boolean",
  "default": true
},
"required": {
  "description": "Le champ est-il obligatoire côté formulaire ?",
  "type": "boolean",
  "default": false
}
```

**Déclaration** : `nullable` absent = `true` (NULL par défaut).

**Le même `field.schema.json` est utilisé pour `fields[]` et `pivot.fields[]`** :
`pivot.schema.json` référence `field.schema.json` via `"$ref": "field.schema.json"`.

### `pivot.schema.json`

```json
"fields": {
  "type": "array",
  "items": { "$ref": "field.schema.json" }
}
```

Les deux contextes partagent le même schéma de champ. Pas de surcharge de défaut dans `pivot.schema.json`.

---

## 5. Comportement `fields[]` d'entité

Source : `canonical_model_normalizer.py::_normalize_field()` (ligne 111-113)

```python
nullable = bool(field.get("nullable", False))          # défaut False → NOT NULL
if field.get("required") and not field.get("nullable"):
    nullable = False
```

| Cas | `nullable` calculé | SQL généré |
|---|---|---|
| absent (ni `nullable` ni `required`) | `False` | `NOT NULL` |
| `nullable: true` | `True` | `NULL` |
| `nullable: false` | `False` | `NOT NULL` |
| `required: true` (sans `nullable`) | `False` | `NOT NULL` |
| `required: false` (sans `nullable`) | `False` | `NOT NULL` |
| `required: true + nullable: true` | `True` (**`nullable` gagne**) | `NULL` |
| `required: true + nullable: false` | `False` | `NOT NULL` |

**Anomalie** : le défaut implicite est `False` (NOT NULL), en contradiction avec
`field.schema.json` qui déclare `default: true`.

**Anomalie secondaire** : `required: true + nullable: true` → `NULL` dans une entité.
Le `required` ne peut pas écraser un `nullable: true` explicite. La condition
`not field.get("nullable")` est `False` si `nullable` est `True`, donc l'écrasement ne s'applique pas.

---

## 6. Comportement `pivot.fields[]`

Source : `relations.py::_validate_canonical_pivot_fields()` (lignes 388-390)

```python
nullable = bool(field.get("nullable", True))           # défaut True → NULL
if field.get("required") is True:
    nullable = False                                   # required écrase toujours
```

| Cas | `nullable` calculé | SQL généré |
|---|---|---|
| absent (ni `nullable` ni `required`) | `True` | `NULL` |
| `nullable: true` | `True` | `NULL` |
| `nullable: false` | `False` | `NOT NULL` |
| `required: true` (sans `nullable`) | `False` | `NOT NULL` |
| `required: false` (sans `nullable`) | `True` | `NULL` |
| `required: true + nullable: true` | `False` (**`required` gagne**) | `NOT NULL` |
| `required: true + nullable: false` | `False` | `NOT NULL` |

**Comportement cohérent avec `field.schema.json`** sur le défaut (`True` = NULL).

**Anomalie** : `required: true + nullable: true` → `NOT NULL` dans un pivot.
Le `required` écrase inconditionnellement `nullable`.

---

## 7. Matrice comparative

| Cas | `fields[]` entité | `pivot.fields[]` | Cohérence |
|---|---|---|---|
| absent (ni `nullable` ni `required`) | NOT NULL | NULL | **Incohérent** (schéma dit NULL) |
| `nullable: true` | NULL | NULL | OK |
| `nullable: false` | NOT NULL | NOT NULL | OK |
| `required: true` (sans `nullable`) | NOT NULL | NOT NULL | OK |
| `required: false` (sans `nullable`) | NOT NULL | NULL | **Incohérent** |
| `required: true + nullable: true` | NULL (`nullable` gagne) | NOT NULL (`required` gagne) | **Incohérent** |
| `required: true + nullable: false` | NOT NULL | NOT NULL | OK |

**3 cas incohérents sur 7.**

---

## 8. Documentation existante

| Page | État |
|---|---|
| `entity-schema.md` ligne 90 | **Inexacte** : dit `nullable: défaut true` — contredit le comportement réel des entités (défaut `False`) |
| `types-forge-mariadb.md` lignes 95-98 | **Correcte** : documente `rien (entity fields[]) → NOT NULL` et `rien (pivot fields[]) → NULL` |
| `limites-contrats-json.md` ligne 115 | **Partielle** : mentionne l'écart sans détailler les valeurs ni le cas `required+nullable` |
| `pivots-many-to-many.md` ligne 130 | **Incomplète** : dit "les clés optionnelles fonctionnent de la même façon" — inexact pour `required+nullable` |

---

## 9. Risques de correction

| Risque | Sévérité | Détail |
|---|---|---|
| Modifier le défaut entités `False` → `True` | Haute | Change le SQL généré pour tous les champs sans `nullable` — rupture pour les projets existants |
| Modifier le défaut pivot `True` → `False` | Haute | Casse les tables pivot existantes sans `nullable: false` |
| Harmoniser `required + nullable` | Moyenne | Choix non trivial : `required` = contrainte formulaire, `nullable` = contrainte SQL |
| Corriger `entity-schema.md` | Faible | Documentation uniquement, pas de rupture runtime |

---

## 10. Options étudiées

### Option A — Documenter et conserver (recommandée à court terme)

Conserver le comportement actuel. Compléter la documentation pour que les deux écarts
(défaut + conflit `required+nullable`) soient explicitement documentés.

**Avantages** : aucune rupture, correction documentaire uniquement.
**Inconvénients** : contrat moins intuitif ; `entity-schema.md` reste à corriger.

---

### Option B — Harmoniser vers `nullable: true` par défaut partout

Modifier `canonical_model_normalizer.py` pour utiliser `field.get("nullable", True)`.

**Avantages** : cohérent avec `field.schema.json` ; comportement identique entité/pivot pour le cas absent.
**Inconvénients** : change le SQL généré pour tous les champs d'entité sans `nullable` explicite —
rupture potentielle pour projets existants ; les 55 fichiers de tests legacy utilisent `nullable: False`
dans les fixtures, mais les tests sur les entités canoniques pourraient être impactés.

---

### Option C — Harmoniser vers `NOT NULL` par défaut partout

Modifier `relations.py` pour utiliser `field.get("nullable", False)` dans les pivots.

**Avantages** : comportement strict et prévisible.
**Inconvénients** : contredit `field.schema.json` (`default: true`) ; casse les pivots existants
sans `nullable: false` explicite.

---

### Option D — `required` prioritaire sur `nullable`

Définir la règle : `required: true` écrase toujours `nullable`, quelle que soit la valeur.
Aligner le comportement entité sur le pivot.

**Avantages** : règle lisible (`required` = SQL NOT NULL) ; cohérent avec le pivot actuel.
**Inconvénients** : change le comportement des entités pour `required: true + nullable: true` ;
potentiellement contre-intuitif (un champ `nullable: true` pourrait devenir NOT NULL).

---

## 11. Recommandation

**Ne pas corriger dans ce ticket.**

À court terme : **Option A** — documenter précisément les trois incohérences dans la
documentation existante, notamment corriger `entity-schema.md` (dit `défaut: true`
alors que le comportement réel est `NOT NULL` pour les entités).

À moyen terme : **créer NULLABLE-CONTRACT-002** pour décider la règle officielle et
l'appliquer de façon contrôlée, avec tests de non-régression.

La décision sur l'Option B ou D modifie le SQL généré — elle doit être traitée comme
un changement comportemental dans un ticket dédié, pas comme une correction documentaire.

---

## 12. Prochains tickets proposés

| Ticket | Objectif | Statut |
|---|---|---|
| `NULLABLE-CONTRACT-002` | Décider et appliquer la règle officielle `nullable` (défaut + `required` vs `nullable`) | **Livré** |
| `NULLABLE-DOC-FIX-001` | Corriger la documentation utilisateur | **Livré** |
| `NULLABLE-CONTRACT-003` | Appliquer la règle officielle dans `canonical_model_normalizer.py` + tests | **Livré** |

---

## 14. Correction runtime

`NULLABLE-CONTRACT-003` aligne le normaliseur d'entité sur ADR-013 :
`nullable` par défaut (`True`), `required` prioritaire.

Fichier corrigé : `forge_cli/entities/canonical_model_normalizer.py::_normalize_field()`.
Test mis à jour : `test_default_nullable_is_false` → `test_default_nullable_is_true`.
3 nouveaux tests de matrice ADR-013 ajoutés.

---

## 15. Correction documentaire

`NULLABLE-DOC-FIX-001` aligne la documentation utilisateur avec ADR-013 et le runtime
corrigé par NULLABLE-CONTRACT-003.

Pages mises à jour : `types-forge-mariadb.md` (table + note divergence → règle ADR-013),
`limites-contrats-json.md` (limite divergence → règle uniforme), `pivots-many-to-many.md`
(règle pivot.fields[] explicitée).

`entity-schema.md` était déjà exact (`nullable: défaut true`).

---

## 13. Décision post-audit

**Décision** : champ nullable par défaut, `required` prioritaire.

Règle officielle : absent → NULL ; `required: true` → NOT NULL ; `nullable` explicite → respecté sauf si `required: true`.

Voir **ADR-013 — Politique nullable / required dans les contrats JSON Forge** :
`docs/adr/013-nullable-required-contract-policy.md`

---

## 16. Clôture du bloc nullable / required

**Statut : terminé.**

Le bloc nullable / required est clôturé après livraison de :

- `NULLABLE-CONTRACT-001` — audit des incohérences ;
- `NULLABLE-CONTRACT-002` — décision ADR-013 ;
- `NULLABLE-CONTRACT-003` — alignement runtime (`canonical_model_normalizer.py`) ;
- `NULLABLE-DOC-FIX-001` — documentation utilisateur alignée.

**Règle officielle** : nullable par défaut, `required` prioritaire.

`fields[]` d'entité et `pivot.fields[]` suivent désormais la même règle (ADR-013).

| Élément | Statut |
|---|---|
| Audit | Livré — NULLABLE-CONTRACT-001 |
| Décision | Livrée — ADR-013 (NULLABLE-CONTRACT-002) |
| Runtime | Aligné — NULLABLE-CONTRACT-003 |
| Documentation utilisateur | Alignée — NULLABLE-DOC-FIX-001 |
| Schémas JSON | Non modifiés (conformes à la règle) |
| Starters | Non modifiés (explicitement annotés) |
| PyPI | Aucune publication |