# Pivot advanced — tables pivot avec attributs

## 1. Objectif

Un pivot advanced est une table pivot `many_to_many` qui porte des attributs
métier propres à la relation — `position`, `note`, `role`, `joined_at`, etc.

Ces attributs ne sont ni des colonnes d'entité source ni des colonnes d'entité
cible : ils appartiennent à l'**association elle-même**. Le CRUD standard de
Forge (`make:crud`) ne peut pas les gérer — il synchronise uniquement des paires
d'IDs. Un sous-CRUD relationnel dédié est nécessaire.

Forge fournit :

- `PivotAdvancedService` — service de persistence pour les associations pivot ;
- `make:pivot-crud` — générateur opt-in d'un contrôleur et de templates dédiés.

---

## 2. Quand utiliser Pivot advanced ?

Utilisez Pivot advanced quand une relation `many_to_many` porte des données
métier non nullables ou significatives.

| Cas | Recommandation |
|---|---|
| `pivot.fields[]` vide | `make:crud` suffit — `<select multiple>` d'IDs |
| `pivot.fields[]` avec champs tous nullables et non requis | `make:crud` suffit ; attributs ignorés |
| `pivot.fields[]` avec au moins un champ `required: true` ou `nullable: false` | `make:pivot-crud` obligatoire — `make:crud` est bloqué par le garde-fou |
| `pivot.fields[]` avec attributs métier significatifs | `make:pivot-crud` recommandé |

---

## 3. Exemple complet Article ↔ Tag

Un article peut être associé à plusieurs tags. Chaque association porte :

- `position` — ordre d'affichage dans l'article
- `note` — note éditoriale sur l'association

```
Article ↔ article_tag ↔ Tag

Colonnes de article_tag :
  id          (clé primaire technique)
  article_id  (clé étrangère → Article)
  tag_id      (clé étrangère → Tag)
  position    (attribut de l'association)
  note        (attribut de l'association)
```

`position` et `note` sont des informations **de la relation**, pas de `Article`
ni de `Tag`. Un même tag peut avoir `position=1` pour un article et `position=3`
pour un autre.

---

## 4. Déclarer la relation dans relations.json

```json
{
  "schema_version": "1.0",
  "relations": [
    {
      "type": "many_to_many",
      "from": "Article",
      "to": "Tag",
      "name": "tags",
      "inverse_name": "articles",
      "pivot": {
        "table": "article_tag",
        "from_key": "article_id",
        "to_key": "tag_id",
        "id": true,
        "unique_pair": true,
        "fields": [
          {
            "name": "position",
            "type": "integer",
            "nullable": false
          },
          {
            "name": "note",
            "type": "string",
            "max_length": 120,
            "nullable": true
          }
        ]
      }
    }
  ]
}
```

Points clés :

- `schema_version: "1.0"` est obligatoire.
- `pivot.fields[]` non vide déclenche le besoin d'un sous-CRUD dédié.
- `make:crud` refuse de générer le CRUD si un champ est `required: true` ou
  `nullable: false` — message d'erreur explicite avec suggestion d'utiliser
  `make:pivot-crud`.
- `make:pivot-crud` est la commande dédiée pour ces cas.

Après modification de `relations.json`, relancer :

```bash
python forge.py entity:validate   # valide le contrat
python forge.py build:model       # génère le SQL
```

---

## 5. Générer le sous-CRUD pivot

```bash
python forge.py make:pivot-crud Article tags
python forge.py make:pivot-crud Article tags --dry-run
```

- `Article` — entité source (valeur de `"from"` dans `relations.json`)
- `tags` — nom de la relation (valeur de `"name"` dans `relations.json`)

Comportements :

| Comportement | Description |
|---|---|
| `--dry-run` | Liste les fichiers qui seraient générés sans les écrire |
| Génération | Crée les fichiers si absents (write-if-new) |
| Fichiers existants | Préservés — jamais écrasés |
| Routes | Documentées dans la sortie, **non branchées automatiquement** |
| `make:crud` | Non modifié — reste neutre |

