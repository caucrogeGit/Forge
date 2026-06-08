# Modifier un enregistrement

Objectif : éditer une note existante via un formulaire pré-rempli.

**Ce que vous allez apprendre :** la première **écriture** du niveau. Le
formulaire est chargé avec la valeur courante (`fetch_one`), puis l'enregistrement
passe par `core.database.db.execute("UPDATE … WHERE id = ?")`, en POST
**protégé par CSRF**.

## Là où nous en sommes

Jusqu'ici, le Carnet de notes est en **lecture seule** : lister, rechercher,
paginer. Nous ajoutons la première écriture. C'est un nouveau besoin (un
formulaire, une route POST, du CSRF), donc deux nouvelles méthodes sur
`NoteController` et **deux nouvelles routes**.

## L'ajout

Complétez les imports et ajoutez les deux requêtes plus les deux méthodes dans
`mvc/controllers/note_controller.py` :

```python
from core.database.db import execute, fetch_all, fetch_one

SELECT_ONE = "SELECT id, content FROM notes WHERE id = ?"
UPDATE_ONE = "UPDATE notes SET content = ? WHERE id = ?"


class NoteController(BaseController):

    # … index(...) inchangé …

    @staticmethod
    def edit(request: Request) -> Response:
        record_id = int(request.route("id"))
        note = fetch_one(SELECT_ONE, (record_id,))
        if note is None:
            return Response.text("Note introuvable.", status=404)
        return BaseController.render(
            "note/edit.html",
            request=request,
            context={"note": note, "csrf_token": BaseController.csrf_token(request)},
        )

    @staticmethod
    def update(request: Request) -> Response:
        record_id = int(request.route("id"))
        content = request.form("content", default="").strip()
        if not content:
            return Response.text("Le contenu est obligatoire.", status=422)
        execute(UPDATE_ONE, (content, record_id))
        return BaseController.render(
            "note/edit.html",
            request=request,
            context={
                "note": {"id": record_id, "content": content},
                "csrf_token": BaseController.csrf_token(request),
                "updated": True,
            },
        )
```

Créez la vue `mvc/views/note/edit.html` :

```html
<!-- mvc/views/note/edit.html -->
{% extends "note/_layout.html" %}

{% block title %}Modifier la note #{{ note.id }}{% endblock %}

{% block content %}
<h1>Modifier la note #{{ note.id }}</h1>

{% if updated %}<p><strong>Note mise à jour.</strong></p>{% endif %}

<form method="post" action="/notes/{{ note.id }}/edit">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <input type="text" name="content" value="{{ note.content }}">
    <button type="submit">Enregistrer</button>
</form>

<p><a href="/notes">Retour à la liste</a></p>
{% endblock %}
```

Ajoutez aussi un lien « éditer » sur chaque note de la liste, dans
`mvc/views/note/index.html` :

```html
<li>#{{ note.id }} : {{ note.content }}
    <a href="/notes/{{ note.id }}/edit">éditer</a></li>
```

Puis déclarez les deux routes dans `mvc/routes.py`.

## Votre mvc/routes.py à ce stade

```python
# mvc/routes.py
from core.http.router import Router
from mvc.controllers.home_controller import HomeController
from mvc.controllers.note_controller import NoteController

router = Router()

with router.group("", public=True) as pub:
    pub.add("GET",  "/", HomeController.index, name="home_index")
    pub.add("GET",  "/notes", NoteController.index, name="notes_index")
    pub.add("GET",  "/notes/{id}/edit", NoteController.edit, name="notes_edit")
    pub.add("POST", "/notes/{id}/edit", NoteController.update, name="notes_update")
```

## Comprendre ce code

- `edit` **pré-remplit** le formulaire : on lit la valeur courante avec
  `fetch_one` avant d'afficher le champ, et on renvoie un `404` si l'`id` est
  inconnu.
- `update` valide d'abord (refus `422` si vide), puis `execute(UPDATE_ONE, …)` :
  l'`id` et le contenu sont des **paramètres liés**.
- L'`id` vient de la **route** (`request.route("id")`), pas de la *query string*.
- Le `<form>` est en `method="post"` et embarque le **jeton CSRF** : toute
  écriture est protégée.

## Tester dans le navigateur

| URL | Résultat |
|---|---|
| `https://localhost:8000/notes` | la liste, avec un lien « éditer » par note |
| Éditer une note, changer le texte, Enregistrer | « Note mise à jour. » |
| Soumettre vide | `Le contenu est obligatoire.` (statut `422`) |

## À retenir

- Modifier, c'est pré-remplir (`fetch_one`) plus `UPDATE … WHERE id = ?` paramétré.
- L'`id` vient de la **route** (`request.route("id")`).
- Toute écriture est en `POST` **avec CSRF**.

Au palier suivant, nous ajoutons la suppression d'une note.

[Continuer avec Supprimer un enregistrement](delete-record.md)
