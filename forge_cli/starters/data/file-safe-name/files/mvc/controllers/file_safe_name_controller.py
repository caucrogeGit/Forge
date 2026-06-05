"""Starter Assainir un nom de fichier — palier 1 du niveau avancé (welcome-files).

Ticket : STARTER-FILE-SAFE-NAME-001.

On entre dans les **primitives** de forge-mvc-files — la boîte à outils que les
opt-ins média composent (ADR-020). ``secure_filename`` transforme un nom fourni
par l'utilisateur (potentiellement piégé : chemins, caractères spéciaux) en un
nom **sûr**, dépourvu de toute composante de répertoire.

  ``index``   — `GET /file-safe-name?name=...` : montre le nom assaini.
  ``inspect`` — `GET /file-safe-name/inspect?name=...` : le même résultat en JSON.

Transformation **pure** : aucune écriture, aucune base de données.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_files import UploadError, secure_filename

_DEMO_NAME = "../Mon Dossier/Rapport Final!.PDF"


def _safe_view(name: str) -> dict:
    try:
        return {"input": name, "safe": secure_filename(name), "error": None}
    except UploadError as exc:
        return {"input": name, "safe": None, "error": str(exc)}


class FileSafeNameController(BaseController):
    """Starter pédagogique : assainir un nom de fichier utilisateur."""

    @staticmethod
    def index(request: Request) -> Response:
        name = request.param("name") or _DEMO_NAME
        return BaseController.render(
            "file_safe_name/index.html", context=_safe_view(name), request=request
        )

    @staticmethod
    def inspect(request: Request) -> Response:
        name = request.param("name") or _DEMO_NAME
        return Response.json(_safe_view(name))
