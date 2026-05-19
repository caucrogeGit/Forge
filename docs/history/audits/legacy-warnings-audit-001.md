# Audit — Warnings legacy dans Forge

**Ticket** : LEGACY-WARNINGS-001-AUDIT-LEGACY-WARNINGS
**Date** : 2026-05-19
**Auteur** : Forge (audit pré-implémentation)
**Périmètre** : `forge_cli/entities/`, `forge_cli/starters/`, `tests/`

---

## 1. Résumé

Le format legacy (`format_version: 1`) est officiellement déprécié par ADR-012,
mais Forge l'accepte encore silencieusement dans toutes ses commandes de génération.

L'audit identifie **5 points d'entrée legacy actifs**, les commandes candidates à un
avertissement, et analyse les risques de bruit pour chaque option.

**Recommandation** : warning humain non bloquant dans `build:model` uniquement,
au moment où un fichier legacy est effectivement chargé. Les autres commandes
pourront être traitées ensuite dans LEGACY-WARNINGS-002.

Aucun warning runtime n'est ajouté dans ce ticket.

---

## 2. Contexte

ADR-012 (`docs/adr/012-legacy-format-deprecation-policy.md`) officialise la
dépréciation du format legacy. Le format canonique (`schema_version: "1.0"`) est
le seul format officiel. Les starters sont 100 % canoniques. Un guide de migration
est disponible (`docs/entities/migration-legacy-vers-canonique.md`).

La question ouverte : faut-il avertir l'utilisateur quand Forge rencontre un
fichier `format_version: 1` ?

---

## 3. Méthode d'audit

Fichiers audités directement :

```
forge_cli/entities/model.py
forge_cli/entities/relations.py
forge_cli/entities/make_crud.py
forge_cli/entities/make_entity.py
forge_cli/entities/make_relation.py
forge_cli/entities/migrations.py
forge_cli/entities/validation.py
forge_cli/entities/entity_validate.py
forge_cli/starters/builder.py
forge_cli/starters/scaffold.py
forge_cli/output.py
```

Commande grep :

```bash
grep -RInE 'format_version|legacy|canonical_model_normalizer|schema_version' forge_cli/
```

Comptage des tests utilisant `format_version` :

```bash
find tests/ -name "*.py" | xargs grep -l 'format_version' | wc -l
# → 75
```

---

## 4. Chemins legacy concernés

### 4.1 `forge_cli/entities/model.py` — `build_model()` et `_load_entity_sources()`

**Commande** : `build:model`

Deux chemins de lecture dans la même boucle :

```python
# _load_entity_sources() — lignes 334-338
if isinstance(raw_data, dict) and raw_data.get("schema_version") == "1.0":
    legacy_data = normalize_canonical_entity_for_model_build(raw_data)
    definition = validate_entity_definition(legacy_data, ...)
else:
    definition = validate_entity_definition(raw_data, ...)   # ← legacy silencieux
```

Le `else` accepte silencieusement un fichier `format_version: 1` et le passe
directement à `validate_entity_definition()`.

**Endroit possible pour un warning** : dans le `else`, avant l'appel à
`validate_entity_definition()`, émettre un `[WARN]` sur stdout.

**Risque** : faible — `build:model` est une commande humaine interactive.

---

### 4.2 `forge_cli/entities/relations.py` — `_load_relation_sources()`

**Commande** : `build:model` (via la boucle des fichiers `relations.json`)

```python
# lignes 159-163
if isinstance(raw_data, dict) and raw_data.get("schema_version") == "1.0":
    legacy_data = normalize_canonical_entity_for_model_build(raw_data)
    data = validate_entity_definition(legacy_data, ...)
else:
    data = validate_entity_definition(raw_data, ...)         # ← legacy silencieux
```

Même pattern que `model.py`. Un `relations.json` avec `format_version: 1` est
aussi accepté silencieusement.

**Endroit possible pour un warning** : dans le `else` de la même boucle.

**Risque** : faible à moyen — le warning peut apparaître plusieurs fois si plusieurs
relations sont dans le fichier.

---

### 4.3 `forge_cli/entities/make_crud.py` — `make_crud()`

**Commande** : `make:crud`

```python
# lignes 169-172
raw = json.loads(json_path.read_text(encoding="utf-8"))
if isinstance(raw, dict) and raw.get("schema_version") == "1.0":
    raw = normalize_canonical_entity_for_model_build(raw)
definition = validate_entity_definition(raw, ...)            # ← legacy silencieux si pas de schema_version
```

Un fichier sans `schema_version` (legacy) passe directement.

**Endroit possible pour un warning** : après le `if`, dans un `else` explicite.

**Risque** : moyen — `make:crud` est souvent lancé manuellement, mais les warnings
CRUD peuvent déjà être nombreux (formulaire vide, etc.).

---

