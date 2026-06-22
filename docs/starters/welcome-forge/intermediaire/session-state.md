# Mémoriser un état en session

**Objectif**{ .intro-label } : mémoriser un état côté serveur **entre** les requêtes.

**Ce que vous allez apprendre :**{ .intro-label } une requête HTTP est *sans mémoire* : le serveur oublie tout d'une requête à l'autre. La **session** garde un état rattaché à l'utilisateur via un cookie `session_id`. Ce palier compte les visites de la liste.

Le flash du palier précédent stockait déjà un message dans la session.

Nous y écrivons maintenant **notre propre** état : un compteur de visites, lu et incrémenté à chaque affichage de la liste.

??? note "Documentations"
    Pour bien comprendre ce palier :

    | Document | Ce qu'il apporte |
    |---|---|
    | [La session HTTP](../../../core-security/session.md) | lire, créer et écrire un état de session |
    | [Le cookie HTTP](../../../core-security/cookies.md) | les attributs durcis du cookie `session_id` |

??? note "Contrôleurs"
    Complétez les imports et faites évoluer `index` dans `mvc/controllers/note_controller.py` pour lire, incrémenter et réécrire le compteur, puis poser un cookie de session durci :

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
            session = get_session(session_id) or {}
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

    | Élément | Rôle |
    |---|---|
    | `get_session_id` / `get_session` | Lit le cookie, puis renvoie le dictionnaire de session (ou `None`). |
    | `store.create()` | Crée une session s'il n'en existe pas encore (via `_start_session`). |
    | `store.set(session_id, {"visits": visits})` | **Fusionne** la nouvelle valeur sans écraser le reste (csrf, flash). |
    | `set_session_cookie(...)` | Pose un cookie durci : `HttpOnly`, `SameSite=Strict`, `Secure` (HTTPS uniquement). |

??? note "Vues"
    Affichez le compteur dans le bloc `content` de `mvc/views/note/index.html` :

    ```html
    <p><small>Vous avez consulté cette liste {{ visits }} fois.</small></p>
    ```

??? note "Routes"
    Inchangé : le compteur vit dans la session, pas dans une route nouvelle.

    ```python
    # mvc/routes.py
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
    | Ouvrir `https://localhost:8000/note` et recharger | « Vous avez consulté cette liste N fois. », N augmente |

??? note "À retenir"
    - HTTP est sans mémoire ; la **session** garde un état entre requêtes.
    - Lire, créer, écrire : `get_session`, `store.create()`, `store.set(...)`.
    - Le cookie de session est toujours **durci** (`HttpOnly`, `SameSite`, `Secure`).

??? tip "Astuces"
    Lire et fusionner un état de session (`get_session`, `store.set`, `set_session_cookie`) revient à chaque palier qui mémorise quelque chose.
    Une **façade** `Session` de votre application, sous `mvc/helpers/`, regrouperait ces appels.

    Forge ne l'ajoute pas au framework : le noyau reste minimal et explicite, l'ergonomie est à votre main.
    Un parcours dédié vous montre comment construire ces façades pas à pas (`Session`, `Cookies`, `Flash`) : [Construire vos façades helper](../../welcome-helpers/installation.md).

Vous avez parcouru les huit paliers du niveau intermédiaire. Place au bilan.

[Bilan du niveau intermédiaire](bilan.md)
