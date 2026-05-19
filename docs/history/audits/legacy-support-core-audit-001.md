# Audit — Support legacy dans le core Forge

**Ticket** : LEGACY-POLICY-001
**Date** : 2026-05-19
**Auteur** : Forge (audit post-migration starters)
**Périmètre** : `forge_cli/entities/`, `forge_cli/starters/`, `tests/`, code runtime

---

## 1. Résumé

L'audit confirme que le support du format legacy (`format_version: 1`) est encore présent
et actif dans le core Forge. Il est profondément intégré dans le pipeline de génération
(`build:model`, `make:crud`, `make:entity`) via le normaliseur interne.

Les starters distribués ne dépendent **plus** du format legacy (migration complète, 100 %).

Le format legacy est encore utilisé directement dans **55 fichiers de tests**
(187+ instances de `"format_version": 1`).

Ce rapport ne préconise **pas** la suppression immédiate.

---

## 2. Contexte

Suite à la campagne de migration STARTERS-MIGRATE-001 à STARTERS-MIGRATE-005,
tous les starters distribués utilisent `schema_version: "1.0"`. Le support legacy
dans le core Forge n'est plus nécessaire pour les starters, mais reste présent pour :

- les projets utilisateurs antérieurs en `format_version: 1` ;
- les tests unitaires du pipeline legacy ;
- la cohérence interne du pipeline de génération.

---

## 3. Méthode d'audit

```bash
grep -RInE 'format_version' forge_cli core 2>/dev/null
grep -RInl 'format_version.*1|validate_entity_definition|normalize_entity_definition' tests/
grep -RInE 'format_version|sql_type|python_type|...' forge_cli/starters/data 2>/dev/null
```

---

## 4. Chemins legacy détectés dans le core

### 4.1 `forge_cli/entities/validation.py` — normaliseur legacy central

**Rôle** : valide et normalise les entités en format legacy (format_version: 1).

Fonctions exposées :
- `validate_entity_definition(data, source)` — accepte `format_version: 1`, `sql_type`, `python_type`, `primary_key`, `auto_increment`
- `normalize_entity_definition(data, source)` — produit le dictionnaire interne normalisé (format_version, python_type, sql_type, etc.)

Clé centrale :
```python
ALLOWED_ROOT_KEYS = {"format_version", "entity", "table", "description", "fields", "media", "rbac"}
```

Le normaliseur **exporte** `format_version: 1` dans sa sortie (ligne 410), ce qui en fait
le format interne de tout le pipeline de génération.

**Appelé par** : `build:model`, `make:crud`, `make:entity`, migrations.
**Support legacy** : direct — format legacy est le format interne de traitement.
**Risque si suppression** : très élevé — tout le pipeline s'arrête.

---

### 4.2 `forge_cli/entities/canonical_model_normalizer.py` — pont canonique→legacy

**Rôle** : convertit les entités canoniques (`schema_version: "1.0"`) vers le format interne legacy.

`normalize_canonical_entity_for_model_build(data)` produit un dict avec :
`format_version: 1`, `sql_type`, `python_type`, `primary_key`, `auto_increment`, `column`.

C'est grâce à ce pont que les entités canoniques fonctionnent dans le pipeline.

**Appelé par** : `model.py`, `make_crud.py`, `make_entity.py`.
**Support legacy** : indirect — le format legacy est le format interne cible.
**Risque si suppression** : très élevé — supprime la compatibilité canonique.

---

### 4.3 `forge_cli/entities/model.py` — `build:model`

Lignes 86-87 et 334-335 : détection canonique → appel au pont.

```python
if isinstance(raw_data, dict) and raw_data.get("schema_version") == "1.0":
    raw_data = normalize_canonical_entity_for_model_build(raw_data)
```

Après la détection, le reste du pipeline traite uniquement le format interne legacy.

**Commandes** : `build:model`.
**Support legacy** : tolère les deux formats en entrée, traite en legacy interne.

---

### 4.4 `forge_cli/entities/make_entity.py` — générateur SQL

Lignes 364-382 : utilise `field["column"]`, `field["sql_type"]`, `field["primary_key"]`,
`field["auto_increment"]` — clés du format interne legacy.

Ligne 68, 249, 325 : crée les **nouvelles** entités en format canonique
(`schema_version: "1.0"`) — `make:entity` est déjà canonique en sortie.

**Commandes** : `make:entity`, `build:model`.
**Support legacy** : interne (représentation normalisée).

---

### 4.5 `forge_cli/entities/relations.py` — validateur de relations

Ligne 159 : détection canonique → pont.
Ligne 207 : dispatch `from/to` (canonique) vs `from_entity/to_entity` (legacy).
Lignes 564-578 : validation des deux formats en entrée.

