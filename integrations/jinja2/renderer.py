from jinja2 import Environment, FileSystemLoader, select_autoescape
from core.forge import get as _cfg
from core.i18n import trans as _trans
from core.security.csp import get_request_nonce as _get_nonce


def _csp_nonce() -> str:
    """Retourne le nonce CSP de la requête courante, ou une chaîne vide."""
    return _get_nonce() or ""


class Jinja2Renderer:
    def __init__(self, views_dir: str) -> None:
        self._env = Environment(
            loader=FileSystemLoader(views_dir),
            autoescape=select_autoescape(["html"]),
        )
        self._env.globals["url_for"] = self._url_for
        self._env.globals["trans"] = _trans
        self._env.globals["csp_nonce"] = _csp_nonce
        self._env.globals["current_user"] = None
        self._env.globals["is_authenticated"] = False
        self._env.globals["can"] = lambda _code: False
        try:
            from forge_mvc_workflow.jinja import make_workflow_jinja_helpers
            self._env.globals.update(make_workflow_jinja_helpers())
        except ImportError:
            pass

    def render(self, template: str, context: dict) -> str:
        return self._env.get_template(template).render(context)

    @staticmethod
    def _url_for(name: str, **params) -> str:
        router = _cfg("router")
        if router is None:
            raise RuntimeError("Aucun routeur actif pour url_for().")
        return router.url_for(name, **params)
