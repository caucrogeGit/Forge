# Décision — UX et modèle d'usage Pivot advanced

**Ticket** : PIVOT-ADVANCED-002-DEFINE-PIVOT-ADVANCED-UX-AND-USAGE-MODEL
**Date** : 2026-05-20
**Statut** : décision rendue — Option C + E retenue

---

## 1. Résumé

L'UX actuelle de `make:crud` pour les relations `many_to_many` repose sur un
`<select multiple>` d'IDs. Cette UX est correcte pour les pivots simples (pas
d'attributs), mais inadaptée dès qu'un pivot porte des données métier
(`position`, `note`, `role`, `joined_at`).

**Décision** : les attributs pivot sont exposés dans un **écran relationnel
dédié**, séparé du formulaire CRUD principal. Cet écran sera produit par un
générateur ou une commande dédiée (PIVOT-ADVANCED-004). `make:crud` reste neutre.

---

## 2. Contexte

### Tickets précédents

- **PIVOT-CRUD-001** — `make:crud` n'expose pas `pivot.fields[]`. Décision de
  ne pas l'intégrer dans le CRUD core.
- **PIVOT-CRUD-002** — Garde-fou : `make:crud` refuse les champs pivot
  `NOT NULL` sans default, avec message explicite.
- **PIVOT-ADVANCED-001** — Modèle fonctionnel défini : Pivot advanced =
  sous-CRUD relationnel dédié. Option C + D retenue (service + commande).

### Contrainte structurelle confirmée

`CrudManyToManyRelation` (dans `forge_cli/entities/crud/context.py`) n'a pas
d'attribut `pivot_fields`. Les informations de `pivot.fields[]` sont éliminées
dans `_load_crud_many_to_many_relations()` de `relations_loader.py` avant que
le pipeline CRUD ne s'exécute.

Toute extension UX dans `make:crud` nécessiterait une refonte de cette structure —
ce qui est hors périmètre et contraire à la décision PIVOT-ADVANCED-001.

---

## 3. Méthode d'audit

### Commandes exécutées

```bash
git status
python forge.py schema:list                                # 6 schémas OK
python forge.py schema:doctor                              # OK
python forge.py entity:validate                            # OK
python forge.py build:model                                # OK
pytest tests/test_make_crud_many_to_many_canonical.py -q   # 5 passed
pytest tests/test_make_crud_pivot_fields_guard.py -q        # 32 passed
pytest tests/test_pivot_fields_controlled.py -q            # 36 passed
pytest tests/meta/test_pivot_advanced_functional_model_001.py -q  # 17 passed
```

### Zones auditées

- `forge_cli/entities/crud/context.py` — `CrudManyToManyRelation` (sans `pivot_fields`)
- `forge_cli/entities/crud/views_builder.py` — `build_list_view`, `build_show_view`,
  `build_form_view` — génération UX actuelle des M2M
- `forge_cli/entities/crud/model_builder.py` — `sync_function` (IDs seuls)
- `forge_cli/entities/crud/relations_loader.py` — point d'élimination de `pivot_fields`

---

## 4. UX actuelle many_to_many

### Vue liste (`build_list_view`)

Les relations M2M apparaissent comme une colonne affichant les labels joints :

```html
<td class="px-4 py-3 text-gray-800">
    {{ _tag_labels | join(", ") if _tag_labels else "—" }}
</td>
```

Résultat affiché : `Python, Web` — les attributs pivot (`position`, `note`) sont absents.

### Vue détail (`build_show_view`)

Même logique : les M2M sont affichés comme liste de labels joints.

```html
{% if article_tags_labels %}
<p class="text-gray-800">{{ article_tags_labels | join(", ") }}</p>
{% else %}
<p class="text-gray-400 italic">Aucun Tag</p>
{% endif %}
```

Les attributs pivot ne sont pas accessibles dans le contexte de la vue.

### Formulaire (`build_form_view`)

Un `<select multiple>` pour les IDs uniquement :

```html
<select name="tags" multiple class="...">
    {% for value, label in tag_choices %}
    <option value="{{ value }}"
        {{ 'selected' if value in tags_selected else '' }}>
        {{ label }}
    </option>
    {% endfor %}
</select>
```

Aucun champ pour `position`, `note` ou autre attribut pivot.

### Synchronisation (`model_builder.py`)

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

`position` et `note` ne sont ni passés ni insérés. Si `position INT NOT NULL`,
la requête échoue à l'exécution (le garde-fou PIVOT-CRUD-002 bloque avant).

---

## 5. Problème UX avec pivot.fields[]

### 5.1 Problème de saisie

Le `<select multiple>` ne peut pas recevoir d'attributs supplémentaires par
association. Chaque `<option>` représente un ID cible — il n'y a pas de
mécanisme naturel pour y adjoindre `position=1, note="Principal"`.

