import json as _json
from core.forge import get as _cfg
from core.http.helpers import html as _html
from core.http.response import Response
from core.templating.manager import template_manager
from core.security.session import get_session_id, get_session, set_flash, get_utilisateur


class BaseController:
    """
    Classe de base pour tous les contrôleurs.

    Méthodes disponibles :
        render()        → génère une réponse HTML via Jinja2
        redirect()      → génère une réponse 302
        redirect_to_route() → redirige via une route nommée
        redirect_with_flash() → stocke un flash puis redirige
        not_found()     → génère une réponse 404
        json()          → génère une réponse application/json
        set_flash()     → stocke un message flash dans la session
        csrf_token()    → retourne le token CSRF de la session
        include()       → charge et retourne le HTML d'un partial Jinja2
        body()          → extrait les données du formulaire POST (dict plat)
        json_body()     → extrait les données JSON du body POST (dict)
        form_context()  → construit le contexte commun à tout formulaire
    """

    @staticmethod
    def render(template, status=200, context=None, base="layouts/base.html", *, request=None, raw=False):
        if not raw and request is not None:
            ctx = dict(context) if context else {}
            if "csrf_token" not in ctx:
                ctx["csrf_token"] = BaseController.csrf_token(request)
            context = ctx
        return _html(template, status, context, raw=raw)

    @staticmethod
    def redirect(location, *, request=None, flash=None, level="success"):
        if request is not None and flash:
            BaseController.set_flash(request, flash, level)
        return Response(302, headers={"Location": location})

    @staticmethod
    def redirect_with_flash(request, location, message, level="success"):
        """Flux POST-Redirect-GET : message flash puis redirection."""
        BaseController.set_flash(request, message, level)
        return BaseController.redirect(location)

    @staticmethod
    def redirect_to_route(name, *, request=None, flash=None, level="success", **params):
        router = _cfg("router")
        if router is None:
            raise RuntimeError("Aucun routeur actif pour redirect_to_route().")
        return BaseController.redirect(
            router.url_for(name, **params),
            request=request,
            flash=flash,
            level=level,
        )

    @staticmethod
    def not_found():
        return _html("errors/404.html", 404)

    @staticmethod
    def bad_request(context=None):
        return _html("errors/400.html", 400, context)

    @staticmethod
    def forbidden(context=None):
        return _html("errors/403.html", 403, context)

    @staticmethod
    def validation_error(template="errors/422.html", context=None, *, request=None):
        return BaseController.render(template, 422, context, request=request)

    @staticmethod
    def server_error(context=None):
        return _html("errors/500.html", 500, context)

    @staticmethod
    def set_flash(request, message, level="success"):
        set_flash(get_session_id(request), message, level)

    @staticmethod
    def csrf_token(request):
        """Retourne le token CSRF de la session courante."""
        session_id = get_session_id(request)
        session    = get_session(session_id)
        return session.get("csrf_token", "") if session else ""

    @staticmethod
    def current_user(request):
        """Retourne l'utilisateur courant stocké en session."""
        return get_utilisateur(request)

    @staticmethod
    def include(partial, context=None):
        """Charge et retourne le HTML d'un partial Jinja2."""
        return template_manager.render(partial, context or {})

    @staticmethod
    def json(data, status=200):
        """Génère une réponse JSON."""
        return Response(status, _json.dumps(data, ensure_ascii=False),
                        "application/json; charset=utf-8")

    @staticmethod
    def body(request):
        """Extrait les données du formulaire POST sous forme de dict plat."""
        return {k: v[0] for k, v in request.body.items()}

    @staticmethod
    def json_body(request):
        """Retourne le body JSON parsé (dict). Vide si Content-Type != application/json."""
        return request.json_body

    @staticmethod
    def render_form(template, request, data, status=200, erreurs=""):
        """Raccourci : render + form_context en une seule ligne."""
        return BaseController.render(template, status,
                                     context=BaseController.form_context(request, data, erreurs),
                                     request=request)

    @staticmethod
    def form_context(request, data, erreurs=""):
        """
        Construit le contexte commun à tout formulaire (add/edit).

        Args :
            request (Request) : requête courante
            data    (dict)    : données du formulaire à afficher
            erreurs (str)     : message d'erreur de validation — défaut vide
        """
        return {
            **data,
            "csrf_token": BaseController.csrf_token(request),
            "erreurs"   : erreurs,
        }
