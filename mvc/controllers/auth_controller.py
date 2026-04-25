from core.forge import get as _cfg
from core.mvc.controller.base_controller import BaseController
from core.security.session import (
    creer_session,
    get_session,
    get_session_id,
    supprimer_session,
    authentifier_session,
)
from core.security.hashing import verifier_mot_de_passe, enregistrer_tentative, est_limite
from mvc.models.auth_model import get_user_by_login


class AuthController(BaseController):

    @staticmethod
    def login_form(request):
        session_id = get_session_id(request)
        session    = get_session(session_id) if session_id else None
        if not session:
            session_id = creer_session()
            session    = get_session(session_id)
        response = BaseController.render("auth/login.html", base=None, context={
            "csrf_token": session["csrf_token"],
            "app_name"  : _cfg("app_name"),
            "erreur"    : "",
        })
        response.headers["Set-Cookie"] = (
            f"session_id={session_id}; Path=/; HttpOnly; SameSite=Strict; Secure"
        )
        return response

    @staticmethod
    def login(request):
        if est_limite(request.ip):
            return BaseController.render("errors/429.html", 429, base=None)

        session_id = get_session_id(request)
        session    = get_session(session_id)
        csrf_token = request.body.get("csrf_token", [None])[0]
        if not session or csrf_token != session.get("csrf_token"):
            return BaseController.render("errors/403.html", 403, base=None)

        login    = request.body.get("login", [""])[0]
        password = request.body.get("password", [""])[0]

        utilisateur = get_user_by_login(login)
        if (
            utilisateur
            and utilisateur.get("Actif")
            and verifier_mot_de_passe(password, utilisateur["PasswordHash"])
        ):
            nouveau_id = authentifier_session(session_id, utilisateur)
            if not nouveau_id:
                return BaseController.render("errors/403.html", 403, base=None)
            response = BaseController.redirect("/")
            response.headers["Set-Cookie"] = (
                f"session_id={nouveau_id}; Path=/; HttpOnly; SameSite=Strict; Secure"
            )
            return response

        enregistrer_tentative(request.ip)
        return BaseController.render("auth/login.html", base=None, context={
            "csrf_token": session["csrf_token"],
            "app_name"  : _cfg("app_name"),
            "erreur"    : "Identifiant ou mot de passe incorrect.",
        })

    @staticmethod
    def logout(request):
        session_id = get_session_id(request)
        session    = get_session(session_id)
        csrf_token = request.body.get("csrf_token", [None])[0]
        if not session or csrf_token != session.get("csrf_token"):
            return BaseController.render("errors/403.html", 403, base=None)
        supprimer_session(session_id)
        response = BaseController.redirect("/login")
        response.headers["Set-Cookie"] = (
            "session_id=; Path=/; HttpOnly; SameSite=Strict; Secure; Max-Age=0"
        )
        return response
