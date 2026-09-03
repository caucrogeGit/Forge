# pyright: strict
"""Client de test, de la requête à la réponse (`TESTING-CLIENT-001`).

`FakeRequest` permet d'appeler un contrôleur directement. C'est utile et
insuffisant : rien n'y passe par le routeur, ni par les middlewares, ni par la
construction d'une `Request` depuis un environnement WSGI.

Un test qui appelle `ArticleController.show(fake_request)` ne prouve donc rien
du CSRF, de l'authentification, des en-têtes de sécurité, ni même de
l'existence de la route.

## Le client passe par le VRAI chemin de production

Il construit un environnement WSGI et appelle le callable rendu par
`create_wsgi_app`, c'est à dire exactement ce que Gunicorn appelle.

Ce n'est pas un détail d'élégance. Un client de test qui reconstruirait sa
propre boucle serait un **jumeau** : il passerait là où la production échoue,
et les deux dériveraient sans que rien ne le signale. Forge a déjà payé cette
erreur une fois, avec un serveur de développement qui répondait là où Gunicorn
rendait 404.

## Ce que le client garde entre deux requêtes

Les cookies, donc la session. Un scénario de test réaliste enchaîne une
connexion, une lecture de formulaire et un envoi, et chacune de ces étapes
dépend de la précédente.

Rien d'autre n'est gardé : pas d'état applicatif, pas de cache, pas de
transaction. Le client est un navigateur minimal, pas un environnement.
"""
from __future__ import annotations

import io
import json as _json
from http.cookies import SimpleCookie
from typing import Any, Callable, Iterable, Mapping
from urllib.parse import urlencode, urlsplit

__all__ = [
    "ClientError",
    "ClientResponse",
    "ForgeTestClient",
]

_WsgiApp = Callable[[dict[str, Any], Callable[..., Any]], Iterable[bytes]]


class ClientError(RuntimeError):
    """Le client n'a pas pu jouer la requête.

    Nommée `ClientError` et non `TestClientError` : pytest collecte toute
    classe dont le nom commence par `Test`, et aurait tenté d'en faire une
    classe de tests, avec un avertissement à chaque exécution.
    """


class ClientResponse:
    """Réponse capturée, telle qu'un serveur WSGI l'aurait transmise."""

    def __init__(
        self, status: str, headers: "list[tuple[str, str]]", body: bytes
    ) -> None:
        self.status_line = status
        self.headers = headers
        self.body = body

    @property
    def status(self) -> int:
        """Code numérique. `« 404 Not Found »` donne 404."""
        return int(self.status_line.split(" ", 1)[0])

    @property
    def text(self) -> str:
        """Corps décodé en UTF-8, les octets invalides remplacés.

        Remplacés et non levés : un test qui échoue doit montrer la page, et
        une exception de décodage masquerait le vrai motif de l'échec.
        """
        return self.body.decode("utf-8", errors="replace")

    def header(self, name: str) -> "str | None":
        """Premier en-tête de ce nom, insensible à la casse."""
        cible = name.lower()
        for cle, valeur in self.headers:
            if cle.lower() == cible:
                return valeur
        return None

    def headers_all(self, name: str) -> "list[str]":
        """Tous les en-têtes de ce nom. `Set-Cookie` en pose souvent plusieurs."""
        cible = name.lower()
        return [v for k, v in self.headers if k.lower() == cible]

    def json(self) -> Any:
        """Corps décodé en JSON.

        Raises:
            ClientError: le corps n'est pas du JSON. Le message porte le
                début du corps : une page d'erreur HTML rendue là où du JSON
                était attendu se diagnostique en le lisant.
        """
        try:
            return _json.loads(self.text)
        except ValueError as exc:
            apercu = self.text[:200]
            raise ClientError(
                f"la réponse n'est pas du JSON ({exc}). Début du corps : "
                f"{apercu!r}"
            ) from exc

    @property
    def location(self) -> "str | None":
        """Cible d'une redirection, ou `None`."""
        return self.header("Location")

    def __repr__(self) -> str:
        return f"<ClientResponse {self.status_line} {len(self.body)} octets>"


