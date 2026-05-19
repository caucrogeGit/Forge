# Audit — Warnings legacy dans make:crud et make:relation

**Ticket** : LEGACY-WARNINGS-003-AUDIT-MAKECRUD-MAKERELATION-WARNINGS
**Date** : 2026-05-19
**Auteur** : Forge (audit pré-implémentation)
**Périmètre** : `forge_cli/entities/make_crud.py`, `forge_cli/entities/make_relation.py`,
`forge_cli/entities/relations.py`

---

## 1. Résumé

L'audit identifie deux commandes candidates à un warning legacy :

- **`make:crud`** : charge directement l'entité via un chemin identique à `build:model` ;
  le point d'insertion est propre et n'affecte aucune fonction partagée.
  L'infrastructure de warnings (`MakeCrudResult.warnings`) est déjà en place.

- **`make:relation`** : lit `relations.json` (legacy ou canonique) mais écrit toujours
  en canonique (`schema_version: "1.0"`). Un warning legacy dans `relations.json` est
  pertinent mais moins critique — la commande corrige le format automatiquement lors de
  l'écriture.

**Recommandation** : ajouter le warning dans **`make:crud` uniquement** (LEGACY-WARNINGS-004).
Différer `make:relation` à un ticket ultérieur ou considérer la conversion automatique
comme suffisante.

Aucun warning runtime n'est ajouté dans ce ticket.

---

## 2. Contexte

`build:model` émet désormais `[WARN]` pour chaque entité `format_version: 1` via
`BuildModelResult.legacy_warnings` (LEGACY-WARNINGS-002).

Les autres commandes (`make:crud`, `make:relation`, migrations) restent sans warning.
Ce ticket décide si `make:crud` et `make:relation` doivent être étendus.

---

## 3. Méthode d'audit

Fichiers audités directement :

```
forge_cli/entities/make_crud.py
forge_cli/entities/make_relation.py
forge_cli/entities/relations.py  — load_entity_definitions()
forge_cli/entities/model.py      — référence pour le mécanisme LEGACY-WARNINGS-002
```

Commande grep ciblée :

```bash
grep -n 'format_version|schema_version|legacy|normalize_canonical|validate_entity_definition|warning' \
  forge_cli/entities/make_crud.py forge_cli/entities/make_relation.py forge_cli/entities/relations.py
```

---

## 4. make:crud

### 4.1 Chemin de chargement

`make_crud()` — `forge_cli/entities/make_crud.py`, lignes 168-175 :

```python
raw = json.loads(json_path.read_text(encoding="utf-8"))
if isinstance(raw, dict) and raw.get("schema_version") == "1.0":
    raw = normalize_canonical_entity_for_model_build(raw)
definition = validate_entity_definition(raw, source=str(json_path))
```

Le `if` normalise les entités canoniques. Les entités legacy passent directement
à `validate_entity_definition()` sans branche `else` explicite.

| Question | Réponse |
|---|---|
| Charge l'entité directement ? | **Oui** — lit `mvc/entities/<snake>/<snake>.json` |
| Utilise `validate_entity_definition()` ? | **Oui** |
| Passe par `normalize_canonical_entity_for_model_build()` ? | Seulement pour le canonique |
| Détecte `schema_version: "1.0"` ? | **Oui** — branche `if` explicite |
| Accepte `format_version: 1` ? | **Oui** — silencieusement (branche implicite) |

### 4.2 Infrastructure de warnings existante

`MakeCrudResult.warnings: list[str]` est déjà présent.
`cmd_make_crud_main()` l'affiche via `out.warn()` :

```python
for warn in result.warnings:
    print(out.warn(warn))
```

### 4.3 Point d'insertion possible

Dans `make_crud()`, transformer le `if` implicite en `if / else` :

```python
raw = json.loads(json_path.read_text(encoding="utf-8"))
if isinstance(raw, dict) and raw.get("schema_version") == "1.0":
    raw = normalize_canonical_entity_for_model_build(raw)
else:
    result.warnings.append(
        f'Entité legacy : {entity_name}. '
        'format_version: 1 est déprécié — utilisez schema_version: "1.0". '
        "Guide : docs/entities/migration-legacy-vers-canonique.md"
    )
definition = validate_entity_definition(raw, source=str(json_path))
```

**Problème d'ordre** : `result` est instancié à la ligne 184, **après** le chargement
de l'entité (lignes 168-175). L'insertion directe dans `result.warnings` n'est pas
possible sans déplacer l'instanciation ou utiliser une variable intermédiaire.

**Solution** : collecter le warning dans une variable locale et l'ajouter à `result`
après instanciation.

### 4.4 Risque de bruit

**Faible** — `make:crud` est une commande explicitement humaine. Les warnings CRUD
(champ sans métier, form builder) sont déjà affichés. Un warning legacy s'intègre
naturellement.

Les tests `make:crud` vérifient le contenu des fichiers générés, pas la sortie stdout
brute. Le warning n'affecte pas les assertions.

---

## 5. make:relation

### 5.1 Chargement de `relations.json`

`_load_relations_document()` — lignes 118-137 :

```python
if "schema_version" not in data and "format_version" not in data:
    raise ValueError(...)
return data    # accepte format_version OU schema_version
```

`_load_relations_document()` **accepte** un `relations.json` avec `format_version: 1`.

### 5.2 Écriture toujours canonique

Après le dialogue interactif, `main()` construit :

```python
candidate = {
    "schema_version": "1.0",
    "relations": [*document["relations"], relation],
}
```

