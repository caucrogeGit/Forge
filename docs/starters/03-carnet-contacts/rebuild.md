# Reconstruction — Carnet de contacts

Ce fichier reconstruit vite le starter 3 générable : `Ville`, `Contact` et la relation `Contact.ville_id -> Ville.id`.

## 1. Génération automatique

```bash
forge doctor
forge starter:build 3 --dry-run
forge starter:build 3 --init-db
python scripts/seed_villes.py
```

Alias disponibles :

```bash
forge starter:build carnet
forge starter:build carnet-contacts
```

`--force` reconstruit les fichiers du starter et le bloc de routes marqué. À utiliser seulement pour une reconstruction volontaire.

## 2. JSON complets

### `mvc/entities/ville/ville.json`

```json
{
  "format_version": 1,
  "entity": "Ville",
  "table": "ville",
  "description": "Ville de référence pour le carnet de contacts",
  "fields": [
    { "name": "id", "column": "VilleId", "sql_type": "INT", "primary_key": true, "auto_increment": true },
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
  "description": "Contact associé à une ville",
  "fields": [
    { "name": "id", "column": "ContactId", "sql_type": "INT", "primary_key": true, "auto_increment": true },
    { "name": "nom", "sql_type": "VARCHAR(80)", "constraints": { "not_empty": true, "max_length": 80 } },
    { "name": "prenom", "sql_type": "VARCHAR(80)", "constraints": { "not_empty": true, "max_length": 80 } },
    { "name": "email", "sql_type": "VARCHAR(120)", "unique": true, "constraints": { "not_empty": true, "max_length": 120 } },
    { "name": "telephone", "sql_type": "VARCHAR(20)", "nullable": true, "constraints": { "max_length": 20 } },
    { "name": "ville_id", "sql_type": "INT", "nullable": true }
  ]
}
```

## 3. Relations

`mvc/entities/relations.json` :

```json
{
  "format_version": 1,
  "relations": [
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
    }
  ]
}
```

## 4. Routes

```python
# forge-starter:carnet-contacts:start
from mvc.controllers.contact_controller import ContactController
from mvc.controllers.ville_controller import VilleController

with router.group("/contacts", public=True, csrf=False) as g:
    g.add("GET",  "",              ContactController.index,   name="contact_index")
    g.add("GET",  "/new",          ContactController.new,     name="contact_new")
    g.add("POST", "",              ContactController.create,  name="contact_create")
    g.add("GET",  "/{id}",         ContactController.show,    name="contact_show")
    g.add("GET",  "/{id}/edit",    ContactController.edit,    name="contact_edit")
    g.add("POST", "/{id}",         ContactController.update,  name="contact_update")
    g.add("POST", "/{id}/delete",  ContactController.destroy, name="contact_destroy")

with router.group("/villes", public=True, csrf=False) as g:
    g.add("GET", "", VilleController.index, name="ville_index")
# forge-starter:carnet-contacts:end
```

## 5. Fichiers attendus

```text
mvc/entities/ville/
mvc/entities/contact/
mvc/entities/relations.json
mvc/entities/relations.sql
mvc/controllers/contact_controller.py
mvc/controllers/ville_controller.py
mvc/models/contact_model.py
mvc/models/ville_model.py
mvc/forms/contact_form.py
mvc/views/contact/
mvc/views/ville/index.html
scripts/seed_villes.py
```

## 6. Vérification

```bash
forge check:model
forge routes:list
python scripts/seed_villes.py
python app.py
```

Ouvrir :

```text
https://localhost:8000/contacts
https://localhost:8000/villes
```