class ForgeTestClient:
    """Navigateur minimal, branché sur le callable WSGI de l'application.

    ```python
    from core.app.wsgi import create_wsgi_app
    from forge_mvc_testing import ForgeTestClient

    client = ForgeTestClient(create_wsgi_app(application, emit_prod_warnings=False))
    reponse = client.get("/articles")
    assert reponse.status == 200
    ```
    """

    def __init__(
        self,
        wsgi_app: _WsgiApp,
        *,
        base_url: str = "http://testserver",
        follow_redirects: bool = False,
    ) -> None:
        self._app = wsgi_app
        self._base = base_url.rstrip("/")
        self._follow = follow_redirects
        self.cookies: "dict[str, str]" = {}

    # -- Verbes ----------------------------------------------------------

    def get(self, path: str, **kw: Any) -> ClientResponse:
        return self.request("GET", path, **kw)

    def post(self, path: str, **kw: Any) -> ClientResponse:
        return self.request("POST", path, **kw)

    def put(self, path: str, **kw: Any) -> ClientResponse:
        return self.request("PUT", path, **kw)

    def delete(self, path: str, **kw: Any) -> ClientResponse:
        return self.request("DELETE", path, **kw)

    # -- Cœur ------------------------------------------------------------

    def request(
        self,
        method: str,
        path: str,
        *,
        data: "Mapping[str, Any] | None" = None,
        json: Any = None,
        headers: "Mapping[str, str] | None" = None,
        query: "Mapping[str, Any] | None" = None,
        follow_redirects: "bool | None" = None,
    ) -> ClientResponse:
        """Joue une requête et rend la réponse.

        `data` est envoyé en formulaire, `json` en corps JSON. Les deux
        ensemble sont refusés : une requête ne porte qu'un corps, et laisser
        l'un gagner en silence produirait un test qui vérifie autre chose que
        ce qu'il croit.
        """
        if data is not None and json is not None:
            raise ClientError(
                "data et json ne peuvent pas être passés ensemble : une "
                "requête ne porte qu'un corps."
            )

        decoupe = urlsplit(path)
        chemin = decoupe.path or "/"
        params = decoupe.query
        if query:
            supplement = urlencode(
                {k: str(v) for k, v in query.items()}, doseq=True
            )
            params = f"{params}&{supplement}" if params else supplement

        corps = b""
        type_contenu = ""
        if json is not None:
            corps = _json.dumps(json, ensure_ascii=False).encode("utf-8")
            type_contenu = "application/json; charset=utf-8"
        elif data is not None:
            corps = urlencode(
                {k: "" if v is None else str(v) for k, v in data.items()},
                doseq=True,
            ).encode("utf-8")
            type_contenu = "application/x-www-form-urlencoded"

        environ = self._environ(method, chemin, params, corps, type_contenu, headers)
        reponse = self._call(environ)
        self._absorb_cookies(reponse)

        suivre = self._follow if follow_redirects is None else follow_redirects
        if suivre and 300 <= reponse.status < 400 and reponse.location:
            # Une seule redirection est suivie. Une boucle de redirections est
            # un défaut à voir, pas à absorber : la suivre indéfiniment ferait
            # tourner le test sans fin.
            return self.request(
                "GET", reponse.location, headers=headers, follow_redirects=False
            )
        return reponse

    # -- Détail ----------------------------------------------------------

    def _environ(
        self,
        method: str,
        path: str,
        query: str,
        body: bytes,
        content_type: str,
        headers: "Mapping[str, str] | None",
    ) -> "dict[str, Any]":
        """Environnement WSGI conforme à la PEP 3333.

        Les clés obligatoires y sont toutes : un environnement incomplet ferait
        échouer la construction de la `Request` pour une raison qui n'a rien à
        voir avec ce que le test vérifie.
        """
        env: dict[str, Any] = {
            "REQUEST_METHOD": method.upper(),
            "PATH_INFO": path,
            "QUERY_STRING": query,
            "SERVER_NAME": "testserver",
            "SERVER_PORT": "80",
            "SERVER_PROTOCOL": "HTTP/1.1",
            "REMOTE_ADDR": "127.0.0.1",
            "HTTP_HOST": "testserver",
            "wsgi.version": (1, 0),
            "wsgi.url_scheme": "http",
            "wsgi.input": io.BytesIO(body),
            "wsgi.errors": io.StringIO(),
            "wsgi.multithread": False,
            "wsgi.multiprocess": False,
            "wsgi.run_once": False,
            "CONTENT_LENGTH": str(len(body)),
        }
        if content_type:
            env["CONTENT_TYPE"] = content_type
        if self.cookies:
            env["HTTP_COOKIE"] = "; ".join(
                f"{k}={v}" for k, v in self.cookies.items()
            )
        for nom, valeur in (headers or {}).items():
            cle = "HTTP_" + nom.upper().replace("-", "_")
            if cle in ("HTTP_CONTENT_TYPE", "HTTP_CONTENT_LENGTH"):
                cle = cle[len("HTTP_"):]
            env[cle] = valeur
        return env

    def _call(self, environ: "dict[str, Any]") -> ClientResponse:
        capture: "dict[str, Any]" = {}

        def start_response(
            status: str, headers: "list[tuple[str, str]]", exc_info: Any = None
        ) -> Callable[[bytes], None]:
            capture["status"] = status
            capture["headers"] = list(headers)
            return lambda _octets: None

        morceaux = self._app(environ, start_response)
        corps = b"".join(morceaux)
        fermer = getattr(morceaux, "close", None)
        if callable(fermer):
            fermer()

        if "status" not in capture:
            raise ClientError(
                "l'application n'a pas appelé start_response : ce n'est pas un "
                "callable WSGI conforme."
            )
        return ClientResponse(
            str(capture["status"]), capture["headers"], corps
        )

    def _absorb_cookies(self, reponse: ClientResponse) -> None:
        """Mémorise les cookies posés, comme un navigateur.

        Un cookie effacé par le serveur (`Max-Age=0`) est **retiré** du client :
        une déconnexion doit se voir sur la requête suivante, et garder le
        cookie ferait passer un test de déconnexion qui ne prouve rien.
        """
        for brut in reponse.headers_all("Set-Cookie"):
            biscuit = SimpleCookie()
            biscuit.load(brut)
            for nom, morceau in biscuit.items():
                efface = morceau["max-age"] == "0" or morceau["expires"].startswith(
                    ("Thu, 01 Jan 1970", "Thu, 01-Jan-1970")
                )
                if efface or not morceau.value:
                    self.cookies.pop(nom, None)
                else:
                    self.cookies[nom] = morceau.value

    def clear_cookies(self) -> None:
        """Oublie tous les cookies. Équivaut à un nouveau navigateur."""
        self.cookies.clear()
