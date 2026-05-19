# Audit/décision — ENTITY-SCHEMA-RBAC-001
## rbac dans le schéma canonique : décision de non-intégration

**Date** : 2026-05-19
**Ticket** : ENTITY-SCHEMA-RBAC-001
**Statut** : Décision rendue — Option A retenue

---

## 1. Contexte

Le ticket LEGACY-STRICT-SCHEMA-001 (cc23b73) a révélé une asymétrie explicite :
l'attribut `rbac` est accepté dans le format interne (`validation.py:ALLOWED_ROOT_KEYS`)
mais absent du schéma canonique (`entity.schema.json`, `additionalProperties: false`).

Ce document audite les usages de `rbac` dans le projet et décide si `rbac` doit
devenir une propriété officielle du schéma canonique.

---

## 2. Audit des usages

### 2.1 Format interne — validation.py

| Fichier | Ligne | Usage | Type |
|---|---|---|---|
| `forge_cli/entities/validation.py` | 55 | `ALLOWED_ROOT_KEYS` inclut `"rbac"` | Acceptation |
| `forge_cli/entities/validation.py` | 56 | `ALLOWED_RBAC_ACTION_KEYS` défini | Validation des actions |
| `forge_cli/entities/validation.py` | 252–280 | `_validate_rbac_structure()` | Validation structure |
| `forge_cli/entities/validation.py` | 426–437 | `normalize_entity_definition()` — preserve `rbac` | Normalisation |

**Conclusion** : le format interne valide et normalise `rbac`. Structure attendue :
```json
{
  "rbac": {
    "permissions": {
      "index": "articles.view",
      "create": "articles.create",
      "edit": "articles.edit",
      "update": "articles.update",
      "delete": "articles.delete"
    }
  }
}
```

### 2.2 Générateurs — make:crud

| Fichier | Ligne | Usage | Type |
|---|---|---|---|
| `forge_cli/entities/make_crud.py` | 242 | `definition.get("rbac")` | Lecture |
| `forge_cli/entities/make_crud.py` | 246–266 | Propagation aux builders | Passage en paramètre |
| `forge_cli/entities/crud/controller_builder.py` | 60–76 | `@require_permission` conditionnel | Génération |
| `forge_cli/entities/crud/views_builder.py` | — | Guards `{% if can() %}` | Génération |

**Conclusion** : `rbac` est lu depuis la définition interne et propagé à tous les
builders. Absence de `rbac` → pas de guards (rétrocompatibilité garantie).

### 2.3 Schéma canonique — entity.schema.json

```
Propriétés : $schema, schema_version, name, table, label, plural_label,
             description, fields, indexes, options
additionalProperties: false
```

**`rbac` est absent** : une entité canonique avec `rbac` est **rejetée** par le
validateur JSON Schema avant même d'atteindre le normalisation.

### 2.4 Normaliseur canonique — canonical_model_normalizer.py

`normalize_canonical_entity_for_model_build()` ne préserve pas `rbac` ni `media`
ni `list.filter`. Ces attributs sont silencieusement ignorés lors de la conversion
canonique → interne.

**Conséquence** : même si un utilisateur parvenait à ajouter `rbac` à une entité
canonique, l'attribut serait perdu lors de la normalisation. Les guards ne seraient
pas générés.

### 2.5 Tests actifs

| Fichier | Tests | Format utilisé |
|---|---|---|
| `tests/test_make_crud_rbac.py` | 34 passent | Format interne (`entity` key) |
| `tests/test_crud_rbac_ui.py` | 22 passent | Format interne (`entity` key) |
| `tests/test_security_rbac_audit.py` | — | Format interne |

**Tous les tests RBAC utilisent le format interne**, pas le format canonique.
Aucun test ne tente d'utiliser `rbac` dans une entité `schema_version: "1.0"`.

### 2.6 Documentation

`docs/rbac.md`, `docs/security.md` documentent le module `forge-mvc-rbac` comme
brique opt-in. Aucune documentation ne mentionne l'attribut `rbac` dans les entités
JSON canoniques.

---

## 3. Analyse des options

### Option A — Ne pas intégrer (statu quo documenté)

`rbac` reste dans le format interne uniquement. L'asymétrie est documentée comme
intentionnelle. Les utilisateurs qui veulent des guards RBAC dans `make:crud`
doivent écrire leurs entités au format interne ou attendre un ticket dédié.

**Avantages** :
- Zéro modification de code ou de schéma
- Séparation claire : schéma canonique = contrat de données, format interne = pipeline CLI
- Aucun risque de régression

**Inconvénients** :
- Friction utilisateur : impossible d'utiliser `rbac` depuis le format canonique
- Double format (interne vs canonique) pour RBAC

