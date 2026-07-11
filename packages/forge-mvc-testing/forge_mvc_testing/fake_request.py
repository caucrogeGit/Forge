"""Requête HTTP simulée pour les tests unitaires de contrôleurs Forge.

Portée depuis `tests/fake_request.py` vers le paquet de test-support
`forge-mvc-testing` (ADR-041), pour que les tests de chaque paquet opt-in y
accèdent sans dépendre du `tests/` racine.
"""


class FakeRequest:
    """
    Requête HTTP simulée pour les tests unitaires de contrôleurs.

    Usage :
        req = FakeRequest("GET", "/clients")
        req = FakeRequest("POST", "/clients", body={"Nom": "Dupont"})
        req = FakeRequest("POST", "/api/sync", json_body={"ids": [1, 2]})
        req = FakeRequest("GET", "/clients", session_id="abc123")

    La fixture `fake_request` (plugin pytest) retourne la classe directement.
    """

    def __init__(self, method="GET", path="/", *,
                 body=None, json_body=None, params=None,
                 session_id=None, ip="127.0.0.1", headers=None, files=None):
        self.original_method = method.upper()
        self.method       = self.original_method
        self.path         = path
        self.ip           = ip
        self.route_params = {}
        self.params       = {k: [v] for k, v in (params or {}).items()}

        # body formulaire (format parse_qs : valeurs en liste)
        self.body      = {k: [v] for k, v in (body or {}).items()}
        self.json_body = json_body or {}
        self.files     = files or {}
        self._apply_method_override()

        # session injectée via le cookie
        self.headers = _FakeHeaders(session_id, headers=headers)

    def _apply_method_override(self):
        if self.original_method != "POST":
            return
        value = self.body.get("_method", [None])
        override = value[0] if isinstance(value, list) and value else value
        if override and str(override).upper() in {"PUT", "PATCH", "DELETE"}:
            self.method = str(override).upper()

    # ── Convention d'inspection — miroir des accesseurs de `Request` ────────
    #
    # Ajouté par STARTER-BONJOUR-FORGE-001 / API-INSPECTABLE-OBJECTS-CONVENTION-001
    # pour que `FakeRequest` se comporte comme `core.http.request.Request`
    # dans les tests qui exercent les contrôleurs typés.

    def query(self, key, default=None):
        values = self.params.get(key)
        if not values:
            return default
        return values[0]

    def header(self, name, default=None):
        return self.headers.get(name, default)

    def form(self, key, default=None):
        values = self.body.get(key)
        if not values:
            return default
        if isinstance(values, list):
            return values[0] if values else default
        return values

    def json(self, key, default=None):
        body = self.json_body
        if not isinstance(body, dict):
            return default
        return body.get(key, default)

    def file(self, key, default=None):
        return self.files.get(key, default)

    def files_list(self, key):
        """Liste des fichiers pour `key` (galeries multi-upload), à l'image de
        `Request.files_list`. Accepte une valeur mono ou déjà-liste dans `files`."""
        val = self.files.get(key, [])
        if isinstance(val, (list, tuple)):
            return list(val)
        return [val] if val else []

    def route(self, key, default=None):
        return self.route_params.get(key, default)

    @property
    def data(self):
        """Mini-version de `Request.data` pour les tests de contrôleurs.

        Reproduit les clés canoniques (method, path, ip, params,
        route_params, headers, body, json_body, files) mais sans le
        masquage avancé (les tests ne devraient pas avoir besoin de
        passer par FakeRequest pour vérifier le masquage — `Request`
        réel est utilisé pour ça)."""
        headers_view = {}
        for key in list(getattr(self.headers, "_headers", {})):
            headers_view[key] = self.headers.get(key)
        return {
            "method": self.method,
            "original_method": self.original_method,
            "path": self.path,
            "ip": self.ip,
            "params": dict(self.params),
            "route_params": dict(self.route_params),
            "headers": headers_view,
            "body": dict(self.body),
            "json_body": dict(self.json_body) if isinstance(self.json_body, dict) else self.json_body,
            "files": {k: {"filename": getattr(f, "filename", None),
                          "size": getattr(f, "size", None),
                          "content_type": getattr(f, "content_type", None)}
                      for k, f in self.files.items()},
        }


class _FakeHeaders:
    """Simule http.client.HTTPMessage pour get("Cookie") et get("Content-Type")."""

    def __init__(self, session_id=None, headers=None):
        self._session_id = session_id
        self._headers = dict(headers or {})
        self._headers_lower = {key.lower(): value for key, value in self._headers.items()}

    def get(self, name, default: str | None = ""):
        if name in self._headers:
            return self._headers[name]
        if name.lower() in self._headers_lower:
            return self._headers_lower[name.lower()]
        if name == "Cookie" and self._session_id:
            return f"__Host-session_id={self._session_id}"
        return default
