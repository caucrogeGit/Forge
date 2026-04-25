# Reconstruction — Carnet relationnel

Ce fichier reconstruit le starter relationnel `Ville`, `Contact`, `Groupe`, `ContactGroupe`.

## 1. Commandes Forge

```bash
forge doctor
forge db:init
forge make:entity Ville --no-input
forge make:entity Contact --no-input
forge make:entity Groupe --no-input
forge make:entity ContactGroupe --no-input
```

Remplacez les JSON générés par les modèles ci-dessous.

```bash
forge build:model --dry-run
forge build:model
forge make:relation
forge make:relation
forge make:relation
forge sync:relations
forge check:model
forge db:apply
forge make:crud Contact
forge make:crud Ville
forge make:crud Groupe
```

## 2. JSON complets

### `mvc/entities/ville/ville.json`

```json
{
  "format_version": 1,
  "entity": "Ville",
  "table": "ville",
  "fields": [
    { "name": "id", "sql_type": "INT", "primary_key": true, "auto_increment": true },
    { "name": "nom", "sql_type": "VARCHAR(100)", "constraints": { "not_empty": true, "max_length": 100 } },
    { "name": "code_postal", "sql_type": "VARCHAR(10)", "nullable": true, "constraints": { "max_length": 10 } }
  ]
}
```

### `mvc/entities/contact/contact.json`

```json
{
  "format_version": 1,
  "entity": "Contact",
  "table": "contact",
  "fields": [
    { "name": "id", "sql_type": "INT", "primary_key": true, "auto_increment": true },
    { "name": "ville_id", "sql_type": "INT", "nullable": true },
    { "name": "nom", "sql_type": "VARCHAR(80)", "constraints": { "not_empty": true, "max_length": 80 } },
    { "name": "prenom", "sql_type": "VARCHAR(80)", "constraints": { "not_empty": true, "max_length": 80 } },
    { "name": "email", "sql_type": "VARCHAR(120)", "nullable": true, "unique": true }
  ]
}
```

### `mvc/entities/groupe/groupe.json`

```json
{
  "format_version": 1,
  "entity": "Groupe",
  "table": "groupe",
  "fields": [
    { "name": "id", "sql_type": "INT", "primary_key": true, "auto_increment": true },
    { "name": "libelle", "sql_type": "VARCHAR(80)", "constraints": { "not_empty": true, "max_length": 80 } }
  ]
}
```

### `mvc/entities/contact_groupe/contact_groupe.json`

```json
{
  "format_version": 1,
  "entity": "ContactGroupe",
  "table": "contact_groupe",
  "fields": [
    { "name": "id", "sql_type": "INT", "primary_key": true, "auto_increment": true },
    { "name": "contact_id", "sql_type": "INT" },
    { "name": "groupe_id", "sql_type": "INT" }
  ]
}
```

## 3. Relations à déclarer

Dans `mvc/entities/relations.json`, les trois relations attendues sont :

```json
[
  {
    "name": "contact_ville",
    "type": "many_to_one",
    "from_entity": "Contact",
    "to_entity": "Ville",
    "from_field": "ville_id",
    "to_field": "id",
    "foreign_key_name": "fk_contact_ville",
    "on_delete": "SET NULL",
    "on_update": "CASCADE"
  },
  {
    "name": "contact_groupe_contact",
    "type": "many_to_one",
    "from_entity": "ContactGroupe",
    "to_entity": "Contact",
    "from_field": "contact_id",
    "to_field": "id",
    "foreign_key_name": "fk_contact_groupe_contact",
    "on_delete": "CASCADE",
    "on_update": "CASCADE"
  },
  {
    "name": "contact_groupe_groupe",
    "type": "many_to_one",
    "from_entity": "ContactGroupe",
    "to_entity": "Groupe",
    "from_field": "groupe_id",
    "to_field": "id",
    "foreign_key_name": "fk_contact_groupe_groupe",
    "on_delete": "CASCADE",
    "on_update": "CASCADE"
  }
]
```

## 4. Routes à copier

Copiez les routes affichées par `forge make:crud` pour `Contact`, `Ville` et `Groupe`.

Exemple pour `Contact` :

```python
from mvc.controllers.contact_controller import ContactController

with router.group("/contacts") as g:
    g.add("GET",  "",              ContactController.index,   name="contact_index")
    g.add("GET",  "/new",          ContactController.new,     name="contact_new")
    g.add("POST", "",              ContactController.create,  name="contact_create")
    g.add("GET",  "/{id}",         ContactController.show,    name="contact_show")
    g.add("GET",  "/{id}/edit",    ContactController.edit,    name="contact_edit")
    g.add("POST", "/{id}",         ContactController.update,  name="contact_update")
    g.add("POST", "/{id}/delete",  ContactController.destroy, name="contact_destroy")
```

Ajoutez ensuite vos routes relationnelles manuelles :

```python
from mvc.controllers.carnet_controller import CarnetController

with router.group("/carnet") as g:
    g.add("GET", "/contacts/{id}", CarnetController.contact_detail, name="carnet_contact_detail")
    g.add("GET", "/villes/{id}", CarnetController.ville_detail, name="carnet_ville_detail")
    g.add("GET", "/groupes/{id}", CarnetController.groupe_detail, name="carnet_groupe_detail")
```

## 5. Fichiers à créer ou modifier

Générés :

```text
mvc/entities/*/*.sql
mvc/entities/*/*_base.py
mvc/entities/relations.sql
mvc/controllers/contact_controller.py
mvc/controllers/ville_controller.py
mvc/controllers/groupe_controller.py
mvc/models/contact_model.py
mvc/models/ville_model.py
mvc/models/groupe_model.py
mvc/forms/contact_form.py
mvc/forms/ville_form.py
mvc/forms/groupe_form.py
```

Manuels :

```text
mvc/entities/*/*.json
mvc/entities/relations.json
mvc/models/carnet_model.py
mvc/controllers/carnet_controller.py
mvc/views/carnet/contact_detail.html
mvc/views/carnet/ville_detail.html
mvc/views/carnet/groupe_detail.html
mvc/routes.py
```

## 6. Vérifications

```bash
forge check:model
python app.py
```

Vérifiez dans la base que `Contact.ville_id` accepte `NULL`, car la relation utilise `SET NULL`.

## 7. Test navigateur

1. Créer deux villes.
2. Créer trois contacts, dont un sans ville.
3. Créer deux groupes.
4. Ajouter des lignes dans `contact_groupe`.
5. Ouvrir la liste des contacts.
6. Vérifier le détail relationnel d’un contact.
7. Vérifier les contacts d’une ville.
8. Vérifier les contacts d’un groupe.

## 8. Points pédagogiques

- Le pivot est une entité explicite.
- Les vues relationnelles restent du code applicatif.
- Les `JOIN` SQL sont visibles.
- Forge ne masque pas les relations derrière un ORM.
