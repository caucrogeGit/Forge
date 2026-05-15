import json as _json
import os
from core.forge import get as _cfg
from core.http.response import Response
from core.templating.manager import template_manager

_JSON_CONTENT_TYPE = "application/json; charset=utf-8"


def html(template: str, status: int = 200, context: dict = None, *, raw: bool = False) -> Response:
    if raw:
        filepath = os.path.join(_cfg("views_dir"), template)
        with open(filepath, "r", encoding="utf-8") as f:
            return Response(status, f.read())
    return Response(status, template_manager.render(template, context or {}))


def json_response(data, status: int = 200) -> Response:
    try:
        body = _json.dumps(data, ensure_ascii=False)
    except TypeError as exc:
        raise ValueError(f"Données JSON non sérialisables : {exc}") from exc
    return Response(status, body, _JSON_CONTENT_TYPE)


def api_success(data=None, status: int = 200, meta=None) -> Response:
    payload = {"success": True, "data": data}
    if meta is not None:
        payload["meta"] = meta
    return json_response(payload, status)


def api_error(message: str, status: int = 400, code: str = "error", details=None) -> Response:
    error = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    return json_response({"success": False, "error": error}, status)