La commande affiche les routes à ajouter manuellement dans `mvc/routes.py`.

---

## 6. Fichiers générés

```
mvc/controllers/pivot/article_tags_pivot_controller.py
mvc/templates/pivot/article_tags/index.html
mvc/templates/pivot/article_tags/form.html
```

### Contrôleur

`article_tags_pivot_controller.py` contient une classe avec six actions :

| Action | Route suggérée |
|---|---|
| `index` | `GET /articles/{id}/tags` |
| `add_form` | `GET /articles/{id}/tags/add` |
| `add` | `POST /articles/{id}/tags/add` |
| `edit_form` | `GET /articles/{id}/tags/{tag_id}/edit` |
| `edit` | `POST /articles/{id}/tags/{tag_id}/edit` |
| `remove` | `POST /articles/{id}/tags/{tag_id}/remove` |

Le contrôleur importe `PivotAdvancedService`, `PivotConstraintError` et
`pivot_error_to_form_error`. Les actions `add` et `edit` intègrent un bloc
`try/except` qui convertit les erreurs de contrainte en `PivotFormError`
transmis au template.

### Templates

`index.html` — tableau listant les associations avec les colonnes pivot.

`form.html` — formulaire d'ajout ou de modification. Affiche le message
d'erreur si `error` est présent dans le contexte :

```html
{% if error %}
<div class="bg-red-50 border border-red-300 text-red-700 px-4 py-3 rounded mb-4">
    {{ error.message }}
</div>
{% endif %}
```

Les templates générés sont une base minimale — adaptez-les selon les besoins
visuels de votre projet.

---

## 7. Utiliser PivotAdvancedService

### Import

```python
from core.pivot_advanced import (
    PivotAdvancedService,
    PivotFieldConstraint,
    PivotConstraintError,
    PivotFormError,
    pivot_error_to_form_error,
)
```

### Instanciation (sans contraintes — API simple)

```python
service = PivotAdvancedService(
    table="article_tag",
    source_key="article_id",
    target_key="tag_id",
    pivot_fields=["position", "note"],
)
```

En production, le service délègue automatiquement aux helpers `core.database.db`.
Les paramètres `fetch_one`, `fetch_all`, `execute`, `insert_fn` sont optionnels
et destinés aux tests.

### Instanciation avec contraintes

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

### Méthodes principales

```python
# Lister toutes les associations d'un article
rows = service.list_for_source(article_id)
# → liste de PivotRow

# Lire une association spécifique
row = service.get(article_id, tag_id)
# → PivotRow ou None

# Créer une association
pivot_id = service.attach(article_id, tag_id, {"position": 1, "note": "Principal"})
# → lastrowid

# Modifier les attributs d'une association
service.update(article_id, tag_id, {"note": "Mis à jour"})
# → rowcount

# Supprimer une association
service.detach(article_id, tag_id)
# → rowcount
```

### Méthodes par id technique (requiert `id_field`)

```python
row = service.get_by_id(pivot_id)
service.update_by_id(pivot_id, {"note": "Nouveau"})
service.delete_by_id(pivot_id)
```

Ces méthodes nécessitent `id_field="id"` lors de l'instanciation. Sans ce
paramètre, elles lèvent `PivotConstraintError(code="missing_id_field")`.

### PivotRow

Chaque résultat est un `PivotRow` :

```python
row.source_id    # article_id
row.target_id    # tag_id
row.pivot_data   # dict : {"id": 1, "position": 2, "note": "..."}
```

---

## 8. Contraintes : required, nullable, unique_pair, id technique

Les contraintes sont déclarées via `PivotFieldConstraint` dans le constructeur.
Elles s'appliquent lors de `attach` et `update`.

### required

```python
PivotFieldConstraint("position", required=True)
```

- `required=True` — le champ doit être présent dans `pivot_data` lors d'un `attach`.
- `required` **n'est pas vérifié** lors d'un `update` — mise à jour partielle autorisée.

### nullable

```python
PivotFieldConstraint("position", nullable=False)
```

