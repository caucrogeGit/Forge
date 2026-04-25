from jinja2 import Environment, FileSystemLoader, select_autoescape
from core.forge import get as _cfg


class Jinja2Renderer:
    def __init__(self, views_dir: str) -> None:
        self._env = Environment(
            loader=FileSystemLoader(views_dir),
            autoescape=select_autoescape(["html"]),
        )
        self._env.globals["url_for"] = self._url_for

    def render(self, template: str, context: dict) -> str:
        return self._env.get_template(template).render(context)

    @staticmethod
    def _url_for(name: str, **params) -> str:
        router = _cfg("router")
        if router is None:
            raise RuntimeError("Aucun routeur actif pour url_for().")
        return router.url_for(name, **params)
