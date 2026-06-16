# pyright: strict
from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any
from urllib.parse import quote


SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Handler de route : reçoit la requête, retourne une réponse. Volontairement
# large (`Callable[..., Any]`) pour ne pas coupler le routeur aux types
# Request/Response (évite un import circulaire) ; le contrat précis est vérifié
# à l'usage côté Application.
Handler = Callable[..., Any]


class RouteEntry:
    """
    Représente une route compilée : pattern → regex, params nommés, handler.

    Patterns supportés :
        /clients            → route statique exacte
        /clients/{id}       → segment dynamique nommé
        /clients/{id}/edit  → segment dynamique en position intermédiaire
    """

    _PARAM = re.compile(r'\{(\w+)\}')

    def __init__(self, method: str | list[str], pattern: str, handler: Handler,
                 *, name: str | None = None, public: bool = False,
                 csrf: bool = True, api: bool = False) -> None:
        # Validation à l'enregistrement (donc dans le frame de mvc/routes.py).
        # Un handler non appelable ne casserait sinon qu'au dispatch
        # (`route.handler(request)`), erreur différée pointant le routeur et
        # non la ligne de routes.py fautive.
        if not callable(handler):
            raise TypeError(
                f"Le handler de la route {method!r} {pattern!r} doit être "
                f"appelable (méthode ou fonction de contrôleur), reçu "
                f"{type(handler).__name__} {handler!r}. "
                f'Exemple : router.add("GET", "/", HomeController.index).'
            )
        self.method   = method.upper() if isinstance(method, str) else [m.upper() for m in method]
        self.pattern  = pattern
        self.handler  = handler
        self.name     = name
        self.public   = public
        self.csrf     = csrf
        self.api      = api
        self.regex    = self._compile(pattern)

    @classmethod
    def _compile(cls, pattern: str) -> re.Pattern[str]:
        parts: list[str] = []
        for segment in pattern.split('/'):
            m = re.fullmatch(r'\{(\w+)\}', segment)
            if m:
                parts.append(f'(?P<{m.group(1)}>[^/]+)')
            else:
                parts.append(re.escape(segment))
        return re.compile('^' + '/'.join(parts) + '$')

    def matches_method(self, method: str) -> bool:
        if isinstance(self.method, list):
            return method.upper() in self.method
        return method.upper() == self.method

    @property
    def method_label(self) -> str:
        if isinstance(self.method, list):
            return ",".join(self.method)
        return self.method

    def requires_csrf(self, method: str) -> bool:
        return self.csrf and method.upper() in UNSAFE_METHODS

    def match(self, path: str) -> dict[str, Any] | None:
        """Retourne les paramètres capturés ou None si la route ne correspond pas."""
        m = self.regex.match(path)
        return m.groupdict() if m else None


class RouteGroup:
    """
    Groupe de routes partageant un préfixe commun et des propriétés partagées.

    Usage :
        with router.group("/api") as api:
            api.add("GET", "/clients",      ClientController.list)
            api.add("GET", "/clients/{id}", ClientController.show, name="client_show")
    """

    def __init__(self, router: "Router", prefix: str, *, public: bool = False,
                 csrf: bool = True, api: bool = False):
        self._router = router
        self._prefix = prefix.rstrip('/')
        self._public = public
        self._csrf = csrf
        self._api = api

    def add(self, method: str | list[str], pattern: str, handler: Handler, *,
            name: str | None = None, public: bool | None = None,
            csrf: bool | None = None, api: bool | None = None) -> RouteGroup:
        is_public = public if public is not None else self._public
        csrf_enabled = csrf if csrf is not None else self._csrf
        is_api = api if api is not None else self._api
        self._router.add(method, self._prefix + pattern, handler,
                         name=name, public=is_public,
                         csrf=csrf_enabled, api=is_api)
        return self

    def __enter__(self) -> RouteGroup:
        return self

    def __exit__(self, *args: object) -> None:
        pass


