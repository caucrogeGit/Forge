from jinja2 import BaseLoader, Environment, FileSystemLoader, TemplateNotFound, select_autoescape
from core.forge import get as _cfg
from core.mvc.controller.registry import iter_jinja_template_loaders
from core.security.csp import get_request_nonce as _get_nonce
from core.templating.errors import TemplateNotFoundError


class _OptinAwareLoader(BaseLoader):
    """Loader composite : `mvc/views/` du projet, puis les loaders d'opt-in (ADR-046).

    La liste des loaders d'opt-in est relue à CHAQUE résolution via le registre
    du cœur (`iter_jinja_template_loaders`). L'ordre d'import des paquets n'a donc
    aucune importance : un opt-in qui s'enregistre après la construction du
    renderer est quand même pris en compte. Le dossier du projet vient en premier,
    ce qui permet de surcharger un template par défaut d'un paquet en plaçant un
    fichier de même chemin dans `mvc/views/`.
    """

    def __init__(self, views_dir: str) -> None:
        self._project = FileSystemLoader(views_dir)

    def _loaders(self):
        return [self._project, *iter_jinja_template_loaders()]

    def get_source(self, environment, template):
        for loader in self._loaders():
            try:
                return loader.get_source(environment, template)
            except TemplateNotFound:
                continue
        raise TemplateNotFound(template)

    def list_templates(self):
        seen = set()
        names = []
        for loader in self._loaders():
            try:
                loader_names = loader.list_templates()
            except TypeError:
                continue
            for name in loader_names:
                if name not in seen:
                    seen.add(name)
                    names.append(name)
        return names


def _csp_nonce() -> str:
    """Retourne le nonce CSP de la requête courante, ou une chaîne vide."""
    return _get_nonce() or ""


def _default_trans(key, *_args, **_kwargs):
    """Repli i18n du noyau : retourne la clé telle quelle.

    Le noyau expose toujours un global `trans` pour que les templates générés
    (CRUD, pages publiques) rendent sans erreur même sans traduction. Quand
    l'opt-in `forge-mvc-i18n` (ADR-027) est installé, le renderer remplace ce
    repli par la vraie fonction `trans()` qui charge les catalogues JSON.
    """
    return key


class Jinja2Renderer:
    def __init__(self, views_dir: str) -> None:
        self._views_dir = views_dir
        self._env = Environment(
            loader=_OptinAwareLoader(views_dir),
            autoescape=select_autoescape(["html"]),
        )
        self._env.globals["url_for"] = self._url_for
        self._env.globals["csp_nonce"] = _csp_nonce
        self._env.globals["current_user"] = None
        self._env.globals["is_authenticated"] = False
        self._env.globals["can"] = lambda _code: False
        # i18n : repli no-op du noyau (retourne la clé) ; l'opt-in
        # forge-mvc-i18n (ADR-027) l'enrichit avec les vrais catalogues.
        self._env.globals["trans"] = _default_trans
        try:
            from forge_mvc_i18n import trans as _trans
            self._env.globals["trans"] = _trans
        except ImportError:
            pass
        try:
            from forge_mvc_workflow.jinja import make_workflow_jinja_helpers
            self._env.globals.update(make_workflow_jinja_helpers())
        except ImportError:
            pass

    def render(self, template: str, context: dict) -> str:
        try:
            tmpl = self._env.get_template(template)
        except TemplateNotFound as exc:
            # Conversion vers l'exception Forge — découple le moteur Jinja2
            # de l'erreur publique exposée par les contrôleurs et le helper
            # `core.http.helpers.html`. Voir DX-RENDER-ERROR-001.
            raise TemplateNotFoundError(template, self._views_dir) from exc
        return tmpl.render(context)

    @staticmethod
    def _url_for(name: str, **params) -> str:
        router = _cfg("router")
        if router is None:
            raise RuntimeError("Aucun routeur actif pour url_for().")
        return router.url_for(name, **params)
