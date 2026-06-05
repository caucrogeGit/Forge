"""Starter Chemin anti-traversal — palier 2 du niveau avancé (welcome-files).

Ticket : STARTER-FILE-SAFE-PATH-001.

Le cœur de la sécurité du stockage : empêcher qu'un chemin **sorte** de la racine
d'upload (attaque par traversée de répertoire, ``../../etc/passwd``).
``is_safe_media_path`` répond oui/non ; ``normalize_media_path`` renvoie un chemin
relatif sûr ou **refuse**. Ce sont les primitives que ``serve_media_file`` et les
opt-ins média réutilisent (ADR-020).

  ``index``   — `GET /file-safe-path?path=...` : verdict de sûreté + chemin normalisé.
  ``inspect`` — `GET /file-safe-path/inspect?path=...` : le même résultat en JSON.

Transformation **pure** : aucune lecture/écriture, aucune base de données.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_files import UploadError, is_safe_media_path, normalize_media_path

_DEMO_PATH = "../../etc/passwd"


def _path_view(path: str) -> dict:
    try:
        normalized = normalize_media_path(path)
    except UploadError:
        normalized = None
    return {
        "input": path,
        "is_safe": bool(is_safe_media_path(path)),
        "normalized": normalized,
    }


class FileSafePathController(BaseController):
    """Starter pédagogique : juger la sûreté d'un chemin de fichier."""

    @staticmethod
    def index(request: Request) -> Response:
        path = request.param("path") or _DEMO_PATH
        return BaseController.render(
            "file_safe_path/index.html", context=_path_view(path), request=request
        )

    @staticmethod
    def inspect(request: Request) -> Response:
        path = request.param("path") or _DEMO_PATH
        return Response.json(_path_view(path))
