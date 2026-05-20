# Audit — CRUD avancé des attributs de pivot

**Date** : 2026-05-20
**Ticket** : PIVOT-CRUD-001-AUDIT-PIVOT-FIELDS-CRUD-BEHAVIOR
**Statut** : Décision rendue — Option A retenue

---

## 1. Résumé

`pivot.fields[]` est validé par `entity:validate` et génère du SQL correct via
`build:model`. En revanche, `make:crud` n'expose pas les attributs de pivot dans
les formulaires, contrôleurs ou vues générés. Les champs pivot sont éliminés lors
de la conversion `ValidatedCanonicalManyToManyRelation → CrudManyToManyRelation`
dans `relations_loader.py`.

**Décision recommandée** : ne pas intégrer l'édition des attributs pivot dans
`make:crud` core à ce stade. L'approche correcte est un module ou une commande
dédiée (Option A + voie vers Option D).

---

## 2. Contexte

Les tickets ENTITY-CONTRACT-017 et ENTITY-CONTRACT-018 ont :

- validé les types Forge autorisés dans `pivot.fields[]` (12 types + `string`/`decimal`) ;
- ajouté la protection des noms réservés (`id`, `from_key`, `to_key`) ;
- généré le SQL pivot avec colonnes métier dans `relations.sql` ;
- intégré les relations canoniques `many_to_many` dans `make:crud` ;
- validé la non-régression avec 127 tests passants.

La question ouverte : `make:crud` doit-il aller plus loin et exposer
`pivot.fields[]` dans les formulaires et vues générés ?

---

## 3. Méthode d'audit

**Commandes exécutées** :

```bash
git status                                               # propre (1 commit ahead)
python forge.py schema:list                             # 6 schémas OK dont pivot
python forge.py schema:doctor                           # OK — toutes refs vérifiées
python forge.py entity:validate                         # OK (pas d'entité locale)
pytest tests/test_pivot_fields_controlled.py -q         # 36 passed
pytest tests/test_make_crud_many_to_many_canonical.py -q # 5 passed
pytest tests/test_many_to_many_pivot_integration.py -q  # 42 passed
pytest tests/test_many_to_many_canonical_generation.py -q # 44 passed
```

**Zones auditées** :

- `forge_cli/entities/relations.py` — `ValidatedCanonicalManyToManyRelation`, `ValidatedPivotField`, `_generate_canonical_m2m_sql`, `_validate_canonical_pivot_fields`
- `forge_cli/entities/crud/relations_loader.py` — `_load_crud_many_to_many_relations`
- `forge_cli/entities/crud/context.py` — `CrudManyToManyRelation`
- `forge_cli/entities/crud/model_builder.py` — `add_function` / `sync_function`
- `forge_cli/entities/crud/views_builder.py` — génération `<select multiple>`
- `forge_cli/entities/make_crud.py` — pipeline CRUD principal
- `docs/entities/pivots-many-to-many.md`
- `docs/entities/relations-schema.md`
- `docs/entities/limites-contrats-json.md`
- `tests/test_pivot_fields_controlled.py`
- `tests/test_make_crud_many_to_many_canonical.py`

---

## 4. Contrat many_to_many actuel

### 4.1 Types autorisés dans pivot.fields[]

Tous les types Forge acceptés dans `field.schema.json` sont supportés :

| Type Forge | SQL généré |
|---|---|
| `string` (+ `max_length`) | `VARCHAR(n)` / `VARCHAR(255)` par défaut |
| `text` | `TEXT` |
| `integer` | `INT` |
| `big_integer` | `BIGINT` |
| `float` | `DOUBLE` |
| `decimal` (+ `precision`, `scale`) | `DECIMAL(p,s)` |
| `boolean` | `BOOLEAN` |
| `date` | `DATE` |
| `datetime` | `DATETIME` |
| `email` | `VARCHAR(255)` |
| `password` | `VARCHAR(255)` |
| `json` | `LONGTEXT` |

### 4.2 Contraintes nullable / required

La règle est uniforme (ADR-013) :

