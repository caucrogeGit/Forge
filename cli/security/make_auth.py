# pyright: strict
"""`forge make:auth` — scaffold du flux de connexion (FORGE-5).

Le cœur redirige les routes protégées vers `/login` (codé en dur) et fournit le
backend d'authentification (`core.auth.session`), mais aucune route, aucun
contrôleur ni aucune vue de login n'étaient scaffoldés. `make:auth` comble ce
trou : il génère un contrôleur d'authentification, une vue de login, et **affiche**
les routes à ajouter dans `mvc/routes/__init__.py` (mode « Forge affiche », charte §7 : pas
de réécriture silencieuse d'un fichier utilisateur).

Périmètre v1 : socle standard `users` (email / password_hash / is_active, produit
par `forge auth:init`), avec défense anti-fixation de session (régénération +
cookie). MFA, rate-limit et audit sont laissés en extension (voir le contrôleur de
référence `tests/fixtures/app/mvc/controllers/auth_controller.py`).

`auth:init` reste centré sur les comptes/SQL ; `make:auth` scaffolde l'UI/le flux.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


AUTH_CONTROLLER = '''\
"""Contrôleur d'authentification (généré par forge make:auth).

Flux de connexion sur le socle `users` (forge auth:init) : formulaire, POST de
login (avec défense anti-fixation de session), et logout. Le loader charge un
utilisateur par email pour `authenticate_user` (cœur).
"""
from core.auth.session import authenticate_user, login_user, logout_user
from core.database.db import fetch_one
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController
from core.security.cookies import clear_session_cookie, set_session_cookie
from core.security.session import get_session, get_session_id, regenerate_session
from core.sessions.manager import get_session_store


def load_user_by_email(email: str):
    """Charge un utilisateur du socle `users` par email (loader d'authenticate_user)."""
    return fetch_one(
        "SELECT id, email, password_hash, is_active FROM users WHERE email = ?",
        (email,),
    )


class AuthController(BaseController):

    @staticmethod
    def login_form(request: Request) -> Response:
        # Garantit une session (donc un csrf_token) même pour un visiteur anonyme.
        session_id = get_session_id(request)
        if not session_id or get_session(session_id) is None:
            session_id = get_session_store().create()
        session = get_session(session_id) or {}
        response = BaseController.render("auth/login.html", context={
            "csrf_token": session.get("csrf_token", ""),
            "erreur": "",
        })
        set_session_cookie(response, session_id)
        return response

    @staticmethod
    def login(request: Request) -> Response:
        session_id = get_session_id(request)
        session = get_session(session_id) if session_id else None
        if session_id is None or session is None:
            return BaseController.redirect("/login")

        email = request.form("email", "")
        password = request.form("password", "")
        user = authenticate_user(email, password, load_user_by_email)
        if user is not None:
            login_user(request, user)
            # Défense anti-fixation : nouvel identifiant de session + réémission du cookie.
            new_id = regenerate_session(session_id)
            response = BaseController.redirect("/")
            set_session_cookie(response, new_id)
            return response

        response = BaseController.render("auth/login.html", context={
            "csrf_token": session.get("csrf_token", ""),
            "erreur": "Identifiant ou mot de passe incorrect.",
        })
        set_session_cookie(response, session_id)
        return response

    @staticmethod
    def logout(request: Request) -> Response:
        logout_user(request)
        response = BaseController.redirect("/login")
        clear_session_cookie(response)
        return response
'''


AUTH_LOGIN_VIEW = '''\
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Connexion</title>
    <link rel="icon" href="/static/favicon.png" type="image/png">
    <link rel="stylesheet" href="/static/tailwind.css">
</head>
<body class="bg-gray-100 min-h-screen flex items-center justify-center">
    <div class="bg-white rounded shadow p-8 w-full max-w-sm">
        <h1 class="text-2xl font-bold text-gray-800 mb-6 text-center">Connexion</h1>

        {% if erreur %}
        <p class="text-red-600 text-sm mb-4">{{ erreur }}</p>
        {% endif %}

        <form method="POST" action="/login" class="space-y-4">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">

            <div>
                <label class="block text-sm font-medium text-gray-700">Email</label>
                <input type="email" name="email" required autofocus
                    class="mt-1 w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
            </div>

            <div>
                <label class="block text-sm font-medium text-gray-700">Mot de passe</label>
                <input type="password" name="password" required
                    class="mt-1 w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
            </div>

            <button type="submit" class="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700">
                Se connecter
            </button>
        </form>
    </div>
</body>
</html>
'''


AUTH_ROUTES_FILE = '''\
"""Routes du contrôleur AuthController (ADR-068)."""
from core.http.router import Router
from mvc.controllers.auth_controller import AuthController


def register_auth_routes(router: Router) -> None:
    # Login public (accessible sans authentification) ; logout protégé.
    router.add("GET", "/login", AuthController.login_form, public=True, name="auth-login_form")
    router.add("POST", "/login", AuthController.login, public=True, name="auth-login")
    router.add("POST", "/logout", AuthController.logout, name="auth-logout")
'''


ROUTE_BLOCK = "\n".join([
    "Branchement à ajouter dans mvc/routes/__init__.py :",
    "─" * 70,
    "  from mvc.routes.auth_routes import register_auth_routes",
    "  register_auth_routes(router)",
])


@dataclass
class MakeAuthResult:
    created: list[str]
    skipped: list[str]
    route_block: str = ROUTE_BLOCK


def _write_if_new(path: Path, content: str, result: MakeAuthResult) -> None:
    rel = path.as_posix()
    if path.exists():
        result.skipped.append(rel)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    result.created.append(rel)


def make_auth(root: Path | None = None) -> MakeAuthResult:
    base = root or Path.cwd()
    result = MakeAuthResult(created=[], skipped=[])
    _write_if_new(base / "mvc" / "controllers" / "auth_controller.py", AUTH_CONTROLLER, result)
    _write_if_new(base / "mvc" / "views" / "auth" / "login.html", AUTH_LOGIN_VIEW, result)
    # ADR-068 : les routes du contrôleur auth vivent dans leur propre fichier ;
    # mvc/routes/__init__.py ne fait que les brancher (affiché ci-dessous).
    _write_if_new(base / "mvc" / "routes" / "auth_routes.py", AUTH_ROUTES_FILE, result)
    return result


def main(argv: list[str] | None = None) -> None:
    import sys

    args = list(sys.argv[1:] if argv is None else argv)
    if [a for a in args if a != "make:auth"]:
        print("Usage : forge make:auth")
        raise SystemExit(1)

    result = make_auth()
    for path in result.created:
        print(f"[CREE] {path}")
    for path in result.skipped:
        print(f"[PRESERVE] {path}")
    print()
    print(result.route_block)
    print()
    print("Prérequis : forge auth:init puis forge db:apply (table users).")
    print("Créez un compte : forge auth:user:create")
