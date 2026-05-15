class Response:
    """
    Encapsule une réponse HTTP à envoyer au navigateur.

    Attributs :
        status       (int)   : code HTTP — 200, 403, 404...
        content_type (str)   : type MIME — text/html, text/css...
        body         (bytes) : contenu à envoyer (str converti automatiquement en bytes)
        headers      (dict)  : headers HTTP supplémentaires — ex: {"Location": "/clients"}
    """
    def __init__(self, status=200, body=b"", content_type="text/html; charset=utf-8", headers=None):
        self.status       = status
        self.content_type = content_type
        if isinstance(body, str):
            self.body = body.encode("utf-8")
        elif body is None:
            self.body = b""
        else:
            self.body = body
        self.headers      = headers if headers is not None else {}