### Option B — Intégrer `rbac` dans entity.schema.json

Ajouter `rbac` comme propriété officielle du schéma canonique et mettre à jour
le normalisation pour le préserver.

**Requis** :
- Modifier `schemas/entity.schema.json` (ajouter `rbac` avec sa structure)
- Modifier `forge_cli/entities/canonical_model_normalizer.py` (préserver `rbac`)
- Modifier `forge_cli/entities/entity_validate.py` si nécessaire
- Écrire des tests canoniques pour `rbac`
- Garantir la rétrocompatibilité (entités sans `rbac` → pas de guards)

**Avantages** :
- Expérience utilisateur unifiée
- `rbac` devient un contrat officiel documenté
- Cohérence schéma canonique ↔ génération

**Inconvénients** :
- Périmètre important (3+ fichiers, nouveaux tests)
- Ce ticket est décision-only : modifications interdites

### Option C — Zone d'extensions dans le schéma

Ajouter une zone `extensions` permissive pour des attributs opt-in comme `rbac`
et `media`. La zone serait validée séparément.

**Verdict** : introduit une meta-structure complexe. Option B est plus directe.

### Option D — Fichier séparé par entité

Fichier `article.rbac.json` à côté de `article.json`.

**Verdict** : fragmente la configuration, complique `make:crud`. Rejeté.

---

## 4. Décision — Option A retenue

**rbac ne sera PAS intégré dans `entity.schema.json` dans ce ticket.**

**Justification** :

1. **Double rupture actuelle** : le schéma canonique rejette `rbac`
   (`additionalProperties: false`) ET le normalisation le supprime. L'intégration
   canonique nécessite de corriger les deux, ce qui dépasse le périmètre de ce ticket.

2. **Pipeline de travail distinct** : les tests RBAC utilisent tous le format interne.
   Le format interne fonctionne et est stable. Aucun utilisateur réel n'essaie d'écrire
   `rbac` dans un fichier `schema_version: "1.0"` aujourd'hui.

3. **Principe 2 — petits tickets** : définir où vit la configuration RBAC mérite
   un ticket dédié (RBAC-CONTRACT-001). Ce ticket doit décider de l'emplacement
   séparé, pas intégrer `rbac` dans `entity.schema.json`.

4. **Séparation sémantique saine** : le schéma canonique décrit la structure de données
   (tables, champs, index, options). `rbac` décrit des règles d'autorisation applicatives.
   Ces deux préoccupations peuvent légitimement vivre dans des formats différents.

---

## 5. État final après ENTITY-SCHEMA-RBAC-001

| Élément | État | Note |
|---|---|---|
| `schemas/entity.schema.json` | Inchangé | `rbac` absent, `additionalProperties: false` |
| `forge_cli/entities/validation.py` | Inchangé | `rbac` dans `ALLOWED_ROOT_KEYS` |
| `forge_cli/entities/canonical_model_normalizer.py` | Inchangé | Ne préserve pas `rbac` |
| `forge_cli/entities/make_crud.py` | Inchangé | Lit `rbac` depuis la définition interne |
| Tests RBAC | 56 passent | Format interne |
| Documentation | Inchangée | Aucune mention de `rbac` dans l'entity schema |

---

## 6. Ticket suivant recommandé

**RBAC-CONTRACT-001** — Définir un contrat RBAC séparé du schéma d'entité.

Objectif : décider où vit la configuration RBAC (emplacement, format, structure)
sans toucher à `entity.schema.json`. L'emplacement recommandé est
`mvc/security/rbac.json` (contrat séparé, fichier dédié).

Prérequis : ENTITY-SCHEMA-RBAC-001 livré (ce document).

**Note** : le ticket suivant N'est PAS une intégration dans `entity.schema.json`.
La décision Option A est ferme : `rbac` hors du schéma d'entité.

---

## 7. Traces intentionnelles restantes

| Fichier | Trace | Justification |
|---|---|---|
| `forge_cli/entities/validation.py` | `ALLOWED_ROOT_KEYS` inclut `rbac` | Pipeline interne actif et stable |
| `forge_cli/entities/make_crud.py` | `definition.get("rbac")` | Lecture depuis format interne |
| `forge_cli/entities/crud/controller_builder.py` | Guards `@require_permission` | Génération conditionnelle |
| `forge_cli/entities/crud/views_builder.py` | Guards `{% if can() %}` | Génération conditionnelle |
| `tests/test_make_crud_rbac.py` | 34 tests format interne | Garde-fous actifs |
| `tests/test_crud_rbac_ui.py` | 22 tests format interne | Garde-fous actifs |