- `nullable=False` — la valeur `None` est refusée dans `attach` et `update`.
- Si le champ est absent de `pivot_data` lors d'un `attach`, aucune vérification n'est faite
  (sauf si `required=True`).

### unique_pair

```python
service = PivotAdvancedService(
    ...,
    unique_pair=True,
)
```

- Avant chaque `attach`, le service vérifie que la paire `(source_id, target_id)` n'existe
  pas déjà.
- Si elle existe, `PivotConstraintError(code="duplicate_pair")` est levée.
- Sans `unique_pair=True`, la contrainte UNIQUE de la base de données s'applique directement.

### id technique

```python
service = PivotAdvancedService(
    ...,
    id_field="id",
)
```

Active les méthodes `get_by_id`, `update_by_id`, `delete_by_id`.

---

## 9. Erreurs UX et messages formulaire

### Codes d'erreur stables

| Code | Cas |
|---|---|
| `required_field_missing` | Champ `required=True` absent lors de `attach` |
| `nullable_field_rejected` | Champ `nullable=False` reçoit `None` |
| `duplicate_pair` | Association déjà existante avec `unique_pair=True` |
| `missing_id_field` | Appel `*_by_id` sans `id_field` configuré |
| `unknown_pivot_field` | Champ inconnu dans `pivot_data` |
| `invalid_pivot_data` | Toute autre erreur inattendue |

### Conversion en erreur formulaire

```python
try:
    service.attach(article_id, tag_id, pivot_data)
except Exception as exc:
    error = pivot_error_to_form_error(exc)
    return render("form.html", error=error)
```

`pivot_error_to_form_error` retourne un `PivotFormError` :

```python
error.code     # code stable, ex: "required_field_missing"
error.message  # message humain, ex: "Champ pivot requis absent : 'position'."
error.field    # champ concerné si applicable, ex: "position" ou None
```

La fonction ne divulgue jamais de détail SQL — les erreurs inconnues produisent
un message générique.

### Dans le template

```html
{% if error %}
<div>{{ error.message }}</div>
{% endif %}
```

---

## 10. Ce que Pivot advanced ne fait pas

- Il ne modifie pas `make:crud` — le CRUD d'entité classique reste inchangé.
- Il ne branche pas les routes automatiquement dans `mvc/routes.py`.
- Il ne génère pas de JavaScript avancé (drag & drop, ordre dynamique).
- Il n'intègre pas de logique RBAC.
- Il ne remplace pas la conception métier de votre application.
- Les templates générés sont minimaux — ils sont conçus pour être adaptés.
- Une relation sans `pivot.fields[]` non vide n'a pas besoin de Pivot advanced.

---

## 11. Commandes utiles

```bash
# Valider relations.json
python forge.py entity:validate

# Générer le SQL pivot
python forge.py build:model

# Générer le sous-CRUD (avec confirmation de ce qui sera créé)
python forge.py make:pivot-crud Article tags --dry-run

# Générer le sous-CRUD
python forge.py make:pivot-crud Article tags

# Inspecter les routes existantes
python forge.py routes:list
```

---

## 12. Limites actuelles

- Pivot advanced est **opt-in** — rien n'est généré automatiquement.
- `make:crud` reste **neutre** — il ne lit pas `pivot.fields[]` et ne génère
  aucun écran pivot advanced.
- Les routes du sous-CRUD pivot ne sont **pas branchées automatiquement** dans
  `mvc/routes.py` — elles sont documentées dans la sortie de `make:pivot-crud`.
- Les templates générés (`index.html`, `form.html`) sont **minimaux** — une UX
  finale peut nécessiter des adaptations CSS et structurelles.
- La synchronisation globale destructive (remplacer toutes les associations d'une
  source) n'est pas encore couverte par `PivotAdvancedService` — utilisez
  `detach` puis `attach` pour chaque association.
- L'accès par `id_field` est optionnel et doit être configuré explicitement.

Pour la documentation des tables pivot simples (sans attributs métier),
voir [Tables pivot many-to-many](pivots-many-to-many.md).
