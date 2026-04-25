class FakeRequest:
    """
    Requête HTTP simulée pour les tests unitaires de contrôleurs.

    Usage :
        req = FakeRequest("GET", "/clients")
        req = FakeRequest("POST", "/clients", body={"Nom": "Dupont"})
        req = FakeRequest("POST", "/api/sync", json_body={"ids": [1, 2]})
        req = FakeRequest("GET", "/clients", session_id="abc123")

    La fixture `fake_request` dans conftest.py retourne la classe directement.
    """

    def __init__(self, method="GET", path="/", *,
                 body=None, json_body=None, params=None,
                 session_id=None, ip="127.0.0.1", headers=None):
        self.original_method = method.upper()
        self.method       = self.original_method
        self.path         = path
        self.ip           = ip
        self.route_params = {}
        self.params       = {k: [v] for k, v in (params or {}).items()}

        # body formulaire (format parse_qs : valeurs en liste)
        self.body      = {k: [v] for k, v in (body or {}).items()}
        self.json_body = json_body or {}
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


class _FakeHeaders:
    """Simule http.client.HTTPMessage pour get("Cookie") et get("Content-Type")."""

    def __init__(self, session_id=None, headers=None):
        self._session_id = session_id
        self._headers = dict(headers or {})
        self._headers_lower = {key.lower(): value for key, value in self._headers.items()}

    def get(self, name, default=""):
        if name in self._headers:
            return self._headers[name]
        if name.lower() in self._headers_lower:
            return self._headers_lower[name.lower()]
        if name == "Cookie" and self._session_id:
            return f"session_id={self._session_id}"
        return default
