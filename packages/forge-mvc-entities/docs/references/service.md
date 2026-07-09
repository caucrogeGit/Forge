# Le service pivot dans Forge

Ce document décrit `PivotAdvancedService`, le service de persistance des associations pivot enrichies, ainsi que ses contraintes et ses erreurs.

Le fichier de code correspondant est `forge_mvc_entities/service.py`.

## 1. À quoi sert ce module ?

Une table pivot `many_to_many` peut porter des **attributs métier** propres à l'association (`position`, `note`, `role`…).
`PivotAdvancedService` lit et écrit ces associations, en appliquant les contraintes déclarées et en produisant des erreurs UX stables.

## 2. Import

```python
from forge_mvc_entities import (
    PivotAdvancedService,
    PivotFieldConstraint,
    PivotConstraintError,
    PivotFormError,
    pivot_error_to_form_error,
)
```

## 3. Instancier le service

Sans contraintes (API simple) :

```python
service = PivotAdvancedService(
    table="article_tag",
    source_key="article_id",
    target_key="tag_id",
    pivot_fields=["position", "note"],
)
```

En production, le service délègue automatiquement aux helpers `core.database.db`.
Les paramètres `fetch_one`, `fetch_all`, `execute`, `insert_fn` sont optionnels et destinés aux tests.

Avec contraintes :

```python
service = PivotAdvancedService(
    table="article_tag",
    source_key="article_id",
    target_key="tag_id",
    pivot_constraints=[
        PivotFieldConstraint("position", required=True, nullable=False),
        PivotFieldConstraint("note", required=False, nullable=True),
    ],
    unique_pair=True,
    id_field="id",
)
```

## 4. Les méthodes principales

```python
rows = service.list_for_source(article_id)                       # liste de PivotRow
row  = service.get(article_id, tag_id)                           # PivotRow ou None
pid  = service.attach(article_id, tag_id, {"position": 1})       # lastrowid
service.update(article_id, tag_id, {"note": "Mis à jour"})       # rowcount
service.detach(article_id, tag_id)                               # rowcount
```

## 5. Les méthodes par id technique

```python
row = service.get_by_id(pivot_id)
service.update_by_id(pivot_id, {"note": "Nouveau"})
service.delete_by_id(pivot_id)
```

Elles requièrent `id_field="id"` à l'instanciation ; sans lui, elles lèvent `PivotConstraintError(code="missing_id_field")`.

## 6. L'objet `PivotRow`

```python
row.source_id    # article_id
row.target_id    # tag_id
row.pivot_data   # dict, ex. {"id": 1, "position": 2, "note": "..."}
```

## 7. Les contraintes (`PivotFieldConstraint`)

Déclarées dans le constructeur, elles s'appliquent à `attach` et `update`.

- **required** : `PivotFieldConstraint("position", required=True)` exige le champ lors d'un `attach` ; `required` n'est **pas** vérifié lors d'un `update` (mise à jour partielle autorisée).
- **nullable** : `PivotFieldConstraint("position", nullable=False)` refuse la valeur `None` dans `attach` et `update`.
- **unique_pair** : avec `unique_pair=True`, chaque `attach` vérifie que la paire `(source_id, target_id)` n'existe pas déjà, sinon `PivotConstraintError(code="duplicate_pair")`.
- **id_field** : `id_field="id"` active les méthodes `*_by_id`.

## 8. Les erreurs UX

Codes d'erreur stables :

| Code | Cas |
|---|---|
| `required_field_missing` | champ `required=True` absent lors d'un `attach` |
| `nullable_field_rejected` | champ `nullable=False` reçoit `None` |
| `duplicate_pair` | association déjà existante avec `unique_pair=True` |
| `missing_id_field` | appel `*_by_id` sans `id_field` configuré |
| `unknown_pivot_field` | champ inconnu dans `pivot_data` |
| `invalid_pivot_data` | toute autre erreur inattendue |

Conversion en erreur de formulaire :

```python
try:
    service.attach(article_id, tag_id, pivot_data)
except Exception as exc:
    error = pivot_error_to_form_error(exc)
    return render("form.html", error=error)
```

`pivot_error_to_form_error` retourne un `PivotFormError` (`error.code`, `error.message`, `error.field`).
Il ne divulgue jamais de détail SQL : une erreur inconnue produit un message générique.

## 9. Contextes d'utilisation

- **Contrôleur pivot** : `attach` / `update` / `detach` derrière un `try/except` converti en `PivotFormError`.
- **Vue liste** : `list_for_source(source_id)` pour afficher les associations.
- **Tests** : injecter `fetch_one` / `execute` pour piloter le service sans base réelle.

## 10. Voir aussi

- [Le générateur de sous-CRUD pivot](make_pivot_crud.md) : `make:pivot-crud` et `relations.json`.
- [Vue d'ensemble Pivot advanced](../reference.md).
