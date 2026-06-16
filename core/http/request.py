# pyright: strict
from __future__ import annotations

import ipaddress
import json as _json
from typing import Any, cast
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from email.parser import BytesParser
from email.policy import default as _email_policy
from io import BytesIO
from urllib.parse import urlparse, parse_qs

from core.forge import get as _cfg


BODY_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
METHOD_OVERRIDE_TARGETS = {"PUT", "PATCH", "DELETE"}
MAX_BODY_SIZE = 1_048_576  # 1 Mo


# ── Convention d'inspection (API-INSPECTABLE-OBJECTS-CONVENTION-001) ────────
# Clés systématiquement masquées dans Request.data pour éviter de fuiter
# des secrets en logs / debug / sortie pédagogique. La comparaison est faite
# en lower-case, sur l'égalité exacte pour les headers (qui sont des noms
# standardisés) et par sous-chaîne pour les champs formulaire/JSON (qui
# couvrent un univers ouvert : `csrf_token`, `confirm_password`, `_token`, …).

SENSITIVE_HEADER_NAMES: frozenset[str] = frozenset({
    "authorization",
    "proxy-authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "x-auth-token",
    "x-csrf-token",
})


SENSITIVE_FIELD_FRAGMENTS: tuple[str, ...] = (
    "password",
    "passwd",
    "secret",
    "token",
    "csrf",
    "api_key",
    "apikey",
)


MASKED_VALUE = "[masked]"


def _is_sensitive_field(key: str) -> bool:
    """True si `key` ressemble à un champ sensible (formulaire/JSON)."""
    lowered = str(key).lower()
    return any(fragment in lowered for fragment in SENSITIVE_FIELD_FRAGMENTS)


def _is_sensitive_header(name: str) -> bool:
    """True si `name` est un header HTTP standardisé sensible."""
    return str(name).lower() in SENSITIVE_HEADER_NAMES


def _mask_mapping(
    mapping: Any,
    *,
    sensitive_check: Callable[[str], bool],
) -> dict[str, Any]:
    """Retourne une copie de `mapping` avec les valeurs sensibles masquées.

    Accepte les `dict`, `HTTPMessage` ou tout objet itérable type
    `(key, value)`. Préserve la structure originale (list vs valeur seule).
    """
    if mapping is None:
        return {}
    items: Iterable[tuple[Any, Any]]
    if hasattr(mapping, "items"):
        items = mapping.items()
    else:
        items = list(mapping)
    masked: dict[str, Any] = {}
    for key, value in items:
        if sensitive_check(key):
            masked[key] = MASKED_VALUE
        else:
            masked[key] = value
    return masked


