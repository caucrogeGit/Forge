from __future__ import annotations
from core.templating.contracts import Renderer


class TemplateManager:
    def __init__(self) -> None:
        self._renderer: Renderer | None = None

    def register(self, renderer: Renderer) -> None:
        self._renderer = renderer

    def render(self, template: str, context: dict) -> str:
        if self._renderer is None:
            raise RuntimeError(
                "Aucun renderer enregistré — appeler template_manager.register() au démarrage."
            )
        return self._renderer.render(template, context)


template_manager = TemplateManager()
