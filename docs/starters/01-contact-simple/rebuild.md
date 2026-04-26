# Reconstruction — Contacts

Recette courte pour reconstruire le starter 1 depuis un projet Forge propre.

---

## 1. Créer le projet

Installation recommandée :

```bash
pipx install git+https://github.com/caucrogeGit/Forge.git
forge new Contacts
cd Contacts
source .venv/bin/activate
forge doctor
```

Alternative manuelle :

```bash
git clone https://github.com/caucrogeGit/Forge.git Contacts
cd Contacts
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
npm install
forge doctor
```

---

## 2. Configurer la base

Dans `env/dev`, adapter au minimum :

```env
DB_NAME=contacts

DB_ADMIN_HOST=localhost
DB_ADMIN_PORT=3306
DB_ADMIN_LOGIN=forge_admin
DB_ADMIN_PWD=ForgeAdmin_2026!

DB_APP_HOST=localhost
DB_APP_PORT=3306
DB_APP_LOGIN=contacts_app
DB_APP_PWD=ContactsApp_2026!
```

Initialiser la base :

```bash
forge db:init
```

---

## 3. Créer l'entité

```bash
forge make:entity Contact --no-input
```

Remplacer ensuite le contenu de :

```text
mvc/entities/contact/contact.json
```

par le JSON ci-dessous.

---

## 4. JSON complet

```json
{
  "format_version": 1,
  "entity": "Contact",
  "table": "contact",
  "description": "Contacts — starter niveau 1",
  "fields": [
    {
      "name": "id",
      "sql_type": "INT",
      "primary_key": true,
      "auto_increment": true
    },
    {
      "name": "nom",
      "sql_type": "VARCHAR(80)",
      "constraints": {
        "not_empty": true,
        "max_length": 80
      }
    },
    {
      "name": "prenom",
      "sql_type": "VARCHAR(80)",
      "constraints": {
        "not_empty": true,
        "max_length": 80
      }
    },
    {
      "name": "email",
      "sql_type": "VARCHAR(120)",
      "unique": true,
      "constraints": {
        "not_empty": true,
        "max_length": 120
      }
    },
    {
      "name": "telephone",
      "sql_type": "VARCHAR(20)",
      "nullable": true,
      "constraints": {
        "max_length": 20
      }
    }
  ]
}
```

---

## 5. Générer le modèle

```bash
forge check:model
forge build:model --dry-run
forge build:model
forge db:apply
```

---

## 6. Générer le CRUD

```bash
forge make:crud Contact --dry-run
forge make:crud Contact
```

---

## 7. Copier les routes

Ajouter dans `mvc/routes.py` :

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

Pour un test local sans authentification applicative :

```python
with router.group("/contacts", public=True, csrf=False) as g:
    ...
```

La route `/new` doit rester avant `/{id}`.

---

## 8. Fichiers attendus

```text
mvc/entities/contact/contact.json
mvc/entities/contact/contact.sql
mvc/entities/contact/contact_base.py
mvc/entities/contact/contact.py
mvc/entities/contact/__init__.py

mvc/controllers/contact_controller.py
mvc/models/contact_model.py
mvc/forms/contact_form.py
mvc/views/layouts/app.html
mvc/views/contact/index.html
mvc/views/contact/show.html
mvc/views/contact/form.html

mvc/routes.py
```

---

## 9. Vérifier

```bash
forge doctor
forge check:model
forge routes:list
python app.py
```

Ouvrir :

```text
https://localhost:8000/contacts
```

Test rapide : créer, afficher, modifier puis supprimer un contact.