### 4.4 `forge_cli/entities/migrations.py` — `_load_entity_for_migration()`

**Commandes** : `migration:diff`, `migration:make --from-diff`

```python
# lignes 351-353
if isinstance(data, dict) and data.get("schema_version") == "1.0":
    data = normalize_canonical_entity_for_model_build(data)
return validate_entity_definition(data, ...)                 # ← legacy silencieux
```

**Endroit possible pour un warning** : dans un `else` après le `if`.

**Risque** : moyen — les migrations sont souvent scriptées en CI. Un warning
inattendu peut bruiter les logs de migration.

---

### 4.5 `forge_cli/entities/make_relation.py` — `_load_relations_json()`

**Commande** : `make:relation`

```python
# lignes 135-136
if "schema_version" not in data and "format_version" not in data:
    raise ValueError(...)
```

`make:relation` détecte déjà la présence de `format_version` pour accepter le
fichier, mais n'émet pas de warning.

**Endroit possible pour un warning** : après la détection, si `format_version` est
présent et `schema_version` absent.

**Risque** : faible — `make:relation` est interactif.

---

### 4.6 `forge_cli/entities/entity_validate.py` — `collect_entity_validation_results()`

**Commande** : `entity:validate`

```python
# ligne 307
if not isinstance(data, dict) or data.get("schema_version") != "1.0":
    continue   # ← les entités legacy sont IGNORÉES silencieusement
```

`entity:validate` **saute** les entités legacy sans avertissement. Un utilisateur
qui lance `entity:validate` sur un projet legacy obtient « 0 fichier vérifié »
sans explication.

**Endroit possible pour un warning** : dans la boucle, quand un fichier legacy est
détecté et sauté.

**Risque** : élevé à court terme — `entity:validate` est présenté comme l'outil
officiel de validation. Y ajouter un warning legacy mélange deux responsabilités
(validation canonique + détection migration). Mieux vaut un ticket dédié.

---

## 5. Commandes candidates

| Commande | Accepte legacy ? | Warning recommandé ? | Raison |
|---|---|---|---|
| `build:model` | Oui (silencieux) | **Oui — prioritaire** | Point naturel de projection ; commande humaine ; warning visible au bon moment |
| `make:crud` | Oui (silencieux) | Oui — secondaire | Commande humaine ; warnings déjà affichés |
| `make:relation` | Oui (silencieux) | Oui — secondaire | Commande interactive |
| `migration:diff` | Oui (silencieux) | Non immédiatement | Souvent scriptée en CI — risque de bruit dans les logs |
| `migration:make` | Oui (silencieux) | Non immédiatement | Même raison que `migration:diff` |
| `entity:validate` | Non (skip silencieux) | Non direct | Mélange de responsabilités — traiter séparément |
| `make:entity` | Ne lit pas legacy | N/A | Génère toujours canonique |
| `starter:build` | Oui via `build:model` | Hérité | Le warning `build:model` couvre ce cas |

---

## 6. Risques de bruit

### 6.1 Tests

75 fichiers de tests utilisent `format_version: 1` dans leurs fixtures. Si un
warning est émis sur `stdout`, les tests capturant la sortie pourront contenir du
bruit supplémentaire, mais ne casseront pas (les assertions testent le code généré,
pas la sortie brute).

Les tests qui comparent `result.output` ou capturent `capsys.readouterr()` sont à
surveiller.

### 6.2 CI / scripts

Les commandes `migration:diff` et `migration:make` sont fréquemment intégrées dans
des pipelines CI. Un warning sur `stdout` dans ces commandes peut fausser un parsing
de sortie.

**Mitigation** : émettre le warning sur `stderr` plutôt que `stdout`, ou uniquement
dans `build:model` qui est plus rarement scripté.

### 6.3 Sortie JSON (`--json`)

Certaines commandes supportent `--json` pour une sortie machine. Ajouter un warning
humain dans ces commandes sans le conditionner à l'absence de `--json` casserait le
contrat de sortie.

`build:model` n'a pas de mode `--json` actuellement — risque nul sur ce point.

---

## 7. Options étudiées

### Option A — Aucun warning runtime

Le legacy reste supporté silencieusement. La dépréciation reste documentaire
(ADR-012, guide de migration).

**Avantages** : aucun bruit, aucun risque de casser les scripts ou les tests.

**Inconvénients** : les utilisateurs de projets anciens ne sont pas incités à migrer.
Le délai avant suppression risque de s'allonger indéfiniment.

---

### Option B — Warning humain dans `build:model` uniquement

Émettre `[WARN]` sur stdout quand `build:model` charge une entité `format_version: 1`.

```text
[WARN] Entité legacy détectée : article/article.json (format_version: 1).
       Le format canonique schema_version: "1.0" est recommandé.
       Guide de migration : docs/entities/migration-legacy-vers-canonique.md
```

