# Messages flash

Objectif : confirmer une action par un message qui s'affiche **une fois**, à la
requête suivante.

**Ce que vous allez apprendre :** le motif **POST-Redirect-GET**. Une action
`POST` pose un **message flash** (`set_flash`) et **redirige** ; la page cible
lit le flash (`get_flash`, qui le supprime aussitôt) et l'affiche. C'est la
bonne façon de donner un retour après une écriture.

Dernier palier du **niveau intermédiaire** de la
[progression officielle des starters](../../index.md#progression-recommandee),
après [Mémoriser un état en session](session-state.md).

## Ce que ce starter montre

- poser un message flash après une action (`BaseController.set_flash`) ;
- **rediriger** vers la page (`BaseController.redirect`) — motif PRG ;
- lire et afficher le flash **one-shot** (`get_flash`) à la requête suivante ;
- combiner **session**, **CSRF** et **redirection**.

Aucune base de données.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `BaseController.set_flash` / `redirect` | Poser un flash puis rediriger (PRG). | [BaseController](../../../reference/api.md#coremvccontroller) |
| `get_flash` | Lire et supprimer le flash (one-shot). | [Sessions](../../../reference/sessions.md) |
| `BaseController.csrf_token` | Protéger l'action POST. | [BaseController](../../../reference/api.md#coremvccontroller) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/flash-messages`, cliquez **Faire une action** →
un message de confirmation s'affiche. Rechargez → il a disparu (one-shot).

## Le contrôleur

```python
# mvc/controllers/flash_messages_controller.py
from core.security.session import get_flash, get_session, get_session_id
from core.sessions.manager import get_session_store


class FlashMessagesController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        store = get_session_store()
        session_id = get_session_id(request)
        session = get_session(session_id) if session_id else None
        if not session:
            session_id = store.create()
            session = get_session(session_id)

        flash = get_flash(session_id)  # one-shot : le message disparaît
        response = BaseController.render(
            "flash_messages/index.html",
            context={"flash": flash, "csrf_token": BaseController.csrf_token(request)},
            request=request,
        )
        response.headers["Set-Cookie"] = (
            f"session_id={session_id}; Path=/; HttpOnly; SameSite=Strict; Secure"
        )
        return response

    @staticmethod
    def action(request: Request) -> Response:
        BaseController.set_flash(request, "Action effectuée avec succès !")
        return BaseController.redirect("/flash-messages")
```

### Comprendre ce code

- `action` (POST) **pose** le flash dans la session puis **redirige** vers
  `/flash-messages` : c'est le **POST-Redirect-GET**. On ne réaffiche jamais une
  page directement après un POST (sinon un rechargement re-soumet le formulaire).
- `index` lit le flash avec `get_flash`, qui le **renvoie et le supprime** : le
  message ne s'affiche donc qu'**une seule fois**.
- La session doit exister pour porter le flash : on la garantit comme au palier
  *Mémoriser un état en session*.

## La vue

```html
<!-- mvc/views/flash_messages/index.html -->
{% if flash %}
<p data-level="{{ flash.level }}"><strong>{{ flash.message }}</strong></p>
{% endif %}

<form method="post" action="/flash-messages/action">
  <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
  <button type="submit">Faire une action</button>
</form>
```

### Comprendre ce code

- Le bloc `{% if flash %}` n'affiche le message que s'il y en a un.
- L'action est un `POST` **protégé par CSRF**.

## À retenir

- Flash = retour utilisateur **one-shot** après une action.
- Motif **POST-Redirect-GET** : poser le flash, rediriger, l'afficher au GET.
- `get_flash` **lit et supprime** : le message ne réapparaît pas au rechargement.

## Après ce starter

Vous avez terminé le **niveau intermédiaire** : listes, recherche, pagination,
gabarits, mise à jour, suppression, sessions et messages flash. Faites le point
dans le bilan du niveau.

[Bilan du niveau intermédiaire](bilan.md)
