# Imports et usage

Objectif : exposer les trois façades sous un **import unique** et les utiliser
dans un contrôleur réel.

**Ce que vous allez apprendre :** ré-exporter les façades depuis le package, et
les combiner (session, flash, cookie) dans le flux d'un formulaire, en restant
cohérent avec les helpers déjà fournis par Forge.

## Là où nous en sommes

Vous avez les quatre fichiers : `_facade.py`, `session.py`, `cookies.py`,
`flash.py`. Il reste à les rendre commodes à importer, puis à les employer.

## L'ajout

Ré-exportez les façades dans `mvc/helpers/__init__.py` :

```python
# mvc/helpers/__init__.py
from mvc.helpers.cookies import Cookies
from mvc.helpers.flash import Flash
from mvc.helpers.session import Session

__all__ = ["Session", "Cookies", "Flash"]
```

Un contrôleur peut alors tout importer en une ligne et composer le flux :

```python
# mvc/controllers/note_controller.py (extrait)
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController
from mvc.helpers import Cookies, Flash, Session


class NoteController(BaseController):

    @staticmethod
    def _ensure_session(request: Request):
        """Garantit une session et renvoie (session_id, data)."""
        session_id = Session.current_id(request)
        data = Session.get(session_id) if session_id else None
        if data is None:
            session_id = Session.new()
            data = Session.get(session_id)
        return session_id, data

    @staticmethod
    def form(request: Request) -> Response:
        session_id, data = NoteController._ensure_session(request)
        theme = Cookies.get(request, "theme", default="light")   # lecture : sans risque
        response = BaseController.render(
            "note/form.html",
            request=request,
            context={
                "csrf_token": data["csrf_token"],
                "flash": Flash.get(session_id),   # one-shot : lu puis supprimé
                "theme": theme,
            },
        )
        Session.set_cookie(response, session_id)   # le SEUL Set-Cookie de cette réponse
        return response

    @staticmethod
    def create(request: Request) -> Response:
        # ... traitement de la création ...
        # Motif POST -> redirect : Forge pose le flash ET redirige.
        return BaseController.redirect("/note/form", request=request, flash="Note enregistrée")
```

## Comprendre ce code

- **`__init__.py`** ré-exporte les trois classes : `from mvc.helpers import
  Session, Flash, Cookies` suffit, et `__all__` borne la surface publique du
  package.
- **`_ensure_session`** compose les primitifs de `Session` (lire l'id, lire la
  session, en créer une si besoin). On garde la logique *get-or-create* dans le
  contrôleur ; les façades, elles, restent des primitifs.
- **Lecture du flash** : `Flash.get(session_id)` dans le rendu. S'il y a un
  message en attente (posé par une action précédente), il s'affiche **une fois**.
- **Pose du flash** : pour le cas POST→redirect, on utilise
  `BaseController.redirect(..., flash="…")`, **déjà fourni par Forge**, qui pose
  le message et redirige. `Flash.set(...)` de notre façade sert seulement aux
  rares cas où l'on pose un flash **sans** rediriger.
- **Cookie** : on **lit** un cookie applicatif (`theme`) sans risque. On ne le
  **réécrit pas** ici, car cette réponse pose déjà le cookie de session
  (`Session.set_cookie`) ; rappel du palier 3 : **un seul `Set-Cookie` par
  réponse**. Pour changer le thème, on le ferait sur une réponse dédiée qui ne
  pose pas la session.

## Tester

Lancez l'application (`forge run`) et ouvrez le formulaire : le jeton CSRF est
rempli, le thème lu depuis le cookie, et après une création le message « Note
enregistrée » apparaît une seule fois au retour.

## À retenir

- `mvc/helpers/__init__.py` donne un **import unique** pour les trois façades.
- La logique *get-or-create* se compose dans le contrôleur ; les façades restent
  des primitifs.
- Réutilisez les helpers de Forge quand ils existent (`BaseController.redirect`
  pour flash+redirect) ; vos façades complètent, elles ne remplacent pas.
- Respectez la limite **un seul `Set-Cookie` par réponse**.

[Continuer avec le Bilan](bilan.md)
