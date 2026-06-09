# La façade Session

Objectif : regrouper les opérations de **session** (le store) sous une façade
`Session`, bâtie sur la base `Facade` du palier précédent.

**Ce que vous allez apprendre :** déléguer aux briques du noyau
(`get_session_store`, `get_session_id`, `set_session_cookie`) derrière des
méthodes statiques courtes, et distinguer ce qui touche le **store** de ce qui
touche le **cookie** de session.

## Là où nous en sommes

Le palier précédent a posé `mvc/helpers/_facade.py` (la base non instanciable).
Nous ajoutons maintenant la première vraie façade.

## L'ajout

Créez `mvc/helpers/session.py` :

```python
# mvc/helpers/session.py
"""Façade de confort pour la session non-auth (helper applicatif)."""

from core.http.request import Request
from core.http.response import Response
from core.security.cookies import set_session_cookie as _set_cookie
from core.security.session import get_session_id as _get_id
from core.sessions import get_session_store as _store
from mvc.helpers._facade import Facade


class Session(Facade):

    @staticmethod
    def new() -> str:
        return _store().create()

    @staticmethod
    def current_id(request: Request) -> str | None:
        return _get_id(request)

    @staticmethod
    def get(session_id: str) -> dict | None:
        return _store().get(session_id)

    @staticmethod
    def set(session_id: str, values: dict) -> None:
        _store().set(session_id, values)

    @staticmethod
    def set_cookie(response: Response, session_id: str, *, max_age: int | None = None) -> None:
        _set_cookie(response, session_id, max_age=max_age)
```

## Comprendre ce code

- **`Session(Facade)`** : la façade hérite du garde du palier 1, donc
  `Session()` lève une `TypeError`. On l'utilise par ses méthodes statiques.
- **Délégation pure** : chaque méthode ne fait que reléguer à une brique du
  noyau. Aucune logique n'est dupliquée ici ; la validation, la sécurité et le
  stockage restent dans le core. La façade n'apporte que le **regroupement**.
- Deux familles de méthodes, à bien distinguer :
  - **Côté store (l'état de la session)** : `new` crée une session (le store y
    place déjà un `csrf_token`), `get` lit ses données, `set` les met à jour
    (merge, sans écraser le `csrf_token` ni le flash).
  - **Côté cookie (le transport de l'identifiant)** : `current_id` lit l'id dans
    le cookie de la **requête** ; `set_cookie` pose le cookie sur la **réponse**.
- **Pourquoi `set_cookie` est ici** : c'est le cookie **propre à la session**,
  durci (`__Host-`, `Secure`, `HttpOnly`, `SameSite=Strict`). Sa politique de
  sécurité reste **dans le noyau** (`set_session_cookie`) ; la façade ne fait que
  l'exposer. Les cookies **applicatifs génériques** (thème, préférence), eux,
  iront dans une façade `Cookies` distincte au palier suivant.

## Tester

Dans un shell Python du projet :

```python
>>> from mvc.helpers.session import Session
>>> sid = Session.new()
>>> Session.get(sid)["csrf_token"]      # une session neuve porte déjà un jeton
'…'
>>> Session.set(sid, {"visits": 1})
>>> Session.get(sid)["visits"]
1
>>> Session()                            # le garde hérité de Facade s'applique
TypeError: Session ne s'instancie pas : namespace de méthodes statiques.
```

## À retenir

- `Session` regroupe le **store** (`new`, `get`, `set`) et le **cookie de
  session** (`current_id`, `set_cookie`), chaque méthode déléguant au noyau.
- La politique de sécurité du cookie n'est **pas** dans la façade : elle reste
  dans `core.security.cookies`.
- La façade hérite de `Facade` : non instanciable, on l'emploie par ses statics.

Au palier suivant, nous traitons les cookies **applicatifs** génériques avec une
façade `Cookies`.

[Continuer avec La façade Cookies](cookies.md)
