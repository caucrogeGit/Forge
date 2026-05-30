from core.auth import login_user, logout_user, verify_password
from core.forge import get as _cfg
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController
from core.sessions.manager import get_session_store as _get_session_store
from core.security.session import get_session, get_session_id, delete_session
from mvc.models.auth_model import build_auth_user, get_user_by_login


class AuthController(BaseController):
    """Contrôleur applicatif explicite pour login et logout."""

    @staticmethod
    def login_form(request: Request) -> Response:
        session_id = get_session_id(request)
        session = get_session(session_id) if session_id else None
        if not session:
            session_id = _get_session_store().create()
            session = get_session(session_id)

        response = BaseController.render(
            "auth/login.html",
            base=None,
            context={
                "csrf_token": session["csrf_token"],
                "app_name": _cfg("app_name"),
                "erreur": "",
                "login": "",
            },
        )
        response.headers["Set-Cookie"] = (
            f"session_id={session_id}; Path=/; HttpOnly; SameSite=Strict; Secure"
        )
        return response

    @staticmethod
    def login(request: Request) -> Response:
        session_id = get_session_id(request)
        session = get_session(session_id)
        csrf_token = request.body.get("csrf_token", [None])[0]
        if not session or csrf_token != session.get("csrf_token"):
            return BaseController.render("errors/403.html", 403, base=None)

        login = request.body.get("login", [""])[0]
        password = request.body.get("password", [""])[0]

        utilisateur = get_user_by_login(login)
        if (
            utilisateur
            and utilisateur.get("Actif")
            and verify_password(password, utilisateur["PasswordHash"])
        ):
            auth_user = build_auth_user(utilisateur)
            login_user(request, auth_user)
            response = BaseController.redirect("/dashboard")
            response.headers["Set-Cookie"] = (
                f"session_id={session_id}; Path=/; HttpOnly; SameSite=Strict; Secure"
            )
            return response

        return BaseController.render(
            "auth/login.html",
            base=None,
            context={
                "csrf_token": session["csrf_token"],
                "app_name": _cfg("app_name"),
                "erreur": "Identifiant ou mot de passe incorrect.",
                "login": login,
            },
        )

    @staticmethod
    def logout(request: Request) -> Response:
        session_id = get_session_id(request)
        session = get_session(session_id)
        csrf_token = request.body.get("csrf_token", [None])[0]
        if not session or csrf_token != session.get("csrf_token"):
            return BaseController.render("errors/403.html", 403, base=None)

        logout_user(request)
        delete_session(session_id)
        response = BaseController.redirect("/login")
        response.headers["Set-Cookie"] = (
            "session_id=; Path=/; HttpOnly; SameSite=Strict; Secure; Max-Age=0"
        )
        return response
