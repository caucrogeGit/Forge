# Messages flash

**Objectif**{ .intro-label } : confirmer une action par un message qui s'affiche **une seule fois**, à la requête suivante.

**Ce que vous allez apprendre :**{ .intro-label } le motif **POST-Redirect-GET** complet. Une action `POST` pose un **message flash** puis **redirige** ; la page cible lit le flash (`get_flash`, qui le supprime aussitôt) et l'affiche.

La modification ré-affiche la page d'édition, et la suppression redirige sans confirmation.

Nous donnons à ces deux écritures un vrai retour utilisateur : un message de confirmation **one-shot**, posé avant la redirection et affiché sur la liste.

??? note "Documentations"
    Pour bien comprendre ce palier :

    | Document | Ce qu'il apporte |
    |---|---|
    | [La session HTTP](../../../core-security/session.md) | où le flash est stocké entre deux requêtes |
    | [L'objet Response](../../../core-http/response.md) | la redirection qui suit le POST |

??? note "Contrôleurs"
    Dans `mvc/controllers/note_controller.py`, faites poser un flash par `update` et `delete` au moment de rediriger, et lisez le flash dans `index`.

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
            record_id = int(request.route("id", default="0"))
            content = request.form("content", default="").strip()
            if not content:
                return Response.text("Le contenu est obligatoire.", status=422)
            execute(UPDATE_ONE, (content, record_id))
            return BaseController.redirect("/note", request=request, flash="Note mise à jour.")

        @staticmethod
        def delete(request: Request) -> Response:
            record_id = int(request.route("id", default="0"))
            execute(DELETE_ONE, (record_id,))
            return BaseController.redirect("/note", request=request, flash="Note supprimée.")
    ```

    | Élément | Rôle |
    |---|---|
    | `redirect("/note", request=request, flash="…")` | **Pose** le message dans la session puis renvoie une redirection : le **P**OST puis le **R**edirect du motif. |
    | `get_flash(session_id)` | Au **G**ET suivant, lit le message **et le supprime** : il ne s'affiche donc qu'une fois, même en rechargeant. |

    `update` ne ré-affiche plus la page d'édition : il redirige vers la liste, état réel et partageable.

??? note "Vues"
    Affichez le flash en tête du bloc `content` de `mvc/views/note/index.html` :

    ```html
    {% if flash %}
    <p><strong>{{ flash.message }}</strong></p>
    {% endif %}
    ```

??? note "Routes"
    Inchangé : le flash réutilise les routes existantes (aucune route nouvelle).

    ```python
    # mvc/routes/__init__.py
    from core.http.router import Router
    from mvc.controllers.home_controller import HomeController
    from mvc.controllers.note_controller import NoteController

    router = Router()

    with router.group("", public=True) as public:
        public.add("GET",  "/", HomeController.index, name="home-index")
        public.add("GET",  "/note", NoteController.index, name="note-index")
        public.add("GET",  "/note/edit/{id}", NoteController.edit, name="note-edit")
        public.add("POST", "/note/update/{id}", NoteController.update, name="note-update")
        public.add("POST", "/note/delete/{id}", NoteController.delete, name="note-delete")
    ```

??? note "Tests"
    | Action | Résultat |
    |---|---|
    | Modifier une note | retour à la liste avec « Note mise à jour. » |
    | Recharger la liste | le message a disparu (one-shot) |
    | Supprimer une note | retour à la liste avec « Note supprimée. » |

??? note "À retenir"
    - POST-Redirect-GET : on **redirige** après une écriture, jamais on ne ré-affiche directement le POST.
    - Un flash est **one-shot** : `get_flash` le lit et le supprime.
    - Le flash combine **session** (stockage) et **redirection**.

??? tip "Astuces"
    Le couple « poser un flash / le lire » se prête bien à une **façade** `Flash` de votre application, sous `mvc/helpers/`, qui masquerait `get_flash` et le passage du `flash=` au `redirect`.

    Forge ne l'ajoute pas au framework : le noyau reste minimal et explicite, l'ergonomie est à votre main.
    Un parcours dédié vous montre comment construire ces façades pas à pas (`Session`, `Cookies`, `Flash`) : [Construire vos façades helper](../../welcome-helpers/installation.md).

Au palier suivant, nous mémorisons un état serveur entre les requêtes avec la session.

[Continuer avec Mémoriser un état en session](session-state.md)
