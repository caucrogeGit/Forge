import json as _json
from dataclasses import dataclass
from email.parser import BytesParser
from email.policy import default as _email_policy
from io import BytesIO
from urllib.parse import urlparse, parse_qs

from core.forge import get as _cfg


BODY_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
METHOD_OVERRIDE_TARGETS = {"PUT", "PATCH", "DELETE"}
MAX_BODY_SIZE = 1_048_576  # 1 Mo


class RequestEntityTooLarge(Exception):
    """Levée si Content-Length dépasse MAX_BODY_SIZE."""


@dataclass(frozen=True)
class UploadedFile:
    """Fichier reçu via multipart/form-data."""

    field_name: str
    filename: str
    content: bytes
    content_type: str | None = None

    @property
    def size(self) -> int:
        return len(self.content)

    @property
    def stream(self):
        return BytesIO(self.content)

    def read(self) -> bytes:
        return self.content


def _request_size_limit(content_type: str) -> int:
    if "multipart/form-data" not in content_type:
        return MAX_BODY_SIZE
    try:
        upload_max = int(_cfg("upload_max_size"))
    except Exception:
        upload_max = MAX_BODY_SIZE
    return max(MAX_BODY_SIZE, upload_max + 65_536)


class Request:
    """
    Encapsule une requête HTTP entrante.

    Attributs :
        original_method (str) : verbe HTTP reçu
        method          (str) : verbe effectif après éventuel _method
        path            (str) : chemin de la requête — /clients, /...
        headers         (http.client.HTTPMessage) : en-têtes HTTP
        params          (dict) : paramètres d'URL — ?id=1 → {"id": ["1"]}
        body            (dict) : données du formulaire, format parse_qs (vide pour GET)
        json_body       (dict) : données JSON du body (vide si Content-Type != application/json)
    """
    def __init__(self, handler):
        parsed        = urlparse(handler.path)
        self.original_method = handler.command
        self.method   = handler.command
        self.path     = parsed.path
        self.headers  = handler.headers
        self.params   = parse_qs(parsed.query)
        self.files    = {}
        self.ip           = handler.client_address[0]
        self.route_params = {}  # injecté par Application.dispatch() pour les routes dynamiques

        if self.method in BODY_METHODS:
            content_type = handler.headers.get("Content-Type", "")
            try:
                content_length = int(handler.headers.get("Content-Length", 0))
            except (ValueError, TypeError):
                content_length = 0
            if content_length > _request_size_limit(content_type):
                raise RequestEntityTooLarge(content_length)
            content_length = max(0, content_length)
            raw = handler.rfile.read(content_length) if content_length else b""

            if "application/json" in content_type:
                try:
                    self.json_body = _json.loads(raw.decode("utf-8"))
                except (ValueError, UnicodeDecodeError):
                    self.json_body = {}
                self.body = {}
            elif "multipart/form-data" in content_type:
                self.body, self.files = self._parse_multipart(content_type, raw)
                self.json_body = {}
            else:
                try:
                    self.body = parse_qs(raw.decode("utf-8"), keep_blank_values=True)
                except UnicodeDecodeError:
                    self.body = {}
                self.json_body = {}
        else:
            self.body      = {}
            self.json_body = {}

        self._apply_method_override()

    def _apply_method_override(self) -> None:
        """Transforme POST + _method=DELETE/PATCH/PUT avant le routage."""
        if self.original_method.upper() != "POST":
            return

        raw_method = self.body.get("_method", [None])
        if isinstance(raw_method, list):
            override = raw_method[0] if raw_method else None
        else:
            override = raw_method

        if not override:
            return

        override = str(override).upper()
        if override in METHOD_OVERRIDE_TARGETS:
            self.method = override

    @staticmethod
    def _parse_multipart(content_type: str, raw: bytes):
        body: dict[str, list[str]] = {}
        files: dict[str, UploadedFile] = {}
        header = (
            f"Content-Type: {content_type}\r\n"
            "MIME-Version: 1.0\r\n\r\n"
        ).encode("utf-8")
        try:
            message = BytesParser(policy=_email_policy).parsebytes(header + raw)
        except Exception:
            return body, files
        if not message.is_multipart():
            return body, files
        for part in message.iter_parts():
            if part.get_content_disposition() != "form-data":
                continue
            name = part.get_param("name", header="content-disposition")
            if not name:
                continue
            filename = part.get_filename()
            payload = part.get_payload(decode=True) or b""
            if filename is not None:
                files[name] = UploadedFile(
                    field_name=name,
                    filename=filename,
                    content=payload,
                    content_type=part.get_content_type(),
                )
            else:
                try:
                    value = payload.decode(part.get_content_charset() or "utf-8")
                except UnicodeDecodeError:
                    value = ""
                body.setdefault(name, []).append(value)
        return body, files