def resolve_client_ip(remote_addr: str, headers: Any, trusted_proxies: Iterable[str]) -> str:
    """Résout l'IP client en honorant `X-Real-IP` uniquement derrière proxy fiable.

    Règle de sécurité (HTTP-TRUSTED-PROXY-IP-001) : `X-Real-IP` est utilisé
    seulement si `remote_addr` figure exactement dans `trusted_proxies`. Sinon,
    l'IP retournée reste celle observée par le socket — pas d'usurpation
    possible depuis un client direct.

    Comparaison stricte sur la chaîne (pas de plages CIDR). `0.0.0.0` n'a aucune
    signification spéciale : il ne vaut que pour lui-même.
    """
    trusted = frozenset(trusted_proxies or ())
    if not trusted or remote_addr not in trusted:
        return remote_addr
    forwarded: str = (headers.get("X-Real-IP", "") or "").strip()
    if not forwarded:
        return remote_addr
    try:
        ipaddress.ip_address(forwarded)
    except ValueError:
        return remote_addr
    return forwarded


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
    def stream(self) -> BytesIO:
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

    # Contrat d'attributs. `headers` et `json_body` restent `Any` : ce sont des
    # objets de frontière (HTTPMessage du serveur, JSON arbitraire) dont le type
    # précis n'apporte rien au typage interne.
    original_method: str
    method: str
    path: str
    headers: Any
    params: dict[str, list[str]]
    body: dict[str, list[str]]
    json_body: Any
    files: dict[str, UploadedFile]
    route_params: dict[str, str]
    ip: str

    def __init__(self, handler: Any) -> None:
        parsed        = urlparse(cast(str, handler.path))
        self.original_method = handler.command
        self.method   = handler.command
        self.path     = parsed.path
        self.headers  = handler.headers
        self.params   = parse_qs(parsed.query)
        self.files    = {}
        self.ip           = resolve_client_ip(
            handler.client_address[0],
            handler.headers,
            _cfg("trusted_proxies"),
        )
        self.route_params = {}  # injecté par Application.dispatch() pour les routes dynamiques

        if self.method in BODY_METHODS:
            content_type: str = handler.headers.get("Content-Type", "")
            try:
                content_length = int(handler.headers.get("Content-Length", 0))
            except (ValueError, TypeError):
                content_length = 0
            if content_length > _request_size_limit(content_type):
                raise RequestEntityTooLarge(content_length)
            content_length = max(0, content_length)
            raw: bytes = handler.rfile.read(content_length) if content_length else b""

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

        raw_method = self.body.get("_method")
        override = raw_method[0] if raw_method else None
        if not override:
            return

        override = override.upper()
        if override in METHOD_OVERRIDE_TARGETS:
            self.method = override

    # ── Accesseurs publics (API-INSPECTABLE-OBJECTS-CONVENTION-001) ─────────
    #
    # Forme commune : `obj.lookup(key, default=None)`. Renvoient une valeur
    # scalaire (str ou objet métier) et `default` si la clé est absente.
    # Pour les conteneurs qui parsent en `list[str]` (params, body), on
    # retourne la première valeur — l'attribut brut reste accessible si le
    # contrôleur a besoin de toutes les valeurs.

    def query(self, key: str, default: str | None = None) -> str | None:
        """Premier paramètre de query string pour `key` (`?clé=valeur`)."""
        values = self.params.get(key)
        if not values:
            return default
        return values[0]

    def header(self, name: str, default: str | None = None) -> str | None:
        """Header HTTP (recherche insensible à la casse, via HTTPMessage)."""
        if self.headers is None:
            return default
        value = self.headers.get(name)
        return value if value is not None else default

    def form(self, key: str, default: str | None = None) -> str | None:
        """Premier champ de formulaire (`application/x-www-form-urlencoded`
        ou `multipart/form-data`) pour `key`."""
        values = self.body.get(key)
        if not values:
            return default
        return values[0]

    def json(self, key: str, default: Any = None) -> Any:
        """Champ JSON (`application/json`) pour `key`. Renvoie `default` si
        le body JSON est vide ou si la clé est absente.

        N'éclate pas si `json_body` n'est pas un `dict` (par exemple un
        body JSON racine de type liste) — retourne `default` dans ce cas.
        """
        body = self.json_body
        if isinstance(body, dict):
            mapping = cast("dict[str, Any]", body)
            return mapping.get(key, default)
        return default

    def file(self, key: str, default: "UploadedFile | None" = None) -> "UploadedFile | None":
        """Fichier uploadé pour le champ `key` (`UploadedFile` ou `default`)."""
        return self.files.get(key, default)

    def route(self, key: str, default: str | None = None) -> str | None:
        """Paramètre dynamique de route (`/clients/{id}` → `route('id')`)."""
        return self.route_params.get(key, default)

    # ── Vue d'inspection (.data) ────────────────────────────────────────────

    @property
    def data(self) -> dict[str, Any]:
        """Représentation publique stable de la requête, sûre à afficher.

        Toute clé/header sensible (Authorization, Cookie, password, csrf…)
        est remplacée par `[masked]`. Le contenu binaire des fichiers
        uploadés n'est jamais inclus — seuls leurs métadonnées le sont.

        Cette vue est destinée à la pédagogie et au debug en développement.
        Elle ne reflète pas le format wire ; ce n'est pas une sérialisation
        canonique de la requête.
        """
        headers_dict: dict[str, Any] = {}
        if self.headers is not None:
            for key in self.headers.keys():
                value = self.headers.get(key)
                headers_dict[key] = MASKED_VALUE if _is_sensitive_header(key) else value

        files_meta: dict[str, dict[str, Any]] = {}
        for field_name, upload in self.files.items():
            files_meta[field_name] = {
                "filename": upload.filename,
                "size": upload.size,
                "content_type": upload.content_type,
            }

        return {
            "method": self.method,
            "original_method": self.original_method,
            "path": self.path,
            "ip": self.ip,
            "params": dict(self.params),
            "route_params": dict(self.route_params),
            "headers": headers_dict,
            "body": _mask_mapping(self.body, sensitive_check=_is_sensitive_field),
            "json_body": _mask_mapping(self.json_body, sensitive_check=_is_sensitive_field),
            "files": files_meta,
        }

    def __repr__(self) -> str:  # pragma: no cover — purement cosmétique
        return f"<Request {self.method} {self.path}>"

    @staticmethod
    def _parse_multipart(
        content_type: str, raw: bytes
    ) -> tuple[dict[str, list[str]], dict[str, UploadedFile]]:
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
            if not name or not isinstance(name, str):
                continue
            filename = part.get_filename()
            # get_payload(decode=True) renvoie des bytes ; les stubs email étant
            # imprécis (surcharges), on fixe le type pour le typage statique.
            payload = cast(bytes, part.get_payload(decode=True) or b"")
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
