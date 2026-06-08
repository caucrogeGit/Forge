# Mémoriser un état en session

Objectif : mémoriser un état côté serveur **entre** les requêtes.

**Ce que vous allez apprendre :** une requête HTTP est *sans mémoire* : le serveur
oublie tout d'une requête à l'autre. La **session** garde un état rattaché à
l'utilisateur via un cookie `session_id`. Ce palier compte les visites de la liste.

## Là où nous en sommes

Le flash du palier précédent stockait déjà un message dans la session. Nous y
écrivons maintenant **notre propre** état : un compteur de visites, lu et
incrémenté à chaque affichage de la liste.

## L'ajout

Complétez les imports et faites évoluer `index` dans
`mvc/controllers/note_controller.py` pour lire, incrémenter et réécrire le
compteur, puis poser un cookie de session durci :

```python
from core.security.session import get_flash, get_session, get_session_id
from core.sessions.manager import get_session_store


class NoteController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        # … lecture de q, page, notes inchangée …

        session_id, csrf_token = NoteController._start_session(request)
        flash = get_flash(session_id)
        store = get_session_store()
        session = get_session(session_id)
        visits = int(session.get("visits", 0)) + 1
        store.set(session_id, {"visits": visits})

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
                "visits": visits,
            },
        )
        set_session_cookie(response, session_id)
        return response
```

Affichez le compteur dans le bloc `content` de `mvc/views/note/index.html` :

```html
<p><small>Vous avez consulté cette liste {{ visits }} fois.</small></p>
```

## Votre mvc/routes.py à ce stade

Inchangé : le compteur vit dans la session, pas dans une route nouvelle.

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

- `get_session_id(request)` lit le cookie ; `get_session(session_id)` renvoie le
  dictionnaire de session (ou `None`).
- S'il n'y a pas encore de session, on en **crée** une (`store.create()`).
- `store.set(session_id, {"visits": visits})` **fusionne** la nouvelle valeur
  dans la session, sans écraser le reste (csrf, flash).
- Le cookie `session_id` est posé avec des attributs **durcis** : `HttpOnly`
  (pas accessible en JS), `SameSite=Strict`, `Secure` (HTTPS uniquement).

## Tester dans le navigateur

| Action | Résultat |
|---|---|
| Ouvrir `https://localhost:8000/notes` et recharger | « Vous avez consulté cette liste N fois. », N augmente |

## À retenir

- HTTP est sans mémoire ; la **session** garde un état entre requêtes.
- Lire, créer, écrire : `get_session`, `store.create()`, `store.set(...)`.
- Le cookie de session est toujours **durci** (`HttpOnly`, `SameSite`, `Secure`).

Vous avez parcouru les huit paliers du niveau intermédiaire. Place au bilan.

[Bilan du niveau intermédiaire](bilan.md)