La structure interne `ValidatedRelation` conserve les champs `from_entity`, `to_entity`,
`foreign_key_name` — noms internes hérités du format legacy.

**Commandes** : `build:model`, `make:crud`.
**Support legacy** : direct pour les relations legacy, indirect pour les relations canoniques.

---

### 4.6 `forge_cli/entities/make_crud.py` — générateur CRUD

Lignes 170-171 : même pattern de détection canonique → pont.

**Commandes** : `make:crud`.
**Support legacy** : indirect (via pont), direct (tests et données legacy).

---

### 4.7 `forge_cli/starters/relations.py` — `drop_foreign_keys()`

Lignes 41-42 :
```python
table = rel.get("from_entity", "")
fk = rel.get("foreign_key_name", "")
```

**Anomalie détectée** : cette fonction lit encore les clés legacy `from_entity` et
`foreign_key_name`. Depuis la migration des starters vers le format canonique
(`from`, `foreign_key`), elle ne trouve plus ces clés et saute silencieusement toutes les FK.

Impact : le `DROP FOREIGN KEY` automatique lors d'un `starter:build --force` ne fonctionne
plus pour les starters canoniques. Impact limité car :
- la fonction retourne silencieusement si `mariadb` n'est pas installé ;
- `drop_foreign_keys` n'est utile que lors d'un rebuild avec DB active.

**Risque** : faible en pratique (bêta, pas de production) — corrigé dans
`LEGACY-STARTERRELS-FIX-001` (double fallback canonique + legacy).

---

### 4.8 `forge_cli/starters/scaffold.py` — détection relations vides

Ligne 39 :
```python
return data == {"format_version": 1, "relations": []}
```

Détecte si un fichier `relations.json` est le template legacy vide (pour savoir s'il est
"adoptable" par un starter). Depuis la migration, ce template n'est plus utilisé.

**Correction** : détection étendue aux deux formats dans `LEGACY-SCAFFOLD-FIX-001` —
`data.get("format_version") == 1` **ou** `data.get("schema_version") == "1.0"`, avec
`data.get("relations") == []`. Le code n'est plus potentiellement mort pour les starters canoniques.

---

### 4.9 `forge_cli/entities/make_relation.py` — `make:relation`

Ligne 135 :
```python
if "schema_version" not in data and "format_version" not in data:
    raise ValueError(...)
```

Accepte les deux formats en entrée. Commande `make:relation`.

---

## 5. Tests legacy détectés

### Volumétrie

| Métrique | Valeur |
|---|---|
| Fichiers de test référençant le legacy | 55 |
| Lignes `"format_version": 1` dans les tests | 187+ |
| Fichiers de test utilisant `validate_entity_definition` | ~10 |
| Fichiers de test utilisant `normalize_entity_definition` | ~5 |

### Classification

**Tests de compatibilité legacy utiles (à conserver tant que le support existe) :**

| Fichier | Rôle |
|---|---|
| `tests/test_entity_json_validation.py` | Validation du normaliseur legacy |
| `tests/test_entity_relations.py` | Relations en format legacy |
| `tests/test_make_crud.py` | CRUD generation depuis entités legacy |
| `tests/test_make_entity_canonical.py` | Pont canonique → legacy |
| `tests/test_entity_semantic_validation.py` | Validation sémantique legacy |
| `tests/test_entity_model_cli.py` | CLI `build:model` sur entités legacy |

**Tests de non-régression (nécessaires tant que le support existe) :**

La majorité des ~40 autres fichiers utilisent des fixtures legacy pour tester les générateurs
CRUD (forms, views, controllers, models, media, rbac, pagination, filtres, etc.).
Ces tests n'ont pas pour objet de tester le format legacy mais utilisent ce format
comme entrée de données.

**Tests potentiellement obsolètes (à évaluer dans LEGACY-POLICY-002) :**

Tests qui testent explicitement le comportement legacy (`format_version: 1` dans les
assertions), par opposition à ceux qui l'utilisent seulement comme fixture d'entrée.

---

## 6. Starters : dépendance legacy restante

| Vérification | Résultat |
|---|---|
| `format_version` dans les starters | **0 occurrence** |
| `sql_type` dans les starters | **0 occurrence** |
| `primary_key / auto_increment` dans les starters | **0 occurrence** |
| `from_entity / to_entity` dans les starters | **0 occurrence** |
| `foreign_key_name` dans les starters | **0 occurrence** |
| Fichiers canoniques (`schema_version: "1.0"`) | **15 fichiers (12 entités + 3 relations)** |

**Conclusion** : les starters ne dépendent plus du format legacy.

---

## 7. Commandes impactées