- champ nullable par défaut → `NULL`
- `nullable: false` → `NOT NULL`
- `required: true` → `NOT NULL` (prioritaire sur `nullable: true`)

### 4.3 Contrainte unique

`unique: true` génère `UNIQUE KEY uq_{pivot_table}_{field_name}`.

### 4.4 Noms réservés

`id`, la valeur de `from_key` et la valeur de `to_key` sont interdits dans
`pivot.fields[]`. Toute collision lève `EntityRelationsError` avec le code
`FORGE_PIVOT_RESERVED_FIELD`.

### 4.5 id et unique_pair

`pivot.id` doit valoir `true` (contrainte `const`). Un `id INT NOT NULL AUTO_INCREMENT`
est toujours généré. `pivot.unique_pair` doit aussi valoir `true` — une contrainte
`UNIQUE (from_key, to_key)` est toujours présente.

---

## 5. Comportement SQL actuel

`_generate_canonical_m2m_sql()` dans `relations.py` produit une table pivot complète
incluant les colonnes de `pivot.fields[]` :

```sql
CREATE TABLE IF NOT EXISTS project_user (
    id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    project_id INT NOT NULL,
    role VARCHAR(50) NOT NULL,        -- pivot.fields[] inclus
    joined_at DATETIME NULL,          -- pivot.fields[] inclus
    PRIMARY KEY (id),
    UNIQUE KEY uq_project_user (user_id, project_id),
    ...
);
```

**Les champs pivot sont générés en SQL.** Statut : OUI.

---

## 6. Comportement make:crud actuel

### 6.1 Détection des relations many_to_many canoniques

`_load_crud_many_to_many_relations()` dans `relations_loader.py` reconnaît les
`ValidatedCanonicalManyToManyRelation` (schema_version 1.0) et les traite au même
titre que les relations legacy.

### 6.2 Élimination de pivot_fields

**Point critique** : la conversion de `ValidatedCanonicalManyToManyRelation` vers
`CrudManyToManyRelation` ne copie pas `pivot_fields`. Extrait de
`forge_cli/entities/crud/relations_loader.py` (ligne ~119) :

```python
CrudManyToManyRelation(
    name=rel.name,
    target_entity=rel.to_entity,
    target_table=rel.to_table,
    pivot_table=rel.pivot_table,
    source_key=rel.from_key,
    target_key=rel.to_key,
    # pivot_fields : non transmis
)
```

`CrudManyToManyRelation` dans `context.py` n'a pas d'attribut `pivot_fields`.
L'information est définitivement perdue après cette étape.

### 6.3 Génération des formulaires

`views_builder.py` génère uniquement un `<select multiple>` d'IDs pour les
relations many_to_many. Aucune référence à `pivot_fields` n'existe dans ce
fichier.

```html
<select name="project_ids" multiple>
  {% for value, label in project_choices %}
    <option value="{{ value }}"
      {% if value in project_ids_selected %}selected{% endif %}>
      {{ label }}
    </option>
  {% endfor %}
</select>
```

### 6.4 Génération des fonctions de synchronisation

`model_builder.py` génère une synchronisation simple d'IDs uniquement :

```python
def sync_member_project_ids(member_id, selected_ids):
    from core.database.transaction import transaction
    with transaction() as tx:
        for target_id in selected_ids:
            execute(
                "INSERT INTO member_project (member_id, project_id) VALUES (?, ?)",
                (member_id, target_id), tx=tx
            )
```

Aucune valeur de `pivot.fields[]` n'est insérée. Si un champ pivot est `NOT NULL`
sans valeur par défaut en base (ex : `role VARCHAR(50) NOT NULL`), la requête
générée échouera à l'exécution.

---

## 7. Limites actuelles

| Limite | Impact |
|---|---|
| `pivot_fields` éliminés à `relations_loader.py` | Aucune donnée pivot n'atteint le CRUD |
| `CrudManyToManyRelation` sans `pivot_fields` | Impossible d'exposer les champs sans refonte |
| Sync génère `INSERT (from, to) VALUES (?, ?)` | Insertion incomplète si champ `NOT NULL` sans défaut |
| Aucun formulaire pour les attributs pivot | L'utilisateur ne peut pas saisir `role`, `position`, etc. |
| Aucune vue `show` / `list` pour les attributs pivot | Les données pivot sont invisibles dans l'interface |
| Pas de gestion UPDATE sur les lignes pivot | Modifier un attribut pivot existant est impossible via CRUD |

