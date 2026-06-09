# La façade Cookies

Objectif : regrouper la lecture et l'écriture des cookies **applicatifs**
(thème, préférence…) sous une façade `Cookies`, distincte du cookie de session.

**Ce que vous allez apprendre :** lire un cookie depuis la requête, en poser un
sur la réponse avec des défauts sûrs, et une **limite importante** du noyau à
connaître avant de vous en servir.

## Là où nous en sommes

Vous avez `_facade.py` (palier 1) et `session.py` (palier 2). Nous ajoutons une
façade pour les cookies génériques, qui ne sont pas du ressort de `Session`.

## L'ajout

Créez `mvc/helpers/cookies.py` :

```python
# mvc/helpers/cookies.py
"""Façade de confort pour les cookies applicatifs (helper applicatif).

Limite : Response.headers est un dict, donc UN SEUL Set-Cookie par réponse.
Pour le cookie de SESSION (durci __Host-), utiliser Session.set_cookie.
"""

from core.http.request import Request
from core.http.response import Response
from mvc.helpers._facade import Facade


class Cookies(Facade):

    @staticmethod
    def get(request: Request, name: str, default: str | None = None) -> str | None:
        for part in request.headers.get("Cookie", "").split(";"):
            part = part.strip()
            if part.startswith(name + "="):
                return part[len(name) + 1:]
        return default

    @staticmethod
    def all(request: Request) -> dict[str, str]:
        jar: dict[str, str] = {}
        for part in request.headers.get("Cookie", "").split(";"):
            part = part.strip()
            if "=" in part:
                key, value = part.split("=", 1)
                jar[key.strip()] = value.strip()
        return jar

    @staticmethod
    def set(response: Response, name: str, value: str, *, max_age: int | None = None,
            path: str = "/", secure: bool = True, http_only: bool = True,
            same_site: str = "Strict") -> None:
        parts = [f"{name}={value}", f"Path={path}"]
        if max_age is not None:
            parts.append(f"Max-Age={int(max_age)}")
        if http_only:
            parts.append("HttpOnly")
        if secure:
            parts.append("Secure")
        if same_site:
            parts.append(f"SameSite={same_site}")
        response.headers["Set-Cookie"] = "; ".join(parts)

    @staticmethod
    def clear(response: Response, name: str, *, path: str = "/") -> None:
        Cookies.set(response, name, "", max_age=0, path=path)
```

## Comprendre ce code

- **Lecture** : `get` parcourt l'en-tête `Cookie` de la requête et renvoie la
  valeur (ou `default`). `all` renvoie tous les cookies sous forme de
  dictionnaire. Aucune écriture, aucun effet de bord.
- **Écriture** : `set` construit la chaîne `Set-Cookie` avec des **défauts sûrs**
  (`Secure`, `HttpOnly`, `SameSite=Strict`). Ces défauts sont **surchargeables** :
  pour un cookie lisible côté JavaScript (un thème, par exemple), passez
  `http_only=False`.
- **`clear`** efface un cookie en le réémettant avec `Max-Age=0`.

!!! warning "Limite : un seul Set-Cookie par réponse"
    `Response.headers` est un **dictionnaire** : il ne peut porter qu'**un seul**
    `Set-Cookie`. Donc `Cookies.set(...)` **écrase** tout cookie déjà posé sur la
    même réponse, y compris le cookie de **session** (`Session.set_cookie` écrit
    la même clé). Concrètement : ne posez **pas** un cookie applicatif sur une
    réponse qui pose aussi la session, l'un des deux serait perdu. La lecture
    (`get` / `all`) n'est pas concernée ; c'est l'écriture **multiple** qui est
    bloquée, côté noyau, tant que `Response` ne gère pas une liste de cookies.

## Tester

Dans un shell Python du projet :

```python
>>> import types
>>> from core.http.response import Response
>>> from mvc.helpers.cookies import Cookies
>>> # écriture
>>> r = Response.text("ok")
>>> Cookies.set(r, "theme", "dark", http_only=False, max_age=31536000)
>>> r.headers["Set-Cookie"]
'theme=dark; Path=/; Max-Age=31536000; Secure; SameSite=Strict'
>>> # lecture
>>> req = types.SimpleNamespace(headers={"Cookie": "theme=dark; lang=fr"})
>>> Cookies.get(req, "theme")
'dark'
>>> Cookies.all(req)
{'theme': 'dark', 'lang': 'fr'}
```

## À retenir

- `Cookies` est pour les cookies **applicatifs génériques** ; le cookie de
  session reste géré par `Session.set_cookie` (politique `__Host-` du noyau).
- Lire un cookie = parser l'en-tête `Cookie` de la requête ; écrire = poser un
  `Set-Cookie` sur la réponse.
- **Un seul `Set-Cookie` par réponse** : ne combinez pas un cookie applicatif et
  le cookie de session sur la même réponse.

Au palier suivant, nous ajoutons une façade pour les messages flash.

[Continuer avec La façade Flash](flash.md)
