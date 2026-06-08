# Supprimer un enregistrement

Objectif : supprimer une note via une action **destructive sécurisée**.

**Ce que vous allez apprendre :** une suppression ne se fait **jamais** par un
simple lien `GET` : elle passe par un **POST protégé par CSRF** et
`core.database.db.execute("DELETE … WHERE id = ?")`, puis une redirection vers la
liste (motif POST-Redirect-GET).

## Là où nous en sommes

Le Carnet de notes sait lister et modifier. Nous complétons par la suppression.
La liste affiche déjà un lien « éditer » par note ; nous y ajoutons un bouton
« supprimer ». Comme la liste portera désormais un formulaire, `index` doit lui
fournir un **jeton CSRF**.

## L'ajout

Ajoutez la requête et la méthode `delete` dans `mvc/controllers/note_controller.py`,
et complétez le contexte de `index` avec le jeton CSRF :

```python
DELETE_ONE = "DELETE FROM notes WHERE id = ?"


class NoteController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        # … lecture de q, page, notes inchangée …
        return BaseController.render(
            "note/index.html",
            request=request,
            context={
                "notes": notes,
                "q": q,
                "page": page,
                "has_prev": page > 1,
                "has_next": page * PAGE_SIZE < total,
                "csrf_token": BaseController.csrf_token(request),
            },
        )

    @staticmethod
    def delete(request: Request) -> Response:
        record_id = int(request.route("id"))
        execute(DELETE_ONE, (record_id,))
        return BaseController.redirect("/notes")
```

Dans `mvc/views/note/index.html`, ajoutez le bouton de suppression à côté du lien
« éditer » de chaque note :

```html
<li>#{{ note.id }} : {{ note.content }}
    <a href="/notes/{{ note.id }}/edit">éditer</a>
    <form method="post" action="/notes/{{ note.id }}/delete" style="display:inline">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <button type="submit">supprimer</button>
    </form>
</li>
```

Puis déclarez la route de suppression dans `mvc/routes.py`.

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
    pub.add("POST", "/notes/{id}/delete", NoteController.delete, name="notes_delete")
```

## Comprendre ce code

- La suppression est un **POST** : une action qui modifie l'état n'est jamais un
  `GET` (un lien ou un robot ne doivent pas pouvoir supprimer).
- Chaque ligne porte son **propre mini-formulaire** `POST` vers
  `/notes/{id}/delete` avec le **jeton CSRF**.
- `execute(DELETE_ONE, (record_id,))` : l'`id` est un **paramètre lié**.
- Après l'écriture, `redirect("/notes")` renvoie vers la liste : le navigateur
  recharge l'état réel par un `GET` (motif POST-Redirect-GET).

## Tester dans le navigateur

| URL | Résultat |
|---|---|
| `https://localhost:8000/notes` | la liste, avec « éditer » et « supprimer » par note |
| Cliquer « supprimer » | la note disparaît, la liste se recharge |

## À retenir

- Supprimer, c'est `POST` plus CSRF plus `DELETE … WHERE id = ?` paramétré.
- Une action qui change l'état n'est **jamais** un `GET`.
- Après l'écriture, on **redirige** vers la liste (POST-Redirect-GET).

Au palier suivant, nous confirmons ces actions par un message flash.

[Continuer avec Messages flash](flash-messages.md)