**Risque d'intégrité** : un pivot avec un champ `NOT NULL` sans valeur par défaut
(ex : `role VARCHAR(50) NOT NULL`) sera rejeté par la base de données lors de la
synchronisation générée par `make:crud`. Forge valide et génère le SQL correct,
mais le code CRUD ne peut pas remplir ce champ. Ce risque devra être documenté
ou bloqué dans un ticket futur.

---

## 8. Options étudiées

### Option A — Ne pas gérer pivot.fields[] dans le CRUD core (recommandée)

`make:crud` ignore `pivot.fields[]`. La synchronisation d'IDs reste la seule
opération CRUD sur les relations many_to_many.

**Avantages** :
- Zéro risque de régression sur 127 tests passants
- `make:crud` reste simple — une relation = une sélection d'IDs
- Séparation claire : contrat = structure relationnelle, CRUD = gestion basique
- Cohérent avec le principe 8 — noyau minimal

**Inconvénient** :
- Un pivot avec champs `NOT NULL` sans défaut produira des erreurs à l'exécution

### Option B — Afficher pivot.fields[] en lecture seule

`make:crud` génère des vues `show` et `list` affichant les attributs pivot,
sans formulaire d'édition.

**Avantages** : visualisation des données pivot dans l'interface.

**Inconvénients** :
- Nécessite que `CrudManyToManyRelation` porte `pivot_fields`
- Les templates doivent être étendus pour les pivots
- Pas de solution au problème d'insertion incomplète
- Valeur partielle : on affiche ce qu'on ne peut pas encore saisir

**Verdict** : valeur faible sans Option C ; couplage sans bénéfice complet.

### Option C — Éditer pivot.fields[] dans les formulaires CRUD

`make:crud` génère des formulaires permettant de saisir les attributs pivot lors
de l'association (ex : saisir le `role` au moment de lier un User à un Project).

**Avantages** : CRUD pivot complet, saisie + modification + suppression.

**Inconvénients** :
- Fort couplage `make:crud` ↔ structure pivot avancée
- L'interface de sélection multiple devient un formulaire complexe (IDs + attributs)
- Gestion du UPDATE : `INSERT … ON DUPLICATE KEY UPDATE role = ?` ou DELETE + INSERT
- Conflits potentiels avec la contrainte `unique_pair`
- Doublement de la complexité du générateur CRUD
- Aucun modèle de référence dans le CRUD core actuel

**Verdict** : périmètre trop large pour `make:crud` core ; peut être PIVOT-CRUD-003.

### Option D — Module ou commande dédiée pour le CRUD pivot avancé

`make:crud` core reste neutre. Une commande dédiée (`make:pivot-crud` ?) ou un
module `forge-mvc-pivot` gère la génération de formulaires et contrôleurs pour
les tables pivot avec attributs.

**Avantages** :
- CRUD core reste simple
- Le CRUD pivot avancé est vraiment opt-in
- Conception dédiée, testée séparément
- Cohérent avec l'architecture modulaire de Forge

**Inconvénient** :
- Plus complexe à construire et à utiliser
- Nécessite une conception et des tickets dédiés

**Verdict** : meilleur design à long terme, mais hors périmètre actuel.

---

## 9. Décision recommandée

**Option A retenue : ne pas intégrer l'édition de `pivot.fields[]` dans
`make:crud` core.**

**Justification** :

1. **Complexité disproportionnée** : la gestion d'un CRUD pivot avec attributs
   est un problème de CRUD relationnel avancé, pas une extension naturelle du
   CRUD d'entité standard.

2. **Principe 8 — Noyau minimal** : `make:crud` génère le CRUD d'une entité.
   Les attributs de la relation entre deux entités relèvent d'un autre niveau
   de modélisation.

