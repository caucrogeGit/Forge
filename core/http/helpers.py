import os
from core.forge import get as _cfg
from core.http.response import Response
from core.templating.manager import template_manager


def html(template: str, status: int = 200, context: dict = None, *, raw: bool = False) -> Response:
    if raw:
        filepath = os.path.join(_cfg("views_dir"), template)
        with open(filepath, "r", encoding="utf-8") as f:
            return Response(status, f.read())
    return Response(status, template_manager.render(template, context or {}))