| Commande | Support legacy | Détail |
|---|---|---|
| `entity:validate` | NON | Validation JSON Schema pure — canonique uniquement |
| `make:entity` | Entrée uniquement | Lit les anciennes entités, crée en canonique |
| `build:model` | OUI (via pont) | Accepte legacy et canonique (via `canonical_model_normalizer`) |
| `make:crud` | OUI (via pont) | Idem |
| `make:relation` | OUI | Accepte les deux formats |
| `starter:build` | Indirect | Copie les entités canoniques ; `drop_foreign_keys` cassé (§4.7) |
| `forge new` | Hors scope | Clone `media.json` depuis GitHub |
| `migration:diff` / `migration:make` | OUI (via model) | Accepte les deux formats |

---

## 8. Risques si suppression immédiate

| Risque | Sévérité | Détail |
|---|---|---|
| 55 fichiers de tests cassés (187+ fixtures legacy) | Très élevée | Réécriture complète nécessaire |
| Projets utilisateurs encore en `format_version: 1` | Haute | Aucun outil de migration fourni |
| `build:model` / `make:crud` cassés pour entités legacy | Très élevée | Le format interne est le format legacy normalisé |
| `canonical_model_normalizer` devient inutile | Moyenne | Devrait être adapté, pas supprimé |
| `drop_foreign_keys` déjà cassé pour canonique | Faible | Correction indépendante possible |
| Documentation legacy encore référencée | Faible | Docs à mettre à jour |

---

## 9. Options de politique legacy

### Option A — Maintien temporaire (recommandée à court terme)

Garder le support legacy intact. Le documenter comme format historique, non recommandé
pour les nouveaux projets.

**Avantages** :
- Protège les anciens projets (bêta, sans utilisateurs externes confirmés)
- Aucune rupture de tests (économie d'effort)
- Cohérent avec la politique pré-3.0 (pas de guide de migration formel)

**Inconvénients** :
- Complexité du pipeline maintenue
- Deux formats coexistent, ce qui peut dérouter les nouveaux contributeurs

---

### Option B — Dépréciation active (recommandée à moyen terme)

Documenter `format_version: 1` comme déprécié. Ajouter un avertissement si une commande
reçoit une entité legacy. Planifier la suppression dans Forge 3.1 ou 4.0.

**Avantages** :
- Prépare la suppression sans rupture immédiate
- Informe les utilisateurs existants

**Inconvénients** :
- Nécessite un message de dépréciation dans `validate_entity_definition()`
- Peut bruiter `build:model` pour les anciens projets

---

### Option C — Suppression future planifiée (recommandée à long terme)

Supprimer le support legacy dans une version majeure (3.1, 4.0). Fournir un outil ou
guide de migration.

**Avantages** :
- Simplifie le core significativement
- Impose le format canonique partout

**Inconvénients** :
- Rupture pour les anciens projets sans migration préalable
- Réécriture de ~55 fichiers de tests nécessaire

---

## 10. Recommandation

**Recommandation** : Option A à court terme, transition vers Option B dans LEGACY-POLICY-002.

Ne pas supprimer le support legacy maintenant. Le pipeline interne de Forge repose sur
le format normalisé legacy comme représentation intermédiaire universelle. La suppression
exigerait une refonte architecturale majeure du pipeline de génération (hors scope d'un
simple "retrait de format").

Corrections prioritaires indépendantes :
1. `LEGACY-STARTERRELS-FIX-001` — corriger `drop_foreign_keys()` pour lire `from` et `foreign_key` canoniques.
2. `LEGACY-SCAFFOLD-FIX-001` — mettre à jour la détection de relations vides dans `scaffold.py`.

---

## 11. Prochains tickets proposés

| Ticket | Objectif | Statut |
|---|---|---|
| `LEGACY-STARTERRELS-FIX-001` | Corriger `drop_foreign_keys()` pour relations canoniques | **Livré** |
| `LEGACY-SCAFFOLD-FIX-001` | Mettre à jour la détection de relations vides dans `scaffold.py` | **Livré** |
| `LEGACY-POLICY-002` | Décider et documenter la politique de dépréciation du format legacy | **Livré** |
| `LEGACY-MIGRATION-001` | Documenter ou outiller la migration des anciens projets | Ouvert |
| `LEGACY-REMOVE-001` | Supprimer le support legacy (version majeure future) | Ouvert |

---

## 12. Décision post-audit

**Décision** : maintien temporaire avec dépréciation documentée.

Le format legacy `format_version: 1` est officiellement déprécié au profit du format canonique
`schema_version: "1.0"`. Le support temporaire est maintenu pour la compatibilité du pipeline
interne et des projets existants.

Voir **ADR-012 — Politique de dépréciation du format legacy des entités Forge** :
`docs/adr/012-legacy-format-deprecation-policy.md`