**Avantages** : visible au bon moment ; ne touche pas CI ni `--json` ; pattern déjà
utilisé dans Forge (`out.warn()`).

**Inconvénients** : n'avertit pas pour `make:crud` ou les migrations.

---

### Option C — Warning contrôlé par `--strict` ou variable d'environnement

N'émettre le warning que si `FORGE_STRICT=1` ou si `--strict` est passé.

**Avantages** : silencieux par défaut ; opt-in progressif.

**Inconvénients** : moins visible ; les utilisateurs qui n'activent pas le flag ne
voient jamais la dépréciation.

---

### Option D — Clé `warnings[]` dans la sortie `--json`

Ajouter une section `warnings` dans les sorties JSON des commandes concernées.

**Avantages** : exploitable en CI sans polluer le texte humain.

**Inconvénients** : modifie le contrat de sortie JSON ; nécessite que les commandes
concernées supportent déjà `--json`.

---

## 8. Recommandation

**Option B — Warning humain dans `build:model` uniquement.**

**Justification :**

1. `build:model` est le point de projection central — c'est là que le legacy est
   effectivement utilisé pour générer du SQL.
2. Le warning est visible au moment où l'ancien contrat produit un effet concret.
3. `out.warn()` est déjà le mécanisme officiel pour les avertissements non bloquants
   dans Forge (utilisé dans `make:crud`, `deploy:check`, `doctor`).
4. `build:model` n'a pas de mode `--json` — aucun contrat de sortie à protéger.
5. L'impact sur les tests est limité : les tests qui vérifient le SQL généré ne
   comparent pas la sortie stdout brute.

**Ce que ce warning ne fait pas :**

- Il ne bloque pas la génération.
- Il ne modifie pas le format legacy accepté.
- Il n'affecte pas `entity:validate`, `make:crud`, ni les migrations.

**Ticket suivant :** LEGACY-WARNINGS-002 — implémenter le warning dans `build:model`.

---

## 9. Tickets futurs proposés

| Ticket | Objectif | Statut |
|---|---|---|
| `LEGACY-WARNINGS-002` | Implémenter le warning non bloquant dans `build:model` | **Livré** |
| `LEGACY-WARNINGS-003` | Audit make:crud / make:relation — stratégie warnings | **Livré** |
| `LEGACY-WARNINGS-004` | Warning non bloquant dans `make:crud` | **Livré** |
| `LEGACY-WARNINGS-005` | Décider si `make:relation` doit avertir sur `relations.json` legacy | À créer |
| `LEGACY-TESTS-RECLASSIFY-001` | Reclasser les 75 tests legacy comme `pytest.mark.legacy` | À créer (référencé ADR-012) |

---

## 10. Mise en œuvre partielle

`LEGACY-WARNINGS-002` ajoute un warning humain non bloquant dans `build:model` lorsqu'une
entité `format_version: 1` est chargée.

Mécanisme : `BuildModelResult.legacy_warnings` (liste de messages), affiché via `out.warn()`
dans `main()` uniquement pour la commande `build:model`.

Fichiers modifiés : `forge_cli/entities/model.py` (champ `is_legacy` sur `EntitySource`,
champ `legacy_warnings` sur `BuildModelResult`, collecte dans `build_model()`, affichage
dans `main()`).

Les autres commandes (`make:crud`, `make:relation`, migrations) restent hors périmètre.

---

## 11. Clôture du bloc warnings legacy

**Statut : terminé.**

Le bloc warnings legacy est clôturé après livraison de :

- `LEGACY-WARNINGS-001` — audit stratégie warnings legacy ;
- `LEGACY-WARNINGS-002` — warning non bloquant dans `build:model` ;
- `LEGACY-WARNINGS-003` — audit `make:crud` / `make:relation` ;
- `LEGACY-WARNINGS-004` — warning non bloquant dans `make:crud`.

**État final des warnings legacy :**

| Commande | Statut |
|---|---|
| `build:model` | Warning actif — `[WARN]` par entité `format_version: 1` chargée |
| `make:crud` | Warning actif — `[WARN]` par entité `format_version: 1` utilisée |
| `make:relation` | Pas de warning — conversion canonique automatique considérée suffisante |
| Migrations | Pas de warning — risque de bruit CI ; traitement différé |
| `entity:validate` | Pas de warning legacy — centré sur le format canonique (`schema_version: "1.0"`) |

**Propriétés des warnings :**

- Non bloquants — la génération se poursuit normalement.
- Sorties humaines uniquement — aucun warning n'est ajouté aux sorties JSON.
- Un warning par entité — pas de duplication dans une même exécution.

**Ce qui reste inchangé :**

- Le support legacy (`format_version: 1`) reste présent.
- Aucun tag n'a été créé.
- Aucune publication PyPI n'a été faite.