Pour saisir les attributs d'une association, il faudrait soit :
- un formulaire HTML structurellement différent (liste de paires avec champs) ;
- plusieurs requêtes distinctes (créer l'association, puis la compléter) ;
- un sous-formulaire par association.

Aucun de ces patterns n'est compatible avec la logique actuelle de `make:crud`.

### 5.2 Problème d'affichage

Les vues `list` et `show` affichent uniquement les labels (`join(", ")`). Un
pivot avec `position` et `note` ne peut pas les afficher dans ce format.

Un tableau `Tag | Position | Note | Actions` nécessite une vue dédiée.

### 5.3 Problème d'identification

La synchronisation actuelle (`DELETE + INSERT`) est destructive : elle supprime
toutes les associations existantes et les recrée. Avec des attributs pivot, ce
modèle est inacceptable — les données métier de chaque association seraient
perdues à chaque synchronisation.

Un pivot advanced nécessite un modèle `INSERT` / `UPDATE` / `DELETE` ciblé
sur une association individuelle.

---

## 6. Options étudiées

| Option | Description | Verdict |
|---|---|---|
| **A — Formulaire CRUD principal** | Ajouter les champs pivot dans le formulaire de l'entité source | **Rejeté** — UX confuse, couplage fort, non générique |
| **B — Tableau inline dans la page parent** | Section expandable dans `show` ou `edit` avec gestion pivot | Possible mais complexe ; risque de surcharge de la vue principale |
| **C — Écran relationnel dédié** | Page séparée `/articles/12/tags` avec son propre CRUD pivot | **Retenu** — découplé, clair, extensible |
| **D — Entité pivot explicite** | Forcer l'utilisateur à créer `ArticleTag` comme entité classique | Rejeté — casse le modèle déclaratif, surcharge le développeur |
| **E — Commande/générateur dédié** | `make:pivot-crud` génère les routes et vues pour un pivot donné | **Retenu** — opt-in, cohérent avec Option C |

### Pourquoi A est rejeté

Dans le formulaire `Article`, ajouter une section pour gérer les associations
`article_tag` avec leurs attributs revient à imbriquer un CRUD dans un CRUD.
L'UX devient difficile à comprendre, le formulaire difficile à valider, et la
logique de contrôleur explose en complexité. Ce n'est pas de l'UX, c'est du
couplage.

### Pourquoi B est insuffisant seul

Le tableau inline (section dans `show`) peut fonctionner pour la **lecture** mais
pose des problèmes pour la **saisie** : les formulaires imbriqués en HTML sont
techniquement délicats, et la validation des erreurs pivot dans un formulaire
parent est mal définie. B peut servir comme composant dans C.

### Pourquoi C + E est retenu

Un écran dédié `/articles/{id}/tags` :
- est une URL claire, bookmarkable, directement accessible ;
- peut afficher un tableau complet (Tag, Position, Note, Actions) ;
- a son propre formulaire d'ajout, simple et ciblé ;
- a son propre contrôleur, indépendant du CRUD Article ;
- est généré en opt-in par une commande, pas automatiquement.

---

## 7. Décision retenue

**Option C + E retenue : écran relationnel dédié, généré par une commande dédiée.**

`make:crud` reste **neutre** — il ne génère aucun écran pivot advanced.

### UX cible

L'écran pivot advanced est une page secondaire liée à une entité source :

```
GET  /articles/{article_id}/tags           — liste des associations
GET  /articles/{article_id}/tags/add       — formulaire d'ajout
POST /articles/{article_id}/tags/add       — créer l'association
GET  /articles/{article_id}/tags/{tag_id}/edit    — formulaire de modification
POST /articles/{article_id}/tags/{tag_id}/edit    — modifier les attributs
POST /articles/{article_id}/tags/{tag_id}/remove  — supprimer l'association
```

La conception exacte des routes est décidée dans PIVOT-ADVANCED-004.

---

## 8. Modèle d'usage cible

### Flux recommandé

1. Le CRUD principal Article reste inchangé — formulaire simple, `<select multiple>` pour les IDs.
2. Une commande dédiée (`make:pivot-crud` ou équivalent) génère l'écran relationnel pour une relation pivot donnée.
3. L'écran pivot advanced est lié à l'entité source via une route paramétrée.
4. Les actions pivot (ajouter, modifier, supprimer une association) passent par `PivotAdvancedService`.
5. Les erreurs `required` / `nullable` / `unique_pair` sont gérées dans ce sous-CRUD dédié.

### Vue minimale cible : liste des associations

```
Article #12 — Tags associés

┌─────────┬──────────┬─────────────┬─────────────────────────┐
│ Tag     │ Position │ Note        │ Actions                 │
├─────────┼──────────┼─────────────┼─────────────────────────┤
│ Python  │ 1        │ Principal   │ Modifier  |  Retirer    │
│ Web     │ 2        │ Secondaire  │ Modifier  |  Retirer    │
└─────────┴──────────┴─────────────┴─────────────────────────┘

[Ajouter un tag]
```

### Actions UX cibles

| Action | UX cible |
|---|---|
| Lire les associations | Tableau dédié avec toutes les colonnes pivot |
| Ajouter une association | Formulaire `<select>` (cible) + champs attributs pivot |
| Modifier les attributs pivot | Formulaire de modification avec champs pré-remplis |
| Supprimer une association | Bouton/formulaire de suppression ciblé |
| Gérer les erreurs | Messages d'erreur dans le formulaire dédié (pas dans le CRUD principal) |

### Ce que cette UX ne fait pas

- Elle ne modifie pas le formulaire principal de l'entité source.
- Elle n'est pas générée automatiquement pour toutes les relations.
- Elle ne fait pas de synchronisation globale destructive.
- Elle n'inclut pas de drag & drop ou d'interface JavaScript avancée à ce stade.
- Elle n'intègre pas de logique RBAC dans ce bloc.

---

## 9. Hors périmètre

Ce ticket (PIVOT-ADVANCED-002) est une décision UX uniquement.

Sont hors périmètre :

- l'implémentation de `PivotAdvancedService` (PIVOT-ADVANCED-003)
- la création des routes, contrôleurs et vues pivot (PIVOT-ADVANCED-004)
- la gestion détaillée des contraintes `required` / `nullable` / `unique_pair` (PIVOT-ADVANCED-006)
- la gestion UX des erreurs de validation pivot (PIVOT-ADVANCED-007)
- toute modification de `make:crud`, `relations_loader.py`, `views_builder.py`
- toute modification des schémas JSON
- toute publication PyPI ou création de tag

---

## 10. Tickets futurs proposés

| Ticket | Objectif |
|---|---|
| **PIVOT-ADVANCED-003** | Créer `PivotAdvancedService` — attach, detach, update, list_for_source, get |
| **PIVOT-ADVANCED-004** | Créer la commande/générateur dédié — routes, contrôleur, vues pivot advanced |
| **PIVOT-ADVANCED-005** | Tests E2E pivot advanced — parcours complets avec attributs |
| **PIVOT-ADVANCED-006** | Gestion des contraintes `required`, `nullable`, `unique_pair`, `id` technique |
| **PIVOT-ADVANCED-007** | Gestion UX des erreurs de validation pivot dans les formulaires dédiés |
| **PIVOT-ADVANCED-008** | Documentation complète + exemples réels |
| **PIVOT-ADVANCED-CLOSE-001** | Clôturer le bloc pivot advanced |

---

**Note PIVOT-ADVANCED-003** : le service technique `PivotAdvancedService`
existe désormais dans `core/pivot_advanced.py`. L'UX décrite dans ce document
n'est pas encore générée — les vues, routes et contrôleurs pivot advanced
seront produits par la commande/générateur décidée ici (PIVOT-ADVANCED-004).

**Note PIVOT-ADVANCED-005** : les tests E2E confirment que l'écran relationnel
dédié reste un flux opt-in — les fichiers sont générés par `make:pivot-crud`,
sans modification de `make:crud`. Le cycle `PivotAdvancedService` est validé
sur SQLite in-memory.

**Note PIVOT-ADVANCED-004** : la commande `forge make:pivot-crud` est ajoutée.
Elle génère un contrôleur dédié et deux templates (`index.html`, `form.html`)
pour un pivot avec `pivot.fields[]`. Les routes ne sont pas branchées
automatiquement — elles sont documentées dans la sortie de la commande.

**Note PIVOT-ADVANCED-006** : les contraintes pivot sont applicables via
`PivotFieldConstraint` et `pivot_constraints=[...]` dans `PivotAdvancedService`.
`unique_pair=True` vérifie l'unicité avant INSERT. `id_field="id"` active les
méthodes `get_by_id`, `update_by_id`, `delete_by_id`. L'API `pivot_fields=[...]`
reste inchangée.

**Note PIVOT-ADVANCED-007** : le sous-CRUD pivot dispose désormais d'un modèle
d'erreur affichable dans les formulaires générés. `PivotFormError(code, message, field)`
est la structure stable. `pivot_error_to_form_error(exc)` convertit toute exception
du service en erreur formulaire sans exposer de détail SQL. Le contrôleur généré
intègre les blocs `try/except` avec passage de l'erreur au template. Le template
`form.html` généré affiche `error.message` dans un bloc conditionnel. `make:crud`
reste neutre.

**Note PIVOT-ADVANCED-008** : la documentation complète d'usage est disponible dans
`docs/entities/pivot-advanced.md`. Elle couvre le contrat `relations.json`, la commande
`make:pivot-crud`, `PivotAdvancedService`, les contraintes, les erreurs UX et les limites.

---

## Clôture — PIVOT-ADVANCED-CLOSE-001

Le modèle UX Pivot advanced est clôturé.

La décision initiale est conservée :

- écran relationnel dédié ;
- commande opt-in `make:pivot-crud` ;
- templates minimaux ;
- routes manuelles ;
- `make:crud` neutre.