Peu importe le format d'entrée, `make:relation` écrit toujours un fichier canonique.
**Un `relations.json` legacy est automatiquement upgradé par `make:relation`.**

| Question | Réponse |
|---|---|
| Lit `relations.json` legacy ? | **Oui** |
| Écrit en canonique ? | **Oui — toujours** |
| Le format d'entrée est signalé ? | Non |
| Le warning serait redondant ? | **En partie** — la conversion est automatique |

### 5.3 Chargement des entités

`make:relation` charge les entités via `load_entity_definitions()` dans `relations.py`
(ligne 307, `main()`). Cette fonction est **partagée** avec `build:model`,
`validate_relations_definition()`, et `_safe_load_entities()`.

Ajouter un warning dans `load_entity_definitions()` serait l'**Option D** (fonction
partagée) — à risque élevé de propagation non voulue.

### 5.4 Point d'insertion possible pour `relations.json`

Dans `main()`, après `_load_relations_document()`, si le document chargé contient
`format_version` et pas `schema_version` :

```python
document = _load_relations_document(relations_path)
if "format_version" in document and "schema_version" not in document:
    print("[WARN] relations.json en format legacy. "
          "Il sera converti en schema_version: \"1.0\" lors de l'écriture.")
```

**Risque** : `make:relation` est un outil interactif avec dialogue de confirmation.
Un warning en amont du dialogue est peu intrusif. Mais la conversion étant automatique,
la valeur ajoutée est limitée.

---

## 6. Risques de bruit

| Commande | Risque | Détail |
|---|---|---|
| `make:crud` | **Faible** | Commande humaine, infrastructure warnings existante, tests ne vérifient pas stdout |
| `make:relation` — entités | **Élevé** | `load_entity_definitions()` partagée — toucher cette fonction propagerait le warning à d'autres commandes |
| `make:relation` — `relations.json` | **Faible** | Point d'insertion isolé dans `main()`, mais valeur ajoutée limitée (conversion automatique) |

---

## 7. Options étudiées

### Option A — Aucune extension des warnings

Laisser `make:crud` et `make:relation` sans warning.

**Avantages** : aucune modification, aucun risque de bruit.

**Inconvénients** : un utilisateur qui ne lance jamais `build:model` (ex. : flux
`make:crud` seul) ne voit pas la dépréciation.

---

### Option B — Warning dans `make:crud` uniquement

Ajouter un warning legacy dans `make_crud()` via `MakeCrudResult.warnings`.

**Avantages** : infrastructure existante, point d'insertion propre, pas de fonction
partagée touchée, risque de bruit faible.

**Inconvénients** : `make:relation` reste silencieux sur le legacy.

---

### Option C — Warning dans `make:crud` et `make:relation`

Ajouter warning dans `make_crud()` ET dans `main()` de `make:relation` (pour
`relations.json` legacy uniquement, pas via `load_entity_definitions()`).

**Avantages** : couverture plus large.

**Inconvénients** : `make:relation` a déjà une conversion automatique — le warning
peut sembler superflu ou confus pour l'utilisateur.

---

### Option D — Warning via fonction partagée (`load_entity_definitions`)

Ajouter le warning dans `relations.py::load_entity_definitions()`.

**Avantages** : une seule modification pour toutes les commandes qui chargent des entités.

**Inconvénients** : propagation à toutes les commandes utilisant `load_entity_definitions()`
— dont `validate_relations_definition()` et le validateur des relations. Contraire à la
règle d'arrêt du ticket.

---

## 8. Recommandation

**Option B — Warning dans `make:crud` uniquement.**

**Justification :**

1. `make:crud` est l'autre commande principale qui consomme directement une entité legacy —
   c'est là que l'utilisateur voit le résultat d'un contrat déprécié.
2. L'infrastructure `MakeCrudResult.warnings` + `out.warn()` est déjà en place.
3. Le point d'insertion ne touche pas de fonction partagée.
4. `make:relation` convertit automatiquement en canonique — le warning serait redondant.
   Si le besoin est avéré, un ticket dédié pourra traiter ce cas.
5. `load_entity_definitions()` reste intacte — aucun risque de propagation.

**Ce que ce warning ne fait pas :**

- Il ne bloque pas la génération.
- Il ne modifie pas les fichiers générés.
- Il n'affecte pas `make:relation`, les migrations ni `entity:validate`.

**Ticket suivant :** LEGACY-WARNINGS-004 — implémenter le warning dans `make:crud`.

---

## 9. Tickets futurs proposés

| Ticket | Objectif | Statut |
|---|---|---|
| `LEGACY-WARNINGS-004` | Implémenter warning non bloquant dans `make:crud` | **Livré** |
| `LEGACY-WARNINGS-005` | Décider si `make:relation` doit avertir sur `relations.json` legacy | À créer après LEGACY-WARNINGS-004 |
| `LEGACY-TESTS-RECLASSIFY-001` | Reclasser les 75 tests legacy comme `pytest.mark.legacy` | À créer |

---

## 10. Mise en œuvre

`LEGACY-WARNINGS-004` ajoute un warning humain non bloquant dans `make:crud` lorsqu'une
entité `format_version: 1` est utilisée.

Mécanisme : variable locale `is_legacy` dans `make_crud()`, message inséré dans
`MakeCrudResult.warnings` après instanciation du résultat. Affiché via `out.warn()`
dans `cmd_make_crud_main()`.

`make:relation` reste volontairement sans warning.
