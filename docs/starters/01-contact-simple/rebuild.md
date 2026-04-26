# Reconstruction — Contact simple

Ce fichier permet de reconstruire le starter 1 depuis un projet Forge propre.

## 1. Commandes Forge

Créer le projet :

```bash
pipx install git+https://github.com/caucrogeGit/Forge.git
forge new Contacts
cd Contacts
source .venv/bin/activate
forge doctor
```

Préparer la base (renseigner `env/dev` avant) :

```bash
forge db:init
```

Créer l'entité :

```bash
forge make:entity Contact --no-input
```

Remplacez ensuite `mvc/entities/contact/contact.json` par le JSON ci-dessous.

```bash
forge build:model --dry-run
forge build:model
forge check:model
forge db:apply
forge make:crud Contact
```

## 2. JSON complet

```json
{
  "format_version": 1,
  "entity": "Contact",
  "table": "contact",
  "description": "Contact simple du starter niveau 1",
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

## 3. Routes à copier

Ajoutez le bloc dans `mvc/routes.py`. La route `/new` doit rester avant `/{id}`.

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

## 4. Fichiers à créer ou modifier

Créé par `make:entity` ou `build:model` :

```text
mvc/entities/contact/contact.json
mvc/entities/contact/contact.sql
mvc/entities/contact/contact_base.py
mvc/entities/contact/contact.py
mvc/entities/contact/__init__.py
```

Créé par `make:crud` si absent :

```text
mvc/controllers/contact_controller.py
mvc/models/contact_model.py
mvc/forms/contact_form.py
mvc/views/layouts/app.html
mvc/views/contact/index.html
mvc/views/contact/show.html
mvc/views/contact/form.html
```

Modifié manuellement :

```text
mvc/routes.py
```

## 5. Vérifications

```bash
forge check:model
forge doctor
forge routes:list
python app.py
```

Ouvrir dans le navigateur :

```text
https://localhost:8000/contacts
```

Vérifiez aussi que `forge make:crud Contact --dry-run` n’écrase aucun fichier existant.

## 6. Test navigateur

1. Ouvrir `/contacts`.
2. Cliquer sur le lien de création.
3. Soumettre le formulaire vide et vérifier les erreurs.
4. Créer un contact valide.
5. Vérifier le flash de succès.
6. Ouvrir le détail.
7. Modifier le contact.
8. Supprimer le contact.
9. Revenir à la liste.

## 7. Points pédagogiques

- `contact.json` est la source canonique.
- `contact.sql` et `contact_base.py` sont régénérables.
- `contact.py` et `__init__.py` sont préservés.
- Le formulaire généré contient un champ CSRF.
- Les routes restent ajoutées manuellement.
