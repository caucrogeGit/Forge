# pyright: strict
from __future__ import annotations
import importlib.metadata as _md
from typing import Any
from core.forge import get as _cfg
from core.templating.contracts import Renderer

_forge_version_cache: "str | None" = None


def _forge_version() -> str:
    """Version installée du paquet `forge-mvc` (mise en cache, vide si absente)."""
    global _forge_version_cache
    if _forge_version_cache is None:
        try:
            _forge_version_cache = _md.version("forge-mvc")
        except _md.PackageNotFoundError:
            _forge_version_cache = ""
    return _forge_version_cache


class TemplateManager:
    def __init__(self) -> None:
        self._renderer: Renderer | None = None

    def register(self, renderer: Renderer) -> None:
        self._renderer = renderer

    def render(self, template: str, context: "dict[str, Any]") -> str:
        if self._renderer is None:
            raise RuntimeError(
                "Aucun renderer enregistré — appeler template_manager.register() au démarrage."
            )
        # `app_name` (config APP_NAME) est injecté dans tout contexte de template
        # pour être disponible partout — layout partagé, pages, pages d'erreur —
        # quel que soit le chemin de rendu (render(), _html() direct, erreurs).
        # setdefault : un contrôleur peut toujours surcharger.
        merged = dict(context)
        merged.setdefault("app_name", _cfg("app_name"))
        # `forge_version` (version du paquet forge-mvc) est injecté de la même
        # façon, disponible dans tout template (ex. bandeau d'accueil, pied de page).
        merged.setdefault("forge_version", _forge_version())
        return self._renderer.render(template, merged)


template_manager = TemplateManager()
