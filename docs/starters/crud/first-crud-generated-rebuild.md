# Reconstruction — First CRUD (généré)

[Accueil](../../index.html){ .md-button }

Recette courte pour reconstruire le starter `first-crud-generated` (CRUD
généré, entité neutre `Message`) depuis un projet Forge propre.

---

## 1. Créer le projet

Installation recommandée :

```bash
pipx install git+https://github.com/caucrogeGit/Forge.git
forge new MonProjet
cd MonProjet
source .venv/bin/activate
forge doctor
```

Alternative manuelle :

```bash
git clone https://github.com/caucrogeGit/Forge.git MonProjet
cd MonProjet
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
DB_NAME=first_crud_generated

DB_ADMIN_HOST=localhost
DB_ADMIN_PORT=3306
DB_ADMIN_LOGIN=forge_admin
DB_ADMIN_PWD=ForgeAdmin_2026!

DB_APP_HOST=localhost
DB_APP_PORT=3306
DB_APP_LOGIN=app_user
DB_APP_PWD=AppUser_2026!
```

Initialiser la base :

```bash
forge db:init
```

---

## 3. Créer l'entité

```bash
forge make:entity Message --no-input
```

Remplacer ensuite le contenu de :

```text
mvc/entities/message/message.json
```

par le JSON ci-dessous.

---

## 4. JSON complet

```json
{
  "schema_version": "1.0",
  "name": "Message",
  "table": "message",
  "description": "Entité neutre — starter first-crud-generated (CRUD généré)",
  "fields": [
    {
      "name": "content",
      "type": "string",
      "max_length": 255,
      "nullable": false
    }
  ],
  "options": {
    "timestamps": false,
    "soft_delete": false
  }
}
```

La clé primaire `id` est ajoutée automatiquement par `forge build:model`.

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
forge make:crud Message --dry-run
forge make:crud Message
```

---

## 7. Copier les routes

Ajouter dans `mvc/routes.py` :

```python
from mvc.controllers.message_controller import MessageController

with router.group("/messages") as g:
    g.add("GET",  "",              MessageController.index,   name="message_index")
    g.add("GET",  "/new",          MessageController.new,     name="message_new")
    g.add("POST", "",              MessageController.create,  name="message_create")
    g.add("GET",  "/{id}",         MessageController.show,    name="message_show")
    g.add("GET",  "/{id}/edit",    MessageController.edit,    name="message_edit")
    g.add("POST", "/{id}",         MessageController.update,  name="message_update")
    g.add("POST", "/{id}/delete",  MessageController.destroy, name="message_destroy")
```

Pour un test local sans authentification applicative :

```python
with router.group("/messages", public=True, csrf=False) as g:
    ...
```

La route `/new` doit rester avant `/{id}`.

---

## 8. Fichiers attendus

```text
mvc/entities/message/message.json
mvc/entities/message/message.sql
mvc/entities/message/message_base.py
mvc/entities/message/message.py
mvc/entities/message/__init__.py

mvc/controllers/message_controller.py
mvc/models/message_model.py
mvc/forms/message_form.py
mvc/views/layouts/app.html
mvc/views/message/index.html
mvc/views/message/show.html
mvc/views/message/form.html

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
https://localhost:8000/messages
```

Test rapide : créer, afficher, modifier puis supprimer un message.
