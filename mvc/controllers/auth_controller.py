from core.auth.audit import (
    AUTH_EVENT_LOGIN_FAILED,
    AUTH_EVENT_LOGIN_SUCCESS,
    AUTH_EVENT_LOGOUT,
    AUTH_EVENT_MFA_REQUIRED,
    AUTH_EVENT_USER_DISABLED,
    safe_log_auth_event,
)
try:
    from forge_mvc_mfa import is_mfa_enabled, start_mfa_challenge
    from mvc.models.mfa_model import get_active_mfa_factors
    _MFA_AVAILABLE = True
except ImportError:
    _MFA_AVAILABLE = False

    def is_mfa_enabled(_factors):  # type: ignore[override]
        return False

    def start_mfa_challenge(_request, _user):  # type: ignore[override]
        pass

    def get_active_mfa_factors(_user_id):  # type: ignore[override]
        return []

from core.auth.password import hash_password, verify_password
from core.auth.session import login_user
from core.auth.user import AuthUser
from core.forge import get as _cfg
from core.mvc.controller.base_controller import BaseController
from core.security.cookies import clear_session_cookie, set_session_cookie
from core.security.hashing import record_attempt, is_rate_limited, verify_password_legacy
from core.sessions.manager import get_session_store as _get_session_store
from core.security.session import (
    get_session,
    get_session_id,
    delete_session,
)
from mvc.models.auth_model import get_user_by_login, update_password_hash


def mfa_available() -> bool:
    return _MFA_AVAILABLE


def _check_password(password: str, password_hash: str) -> bool:
    """Vérifie un mot de passe. Argon2id en priorité (core.auth), PBKDF2 en repli legacy."""
    if verify_password(password, password_hash):
        return True
    return verify_password_legacy(password, password_hash)


class AuthController(BaseController):

    @staticmethod
    def login_form(request):
        session_id = get_session_id(request)
        session    = get_session(session_id) if session_id else None
        if not session:
            session_id = _get_session_store().create()
            session    = get_session(session_id)
        response = BaseController.render("auth/login.html", base=None, context={
            "csrf_token": session["csrf_token"],
            "app_name"  : _cfg("app_name"),
            "erreur"    : "",
        })
        set_session_cookie(response, session_id)
        return response

    @staticmethod
    def login(request):
        if is_rate_limited(request.ip):
            return BaseController.render("errors/429.html", 429, base=None)

        session_id = get_session_id(request)
        session    = get_session(session_id)
        if not session:
            return BaseController.render("errors/403.html", 403, base=None)

        login    = request.body.get("login", [""])[0]
        password = request.body.get("password", [""])[0]

        utilisateur = get_user_by_login(login)
        if (
            utilisateur
            and utilisateur.get("Actif")
            and _check_password(password, utilisateur["PasswordHash"])
        ):
            if not utilisateur["PasswordHash"].startswith("$argon2id$"):
                try:
                    update_password_hash(utilisateur["UtilisateurId"], hash_password(password))
                except Exception:
                    pass  # migration non bloquante

            _email = (
                utilisateur.get("Email")
                or utilisateur.get("Login")
                or str(utilisateur["UtilisateurId"])
            )
            auth_user = AuthUser(
                id=utilisateur["UtilisateurId"],
                email=_email,
                password_hash=utilisateur["PasswordHash"],
                is_active=True,
            )

            mfa_factors = get_active_mfa_factors(utilisateur["UtilisateurId"])
            if is_mfa_enabled(mfa_factors):
                start_mfa_challenge(request, auth_user)
                safe_log_auth_event(
                    AUTH_EVENT_MFA_REQUIRED,
                    user_id=utilisateur["UtilisateurId"],
                    ip_address=request.ip,
                )
                response = BaseController.redirect("/login/mfa")
                set_session_cookie(response, session_id)
                return response

            login_user(request, auth_user)
            nouveau_id = _get_session_store().regenerate(session_id)
            safe_log_auth_event(
                AUTH_EVENT_LOGIN_SUCCESS,
                user_id=utilisateur["UtilisateurId"],
                ip_address=request.ip,
            )
            response = BaseController.redirect("/")
            set_session_cookie(response, nouveau_id)
            return response

        if utilisateur is not None and not utilisateur.get("Actif"):
            safe_log_auth_event(
                AUTH_EVENT_USER_DISABLED,
                user_id=utilisateur["UtilisateurId"],
                ip_address=request.ip,
            )
        else:
            safe_log_auth_event(AUTH_EVENT_LOGIN_FAILED, ip_address=request.ip)
        record_attempt(request.ip)
        return BaseController.render("auth/login.html", base=None, context={
            "csrf_token": session["csrf_token"],
            "app_name"  : _cfg("app_name"),
            "erreur"    : "Identifiant ou mot de passe incorrect.",
        })

    @staticmethod
    def logout(request):
        session_id = get_session_id(request)
        session    = get_session(session_id)
        if not session:
            return BaseController.render("errors/403.html", 403, base=None)
        from core.sessions.keys import SESSION_KEY_USER, session_get as _sg
        utilisateur_data = _sg(session, SESSION_KEY_USER) if session else None
        user_id = utilisateur_data.get("id") if isinstance(utilisateur_data, dict) else None
        safe_log_auth_event(AUTH_EVENT_LOGOUT, user_id=user_id, ip_address=request.ip)
        delete_session(session_id)
        response = BaseController.redirect("/login")
        clear_session_cookie(response)
        return response
