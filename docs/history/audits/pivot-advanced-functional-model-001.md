# Décision — Modèle fonctionnel Pivot advanced

**Ticket** : PIVOT-ADVANCED-001-DEFINE-PIVOT-ADVANCED-FUNCTIONAL-MODEL
**Date** : 2026-05-20
**Statut** : décision rendue — Option C + D retenue

---

## 1. Résumé

Un pivot avec `pivot.fields[]` est une **entité relationnelle explicite**.
La gérer en CRUD simple (sélection d'IDs) est fonctionnellement insuffisant dès
qu'un champ porte des données métier (`position`, `note`, `role`, `joined_at`).

**Décision** : Pivot advanced = sous-CRUD relationnel dédié, implémenté via un
service et une commande/générateur séparés. `make:crud` core reste neutre.

---

## 2. Contexte

### Tickets précédents

- **PIVOT-CRUD-001** — Audit du comportement `pivot.fields[]` dans `make:crud`.
  Décision : `make:crud` ne gère pas l'édition avancée des attributs pivot.
- **PIVOT-CRUD-002** — Garde-fou : `required: true` / `nullable: false` dans
  `pivot.fields[]` bloquent `make:crud` avec un message explicite.
- **PIVOT-CRUD-CLOSE-001** — Bloc CRUD pivot simple clôturé.

### État actuel du pipeline

| Étape | État |
|---|---|
| `entity:validate` — validation de `pivot.fields[]` | OUI |
| `build:model` — génération SQL avec colonnes pivot | OUI |
| `make:crud` — synchronisation d'IDs many_to_many | OUI (IDs seuls) |
| `make:crud` — transmission de `pivot_fields` au CRUD | NON (éliminé à `relations_loader.py`) |
| Formulaires CRUD pour attributs pivot | NON |
| Vues `show` / `list` pour attributs pivot | NON |
| Service pivot advanced | NON |
| Commande/générateur dédié | NON |

---

## 3. Méthode d'audit

### Commandes exécutées

```bash
git status
python forge.py schema:list                              # 6 schémas OK
python forge.py schema:doctor                            # OK — toutes refs vérifiées
python forge.py entity:validate                          # OK
python forge.py build:model                              # OK — SQL pivot généré
pytest tests/test_make_crud_pivot_fields_guard.py -q     # 32 passed
pytest tests/test_pivot_fields_controlled.py -q          # 36 passed
pytest tests/test_many_to_many_pivot_integration.py -q   # 42 passed
pytest tests/meta/test_pivot_crud_close_001.py -q        # 9 passed (audit close)
```

### Zones auditées

- `forge_cli/entities/relations.py` — `ValidatedCanonicalManyToManyRelation`,
  `ValidatedPivotField`, `_validate_canonical_pivot_fields`, `_generate_canonical_m2m_sql`
- `forge_cli/entities/crud/relations_loader.py` — `_load_crud_many_to_many_relations`
  et le point d'élimination de `pivot_fields`
- `forge_cli/entities/crud/model_builder.py` — génération `sync_function` (IDs seuls)
- `forge_cli/entities/crud/views_builder.py` — `<select multiple>` sans attributs pivot
- `docs/entities/pivots-many-to-many.md`
- `docs/entities/limites-contrats-json.md`
- `docs/history/audits/pivot-crud-audit-001.md`

---

## 4. État actuel

### Ce que Forge sait faire

**`build:model`** génère un SQL complet incluant les colonnes de `pivot.fields[]` :

```sql
CREATE TABLE IF NOT EXISTS article_tag (
    id INT NOT NULL AUTO_INCREMENT,
    article_id INT NOT NULL,
    tag_id INT NOT NULL,
    position INT NOT NULL,           -- pivot.fields[]
    note VARCHAR(120) NULL,          -- pivot.fields[]
    PRIMARY KEY (id),
    UNIQUE KEY uq_article_tag (article_id, tag_id),
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);
```

**`entity:validate`** valide `pivot.fields[]` : types, nullable, noms réservés,
contrainte `unique_pair`, présence de `id`.

**`make:crud`** synchronise uniquement les paires d'IDs :

```python
def sync_article_tag_ids(article_id, selected_ids):
    with transaction() as tx:
        execute("DELETE FROM article_tag WHERE article_id = ?", (article_id,), tx=tx)
        for target_id in selected_ids:
            execute(
                "INSERT INTO article_tag (article_id, tag_id) VALUES (?, ?)",
                (article_id, target_id), tx=tx
            )
```

Les attributs `position` et `note` sont **invisibles dans ce code généré**.

### Ce que Forge ne sait pas faire

- Créer une association avec valeurs des attributs pivot
- Modifier les attributs d'une association existante
- Lire les attributs pivot dans une vue `show` ou `list`
- Supprimer une association ciblée par `(source_id, target_id)` ou `pivot_id`
- Respecter `unique_pair` en cas de modification
- Valider `required` / `nullable` lors d'une insertion pivot

### Point d'élimination confirmé

Dans `forge_cli/entities/crud/relations_loader.py`, ligne ~159 :

```python
CrudManyToManyRelation(
    name=rel.name,
    target_entity=rel.to_entity,
    target_table=rel.to_table,
    pivot_table=rel.pivot_table,
    source_key=rel.from_key,
    target_key=rel.to_key,
    # pivot_fields : non transmis — éliminés ici
)
```

`CrudManyToManyRelation` dans `context.py` n'a pas d'attribut `pivot_fields`.

---

## 5. Problème fonctionnel

Un pivot avec `pivot.fields[]` non tous nullables est un **pivot advanced** :
il porte des données métier qui ne peuvent pas être ignorées sans risque d'erreur
d'intégrité SQL.

Exemple concret :

```json
"fields": [
  { "name": "position", "type": "integer", "nullable": false },
  { "name": "note", "type": "string", "max_length": 120, "nullable": true }
]
```

`position INT NOT NULL` sans valeur par défaut : toute synchronisation via le
CRUD simple produira une erreur SQL (colonne NOT NULL sans valeur fournie).

Le garde-fou `PIVOT-CRUD-002` bloque actuellement `make:crud` dans ce cas.
C'est le comportement correct, mais il n'existe pas d'alternative implémentée.

---

## 6. Cas d'usage attendus

Les cas d'usage d'un CRUD pivot advanced sont distincts du CRUD d'entité classique.

| Action | Description |
|---|---|
| **Lire les associations** | Lister les paires `(source, target)` avec leurs attributs |
| **Créer une association** | Insérer `(source_id, target_id, position, note)` |
| **Modifier les attributs** | UPDATE sur une ligne pivot identifiée |
| **Supprimer une association** | DELETE ciblé `(source_id, target_id)` ou par `id` |
| **Vérifier unique_pair** | Bloquer les doublons `(source_id, target_id)` |
| **Valider required / nullable** | Refuser insertion si champ requis absent |
| **Gérer un id technique** | Accès par `pivot_id` si `pivot.id = true` |

La **synchronisation globale** (remplacer toutes les associations d'une source)
est un cas d'usage valide mais secondaire — elle sera couverte ultérieurement
(PIVOT-ADVANCED-006 ou suivant).

---

## 7. Options étudiées

| Option | Description | Verdict |
|---|---|---|
| **A — Ne rien faire** | Garder le statu quo, garde-fou seul | Insuffisant — bloque sans alternative |
| **B — Étendre make:crud** | Ajouter pivot.fields[] dans le CRUD généré | **Rejeté** — complexité, couplage, risque de régression |
| **C — Service pivot advanced** | Créer `PivotAdvancedService` avec méthodes dédiées | **Retenu** — socle propre, testable, découplé |
| **D — Commande/générateur dédié** | Créer `make:pivot-crud` ou équivalent | **Retenu** — opt-in, cohérent avec l'architecture Forge |
| **E — Entité explicite forcée** | Forcer le pivot à devenir une entité classique | Rejeté — casse le modèle relationnel déclaratif |

### Pourquoi B est rejeté

- `make:crud` génère le CRUD d'une entité. Une table pivot avec attributs n'est
  pas l'entité source ni l'entité cible — c'est la relation entre les deux.
- L'interface de sélection multiple (IDs) et le formulaire d'attributs pivot
  sont deux UX différentes qui ne doivent pas se mélanger.
- `CrudManyToManyRelation` devrait porter `pivot_fields` — refonte structurelle.
- Risque de régression sur les 12 000+ tests existants.
- Contradiction avec le principe 8 (noyau minimal) et la décision PIVOT-CRUD-001.

### Pourquoi C + D est retenu

- Le service encapsule la logique SQL pivot (INSERT, UPDATE, DELETE, SELECT) sans
  dépendance à `make:crud`.
- Le générateur/commande est opt-in — l'utilisateur active explicitement le CRUD
  pivot advanced sur une relation spécifique.
- Testable indépendamment des tests CRUD core existants.
- Cohérent avec l'architecture modulaire de Forge (`forge-mvc-rbac`,
  `forge-mvc-workflow` suivent le même modèle).

---

## 8. Décision retenue

**Option C + D retenue : service pivot advanced + commande/générateur dédié.**

`make:crud` reste **neutre** — il ne lit pas `pivot.fields[]` dans le CRUD
généré et ne produit aucun code pivot avancé.

### Nature du pivot advanced

Un pivot avec `pivot.fields[]` dont certains sont non-nullables est traité comme
un **sous-CRUD relationnel dédié** : il a ses propres opérations CRUD,
distinctes du CRUD de l'entité source ou cible.

Ce n'est pas :
- une entité classique (pas de fichier `<pivot>.json`)
- une extension de `make:crud` (pas de génération automatique)
- un module opt-in au sens de `forge-mvc-rbac` (pas de package séparé à ce stade)

C'est un **service de persistence pivot** + un **générateur de code dédié**.

---

## 9. Modèle fonctionnel cible

### Service `PivotAdvancedService` (PIVOT-ADVANCED-003)

Nom indicatif — l'implémentation exacte est décidée dans PIVOT-ADVANCED-003.

| Méthode | Signature | Description |
|---|---|---|
| `attach` | `(source_id, target_id, pivot_data)` | Crée une association avec attributs |
| `detach` | `(source_id, target_id)` | Supprime une association ciblée |
| `update` | `(source_id, target_id, pivot_data)` | Modifie les attributs d'une association |
| `list_for_source` | `(source_id)` | Liste toutes les associations d'une source |
| `get` | `(source_id, target_id)` | Lit une association spécifique |

**Si `pivot.id = true`** (accès par id technique) :

| Méthode | Signature | Description |
|---|---|---|
| `get_by_id` | `(pivot_id)` | Lit une ligne pivot par son id |
| `update_by_id` | `(pivot_id, pivot_data)` | Modifie une ligne pivot par son id |
| `delete_by_id` | `(pivot_id)` | Supprime une ligne pivot par son id |

### Modèle d'identification

La base fonctionnelle est **`(source_id, target_id)`** — c'est la clé naturelle
d'une relation many_to_many.

Si `pivot.id = true`, les deux modèles sont supportés : `(source_id, target_id)`
reste la base, `pivot_id` est un accès alternatif.

### Contraintes à respecter

| Contrainte | Traitement |
|---|---|
| `required: true` / `nullable: false` | Validation avant INSERT/UPDATE |
| `unique_pair` | Vérification ou gestion `INSERT … ON DUPLICATE KEY` |
| `id` technique | Génération automatique `AUTO_INCREMENT` — déjà géré en SQL |
| Noms réservés (`id`, `from_key`, `to_key`) | Interdits dans `pivot_data` |

---

## 10. Hors périmètre

Ce ticket (PIVOT-ADVANCED-001) est un cadrage fonctionnel uniquement.

Sont hors périmètre :

- toute implémentation de `PivotAdvancedService`
- toute commande ou générateur dédié
- toute modification de `make:crud`
- toute modification de `relations.py`, `relations_loader.py`, `model_builder.py`
- toute modification des schémas JSON
- toute modification des starters ou exemples
- toute publication PyPI ou création de tag

Le service ne sera pas implémenté dans ce ticket — il sera défini dans
PIVOT-ADVANCED-002 (UX et modèle d'usage) puis implémenté dans PIVOT-ADVANCED-003.

---

## 11. Tickets futurs proposés

| Ticket | Objectif |
|---|---|
| **PIVOT-ADVANCED-002** | Définir l'UX et le modèle d'usage applicatif du pivot advanced |
| **PIVOT-ADVANCED-003** | Créer `PivotAdvancedService` — lecture/écriture pivot avec attributs |
| **PIVOT-ADVANCED-004** | Créer une commande ou un générateur dédié (`make:pivot-crud` ou équivalent) |
| **PIVOT-ADVANCED-005** | Tests E2E pivot advanced — parcours complets avec attributs |
| **PIVOT-ADVANCED-006** | Gestion des contraintes : `required`, `nullable`, `unique_pair`, `id` technique |
| **PIVOT-ADVANCED-007** | Gestion UX des erreurs de validation pivot (formulaires, messages) |
| **PIVOT-ADVANCED-008** | Documentation complète + exemples réels |
| **PIVOT-ADVANCED-CLOSE-001** | Clôturer le bloc pivot advanced |

---

## Mise en œuvre partielle — PIVOT-ADVANCED-003

## Mise en œuvre partielle — PIVOT-ADVANCED-005

PIVOT-ADVANCED-005 ajoute des tests E2E du flux Pivot advanced :
contrat `relations.json` canonique, génération `make:pivot-crud`, fichiers générés,
et cycle complet `PivotAdvancedService` sur SQLite in-memory
(`attach → get → list_for_source → update → detach`).

---

## Mise en œuvre partielle — PIVOT-ADVANCED-004

PIVOT-ADVANCED-004 ajoute la commande dédiée `make:pivot-crud`.
La commande analyse une relation `many_to_many` avec `pivot.fields[]` et génère
un contrôleur et des templates dédiés sans modifier `make:crud`.
Les routes sont documentées mais non branchées automatiquement.

---

PIVOT-ADVANCED-003 crée le service technique `PivotAdvancedService`
dans `core/pivot_advanced.py`.

Le service fournit les opérations de base sur une table pivot avec attributs :
`attach`, `detach`, `update`, `list_for_source`, `get`.

Aucune commande, aucun écran et aucune intégration `make:crud` ne sont ajoutés
dans ce ticket. Le service est utilisable en production et testé sans connexion
MariaDB réelle via des callables injectables.

---

## Mise en œuvre partielle — PIVOT-ADVANCED-006

PIVOT-ADVANCED-006 ajoute les contraintes déclaratives au service :

- `PivotFieldConstraint(name, required, nullable)` — déclaration des contraintes par champ
- `PivotConstraintError` — exception contrôlée (sous-classe de `ValueError`)
- `pivot_constraints=[...]` — nouveau paramètre optionnel du constructeur
- `unique_pair=True` — vérification applicative avant INSERT (lève `PivotConstraintError`)
- `id_field="id"` — active `get_by_id`, `update_by_id`, `delete_by_id`

L'API `pivot_fields=[...]` reste inchangée (backward compatible).
34 nouveaux tests dans `tests/test_pivot_advanced_constraints.py`.

---

## Mise en œuvre partielle — PIVOT-ADVANCED-007

PIVOT-ADVANCED-007 ajoute une couche de traduction UX pour les erreurs de contraintes pivot.
Les erreurs techniques de `PivotAdvancedService` peuvent être converties en messages affichables
par le sous-CRUD pivot.

Ajouts dans `core/pivot_advanced.py` :

- `PivotFormError(code, message, field)` — erreur normalisée affichable dans un formulaire
- `PivotConstraintError` enrichi avec `code` et `field` (backward compatible)
- `pivot_error_to_form_error(exc)` — helper de conversion exception → `PivotFormError`

Codes stables : `required_field_missing`, `nullable_field_rejected`, `duplicate_pair`,
`missing_id_field`, `unknown_pivot_field`, `invalid_pivot_data`.

Le contrôleur généré par `make:pivot-crud` intègre maintenant `try/except` avec
`pivot_error_to_form_error` dans `add` et `edit`. Le template `form.html` affiche
`error.message` si une erreur est présente. `make:crud` reste neutre.
27 nouveaux tests dans `tests/test_pivot_advanced_error_ux.py`.

---

## Mise en œuvre partielle — PIVOT-ADVANCED-008

PIVOT-ADVANCED-008 ajoute la documentation complète d'usage du Pivot advanced :
contrat `relations.json`, commande `make:pivot-crud`, `PivotAdvancedService`,
contraintes, erreurs UX et limites.

Page créée : `docs/entities/pivot-advanced.md`.
Référencée dans `mkdocs.yml` et liée depuis `docs/entities/pivots-many-to-many.md`.
Tests meta : `tests/meta/test_pivot_advanced_usage_docs_008.py`.

---

## Clôture — PIVOT-ADVANCED-CLOSE-001

**Statut : terminé.**

Le bloc Pivot advanced est clôturé après livraison de :

- **PIVOT-ADVANCED-001** — modèle fonctionnel ;
- **PIVOT-ADVANCED-002** — UX et modèle d'usage ;
- **PIVOT-ADVANCED-003** — `PivotAdvancedService` ;
- **PIVOT-ADVANCED-004** — commande `make:pivot-crud` ;
- **PIVOT-ADVANCED-005** — tests E2E ;
- **PIVOT-ADVANCED-006** — contraintes `required`, `nullable`, `unique_pair`, `id` technique ;
- **PIVOT-ADVANCED-007** — erreurs UX ;
- **PIVOT-ADVANCED-008** — documentation complète.

### État final

- `PivotAdvancedService` fournit les opérations `attach`, `get`, `list_for_source`,
  `update`, `detach` ;
- `PivotAdvancedService` gère les contraintes `required`, `nullable`, `unique_pair`
  et `id_field` ;
- `make:pivot-crud` génère un sous-CRUD pivot opt-in ;
- les erreurs de contrainte sont convertibles en `PivotFormError` via
  `pivot_error_to_form_error` ;
- `docs/entities/pivot-advanced.md` documente l'usage complet ;
- `make:crud` reste **neutre** ;
- les routes ne sont **pas branchées automatiquement** ;
- aucun schéma JSON n'est modifié ;
- aucune publication PyPI ni création de tag n'a été effectuée.
