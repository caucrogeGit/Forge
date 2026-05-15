from core.auth.password import verify_password
from core.forge import get as _cfg
from core.mvc.controller.base_controller import BaseController
from core.security.hashing import record_attempt, is_rate_limited, verify_password_legacy
from core.security.session import (
    authenticate_session,
    create_session,
    get_session,
    get_session_id,
    delete_session,
)
from mvc.models.auth_model import get_user_by_login


def _check_password(password: str, password_hash: str) -> bool:
    """Vérifie un mot de passe. Argon2id en priorité (core.auth), PBKDF2 en repli legacy."""
    if verify_password(password, password_hash):
        return True
    return verify_password_legacy(password, password_hash)


class AuthController(BaseController):

    @staticmethod
    def login_form(request):
        session_id = get_session_id(request)
        session = get_session(session_id) if session_id else None
        if not session:
            session_id = create_session()
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
    def login(request):
        if is_rate_limited(request.ip):
            return BaseController.render("errors/429.html", 429, base=None)

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
            and _check_password(password, utilisateur["PasswordHash"])
        ):
            nouveau_id = authenticate_session(session_id, utilisateur)
            if not nouveau_id:
                return BaseController.render("errors/403.html", 403, base=None)

            response = BaseController.redirect("/suivi")
            response.headers["Set-Cookie"] = (
                f"session_id={nouveau_id}; Path=/; HttpOnly; SameSite=Strict; Secure"
            )
            return response

        record_attempt(request.ip)
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
    def logout(request):
        session_id = get_session_id(request)
        session = get_session(session_id)
        csrf_token = request.body.get("csrf_token", [None])[0]
        if not session or csrf_token != session.get("csrf_token"):
            return BaseController.render("errors/403.html", 403, base=None)

        delete_session(session_id)
        response = BaseController.redirect("/login")
        response.headers["Set-Cookie"] = (
            "session_id=; Path=/; HttpOnly; SameSite=Strict; Secure; Max-Age=0"
        )
        return response
