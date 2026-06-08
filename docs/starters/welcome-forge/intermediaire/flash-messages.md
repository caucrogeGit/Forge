# Messages flash

Objectif : confirmer une action par un message qui s'affiche **une seule fois**,
à la requête suivante.

**Ce que vous allez apprendre :** le motif **POST-Redirect-GET** complet. Une
action `POST` pose un **message flash** puis **redirige** ; la page cible lit le
flash (`get_flash`, qui le supprime aussitôt) et l'affiche.

## Là où nous en sommes

La modification ré-affiche la page d'édition, et la suppression redirige sans
confirmation. Nous donnons à ces deux écritures un vrai retour utilisateur : un
message de confirmation **one-shot**, posé avant la redirection et affiché sur la
liste.

## L'ajout

Dans `mvc/controllers/note_controller.py`, faites poser un flash par `update` et
`delete` au moment de rediriger, et lisez le flash dans `index`.

```python
from core.security.session import get_flash, get_session, get_session_id


class NoteController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        # … lecture de q, page, notes inchangée …
        session_id, csrf_token = NoteController._start_session(request)
        flash = get_flash(session_id)  # one-shot : disparaît à la lecture
        response = BaseController.render(
            "note/index.html",
            request=request,
            context={
                "notes": notes,
                "q": q,
                "page": page,
                "has_prev": page > 1,
                "has_next": page * PAGE_SIZE < total,
                "csrf_token": csrf_token,
                "flash": flash,
            },
        )
        set_session_cookie(response, session_id)
        return response

    @staticmethod
    def update(request: Request) -> Response:
        record_id = int(request.route("id"))
        content = request.form("content", default="").strip()
        if not content:
            return Response.text("Le contenu est obligatoire.", status=422)
        execute(UPDATE_ONE, (content, record_id))
        return BaseController.redirect("/note", request=request, flash="Note mise à jour.")

    @staticmethod
    def delete(request: Request) -> Response:
        record_id = int(request.route("id"))
        execute(DELETE_ONE, (record_id,))
        return BaseController.redirect("/note", request=request, flash="Note supprimée.")
```

Affichez le flash en tête du bloc `content` de `mvc/views/note/index.html` :

```html
{% if flash %}
<p><strong>{{ flash.message }}</strong></p>
{% endif %}
```

## Votre mvc/routes.py à ce stade

Inchangé : le flash réutilise les routes existantes (aucune route nouvelle).

```python
# mvc/routes.py
from core.http.router import Router
from mvc.controllers.home_controller import HomeController
from mvc.controllers.note_controller import NoteController

router = Router()

with router.group("", public=True) as pub:
    pub.add("GET",  "/", HomeController.index, name="home-index")
    pub.add("GET",  "/note", NoteController.index, name="note-index")
    pub.add("GET",  "/note/edit/{id}", NoteController.edit, name="note-edit")
    pub.add("POST", "/note/update/{id}", NoteController.update, name="note-update")
    pub.add("POST", "/note/delete/{id}", NoteController.delete, name="note-delete")
```

## Comprendre ce code

- `BaseController.redirect("/note", request=request, flash="…")` **pose** le
  message dans la session puis renvoie une redirection : c'est le **P**OST puis le
  **R**edirect du motif POST-Redirect-GET.
- Au **G**ET suivant, `get_flash(get_session_id(request))` lit le message **et le
  supprime** : il ne s'affichera donc qu'une fois, même si on recharge la page.
- `update` ne ré-affiche plus la page d'édition : il redirige vers la liste, état
  réel et partageable.

## Tester dans le navigateur

| Action | Résultat |
|---|---|
| Modifier une note | retour à la liste avec « Note mise à jour. » |
| Recharger la liste | le message a disparu (one-shot) |
| Supprimer une note | retour à la liste avec « Note supprimée. » |

## À retenir

- POST-Redirect-GET : on **redirige** après une écriture, jamais on ne ré-affiche
  directement le POST.
- Un flash est **one-shot** : `get_flash` le lit et le supprime.
- Le flash combine **session** (stockage) et **redirection**.

Au palier suivant, nous mémorisons un état serveur entre les requêtes avec la session.

[Continuer avec Mémoriser un état en session](session-state.md)