class Router:
    """
    Routeur HTTP avec routes statiques et dynamiques, noms et groupes.

    Usage :
        router = Router()

        # Convention de route (ADR-029) : chemin /<contrôleur>/<méthode>
        # (index = chemin nu), nom <contrôleur>-<méthode>. Racine / exceptée.
        router.add("GET", "/",                  HomeController.index, name="home-index")
        router.add("GET", "/client/show/{id}",  ClientController.show, name="client-show")

        with router.group("", public=True) as public:
            public.add("GET",  "/login/form", LoginController.form, name="login-form")
            public.add("POST", "/login/login", LoginController.login, name="login-login")

        # Dans l'application :
        result = router.resolve("GET", "/client/show/42")
        # → (ClientController.show, {"id": "42"})

        url = router.url_for("client_show", id=42)
        # → "/clients/42"
    """

    def __init__(self):
        self._entries: list[RouteEntry] = []
        self._named:   dict[str, RouteEntry] = {}

    def add(self, method: str | list[str], pattern: str, handler: Handler, *,
            name: str | None = None, public: bool = False, csrf: bool = True,
            api: bool = False) -> Router:
        """Enregistre une route. Retourne self pour le chaînage."""
        entry = RouteEntry(method, pattern, handler, name=name,
                           public=public, csrf=csrf, api=api)
        self._entries.append(entry)
        if name:
            if name in self._named:
                raise ValueError(f"Route déjà nommée : {name!r}")
            self._named[name] = entry
        return self

    def group(self, prefix: str, *, public: bool = False,
              csrf: bool = True, api: bool = False) -> RouteGroup:
        """Retourne un groupe de routes partageant un préfixe."""
        return RouteGroup(self, prefix, public=public, csrf=csrf, api=api)

    def match(self, method: str, path: str) -> tuple[RouteEntry, dict[str, Any]] | None:
        """
        Trouve l'entrée de route correspondante.

        Returns :
            (RouteEntry, params_dict) si trouvé, None sinon.
            params_dict est vide pour les routes statiques.
        """
        for entry in self._entries:
            if not entry.matches_method(method):
                continue
            params = entry.match(path)
            if params is not None:
                return entry, params
        return None

    def resolve(self, method: str, path: str) -> tuple[Handler, dict[str, Any]] | None:
        """
        Trouve la route correspondante.

        Returns :
            (handler, params_dict) si trouvé, None sinon.
            params_dict est vide pour les routes statiques.
        """
        result = self.match(method, path)
        if result is None:
            return None
        entry, params = result
        return entry.handler, params

    def is_public(self, path: str, method: str | None = None) -> bool:
        """Retourne True si le chemin correspond à une route publique."""
        for entry in self._entries:
            if method is not None and not entry.matches_method(method):
                continue
            if entry.public and entry.match(path) is not None:
                return True
        return False

    def iter_routes(self) -> list[RouteEntry]:
        """Retourne les routes dans l'ordre de déclaration."""
        return list(self._entries)

    def url_for(self, name: str, **params: Any) -> str:
        """
        Génère l'URL d'une route nommée en substituant les paramètres.

        Raises :
            KeyError  : si le nom de route est inconnu
            KeyError  : si un paramètre requis est manquant
        """
        entry = self._named.get(name)
        if entry is None:
            raise KeyError(f"Route inconnue : {name!r}")
        url = entry.pattern
        for key, value in params.items():
            # URL-encodage du segment : un paramètre contenant /, espace, ?, #…
            # produirait sinon une URL malformée. safe='' encode aussi '/'
            # (un paramètre de chemin ne traverse pas de segment).
            url = url.replace(f'{{{key}}}', quote(str(value), safe=''))
        if '{' in url:
            missing = re.findall(r'\{(\w+)\}', url)
            raise KeyError(f"Paramètres manquants pour {name!r} : {missing}")
        return url