3. **Zéro régression** : 127 tests passent avec le comportement actuel. Toute
   modification de `make:crud` ou `CrudManyToManyRelation` risque des régressions.

4. **Option D comme horizon** : l'architecture modulaire de Forge (principe 8)
   est mieux servie par un module `forge-mvc-pivot` ou une commande dédiée
   que par une extension de `make:crud` core.

5. **Risque d'intégrité à documenter** : le cas d'un pivot avec champ `NOT NULL`
   sans valeur par défaut devra faire l'objet d'un avertissement ou d'une
   validation dans un ticket futur (PIVOT-CRUD-002).

---

## 10. État final après PIVOT-CRUD-001

| Élément | État |
|---|---|
| `pivot.fields[]` validé par `entity:validate` | OUI |
| SQL pivot avec colonnes métier généré | OUI |
| `make:crud` détecte les relations M2M canoniques | OUI |
| `make:crud` transmet `pivot_fields` au CRUD | NON — éliminé à `relations_loader.py` |
| Formulaires CRUD pour attributs pivot | NON |
| Vues `show` / `list` pour attributs pivot | NON |
| Sync génère INSERT avec attributs pivot | NON — IDs uniquement |
| Runtime CRUD pivot avancé implémenté | NON |

---

## 11. Tickets futurs proposés

| Ticket | Objectif | Priorité |
|---|---|---|
| `PIVOT-CRUD-002` | Avertir ou bloquer si pivot avec champ `NOT NULL` sans défaut détecté lors de `make:crud` | Recommandé |
| `PIVOT-CRUD-003` | Implémenter Option C — édition pivot.fields[] dans make:crud core | Faible |
| `PIVOT-CRUD-004` | Concevoir Option D — module ou commande dédiée pour CRUD pivot avancé | Long terme |

**Recommandation** : poursuivre avec `PIVOT-CRUD-002` — protéger contre le cas
d'intégrité d'un pivot avec champ `NOT NULL` sans valeur par défaut.

---

## Clôture — PIVOT-CRUD-CLOSE-001

**Statut : terminé.**

Le bloc CRUD `pivot.fields[]` est clôturé après livraison de :

- PIVOT-CRUD-001 — audit du comportement CRUD des attributs pivot ;
- PIVOT-CRUD-002 — garde-fou `make:crud` contre les champs pivot obligatoires non gérés.

État final :

- `pivot.fields[]` est accepté par le contrat `many_to_many` canonique ;
- `build:model` génère les colonnes SQL de pivot ;
- `make:crud` détecte les relations `many_to_many` canoniques ;
- `make:crud` synchronise uniquement les identifiants ;
- `make:crud` n'édite pas les attributs pivot ;
- `make:crud` accepte les champs pivot `nullable` ;
- `make:crud` refuse les champs pivot `required: true` ou `nullable: false` ;
- aucun CRUD pivot avancé n'est implémenté dans Forge Core ;
- un module ou une commande dédiée pourra être envisagé plus tard.

---

## Mise en œuvre partielle — PIVOT-CRUD-002

PIVOT-CRUD-002 a ajouté un garde-fou dans `make:crud` contre les
`pivot.fields[]` obligatoires non gérés par le CRUD simple.

**Comportement après PIVOT-CRUD-002** :

| Cas | Résultat |
|---|---|
| pivot sans `fields[]` | Accepté |
| `pivot.fields[]` tous `nullable: true` | Accepté |
| `pivot.fields[]` sans `nullable` ni `required` | Accepté (nullable par défaut) |
| `pivot.fields[]` avec `required: true` | **Refusé** — erreur bloquante |
| `pivot.fields[]` avec `nullable: false` | **Refusé** — erreur bloquante |

**Implémentation** : garde-fou dans `forge_cli/entities/crud/relations_loader.py`,
fonction `_load_crud_many_to_many_relations()`. L'erreur est une `ValueError`
capturée par `make_crud()` qui la projette en `SystemExit(1)` avec message clair.

**Tests** : `tests/test_make_crud_pivot_fields_guard.py` — 13 tests.
