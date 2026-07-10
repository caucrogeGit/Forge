# pyright: strict
"""`forge make:auth` — scaffold du flux de connexion (FORGE-5).

Le cœur redirige les routes protégées vers `/login` (codé en dur) et fournit le
backend d'authentification (`core.auth.session`), mais aucune route, aucun
contrôleur ni aucune vue de login n'étaient scaffoldés. `make:auth` comble ce
trou : il génère un contrôleur d'authentification, une vue de login, **affiche** les
routes à ajouter dans `mvc/routes/__init__.py` (mode « Forge affiche », charte §7), et
**injecte** le bouton Connexion/Déconnexion dans la barre de nav. L'injection est
chirurgicale et idempotente : `layouts/base.html` inclut `partials/nav.html`, qui porte
un ancrage `{# forge:auth-nav #}` ; make:auth y insère le bloc bouton sans toucher aux
autres liens (même principe qu'`opt-in:enable` qui injecte par ancrage dans routes/registry).
Sans ancrage, il n'écrit pas et affiche le bloc à coller. Le bouton s'appuie sur
`is_authenticated`, injecté dans tout template par `BaseController.render`.

Périmètre v1 : socle standard `users` (email / password_hash / is_active, produit
par `forge auth:init`), avec défense anti-fixation de session (régénération +
cookie) et limitation anti-bruteforce par IP (principe §7 « sécuriser par
défaut »). MFA et audit sont laissés en extension (voir le contrôleur de
référence `tests/fixtures/app/mvc/controllers/auth_controller.py`).

`auth:init` reste centré sur les comptes/SQL ; `make:auth` scaffolde l'UI/le flux.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


AUTH_CONTROLLER = '''\
"""Contrôleur d'authentification (généré par forge make:auth).

Flux de connexion sur le socle `users` (forge auth:init) : formulaire, POST de
login (défense anti-fixation de session + limitation anti-bruteforce par IP), et
logout. Le loader charge un utilisateur par email pour `authenticate_user` (cœur).
"""
from core.auth.rate_limit import is_login_rate_limited, record_login_attempt
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

        # Anti-bruteforce : plafonne les tentatives échouées par IP (fenêtre glissante).
        if is_login_rate_limited(request.ip):
            response = BaseController.render("auth/login.html", context={
                "csrf_token": session.get("csrf_token", ""),
                "erreur": "Trop de tentatives. Réessayez dans un instant.",
            })
            set_session_cookie(response, session_id)
            return response

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

        # Échec : enregistre la tentative pour la limitation par IP.
        record_login_attempt(request.ip)
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
{% extends "layouts/base.html" %}
{% from "components/forms.html" import field, submit %}
{% from "components/ui.html" import alert %}
{% block title %}Connexion{% endblock %}
{% block content %}
<div class="max-w-sm mx-auto">
    <h1 class="text-[28px] font-extrabold tracking-tight mb-6 text-center">Connexion</h1>

    {% if erreur %}
    <div class="mb-4">{{ alert(erreur, level="error") }}</div>
    {% endif %}

    <form method="POST" action="/login" class="space-y-4">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        {{ field(name="email", label="Email", type="email", required=True) }}
        {{ field(name="password", label="Mot de passe", type="password", required=True) }}
        {{ submit(label="Se connecter") }}
    </form>
</div>
{% endblock %}
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


# Ancrage et marqueurs pour l'injection chirurgicale du bouton dans partials/nav.html
# (même principe qu'opt-in:enable qui injecte par ancrage dans routes/registry).
AUTH_NAV_ANCHOR = "{# forge:auth-nav #}"
AUTH_NAV_START = "{# forge:auth-nav:start #}"

AUTH_NAV_BLOCK = '''\
{# forge:auth-nav:start #}
{% from "components/ui.html" import button %}
{% if is_authenticated %}
<form method="post" action="/logout">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    {{ button("Déconnexion", variant="secondary", type="submit") }}
</form>
{% else %}
{{ button("Connexion", variant="primary", href="/login") }}
{% endif %}
{# forge:auth-nav:end #}'''


# Contenu de partials/nav.html quand le projet n'en a pas (ancien squelette).
NAV_DEFAULT = (
    "{#\n"
    "  Barre de navigation du projet, intégrée par layouts/base.html.\n"
    "  Ajoutez ici vos liens de navigation.\n"
    "#}\n"
    + AUTH_NAV_ANCHOR + "\n"
    + AUTH_NAV_BLOCK + "\n"
)


ROUTE_BLOCK = "\n".join([
    "Branchement à ajouter dans mvc/routes/__init__.py :",
    "─" * 70,
    "  from mvc.routes.auth_routes import register_auth_routes",
    "  register_auth_routes(router)",
])


# Affiché uniquement en repli, si partials/nav.html n'a pas l'ancrage.
NAV_BLOCK = "\n".join([
    "partials/nav.html n'a pas l'ancrage {# forge:auth-nav #} : ajoutez vous-même",
    "le bouton dans votre barre de nav (base.html inclut partials/nav.html) :",
    "─" * 70,
    AUTH_NAV_BLOCK,
])


@dataclass
class MakeAuthResult:
    created: list[str]
    skipped: list[str]
    modified: list[str]
    route_block: str = ROUTE_BLOCK
    nav_block: str = NAV_BLOCK
    nav_needs_manual: bool = False


def _write_if_new(path: Path, content: str, result: MakeAuthResult) -> None:
    rel = path.as_posix()
    if path.exists():
        result.skipped.append(rel)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    result.created.append(rel)


def _integrate_auth_nav(nav_path: Path, result: MakeAuthResult) -> None:
    """Injecte le bouton Connexion/Déconnexion dans partials/nav.html, de façon
    chirurgicale et idempotente (par ancrage `{# forge:auth-nav #}`), en préservant
    les liens que l'utilisateur y a ajoutés. Absent : le fichier est créé. Déjà
    injecté : rien. Sans ancrage : on n'écrit pas, on affiche (repli, charte §7).
    """
    rel = nav_path.as_posix()
    if not nav_path.exists():
        nav_path.parent.mkdir(parents=True, exist_ok=True)
        nav_path.write_text(NAV_DEFAULT, encoding="utf-8")
        result.created.append(rel)
        return
    content = nav_path.read_text(encoding="utf-8")
    if AUTH_NAV_START in content:
        result.skipped.append(rel)  # déjà intégré
        return
    if AUTH_NAV_ANCHOR in content:
        new = content.replace(AUTH_NAV_ANCHOR, AUTH_NAV_ANCHOR + "\n" + AUTH_NAV_BLOCK, 1)
        nav_path.write_text(new, encoding="utf-8")
        result.modified.append(rel)
        return
    result.nav_needs_manual = True


def make_auth(root: Path | None = None) -> MakeAuthResult:
    base = root or Path.cwd()
    result = MakeAuthResult(created=[], skipped=[], modified=[])
    _write_if_new(base / "mvc" / "controllers" / "auth_controller.py", AUTH_CONTROLLER, result)
    _write_if_new(base / "mvc" / "views" / "auth" / "login.html", AUTH_LOGIN_VIEW, result)
    # ADR-068 : les routes du contrôleur auth vivent dans leur propre fichier ;
    # mvc/routes/__init__.py ne fait que les brancher (affiché ci-dessous).
    _write_if_new(base / "mvc" / "routes" / "auth_routes.py", AUTH_ROUTES_FILE, result)
    # Bouton Connexion/Déconnexion injecté dans la barre de nav (chirurgical, ancré).
    _integrate_auth_nav(base / "mvc" / "views" / "partials" / "nav.html", result)
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
    for path in result.modified:
        print(f"[MODIFIE] {path}")
    for path in result.skipped:
        print(f"[PRESERVE] {path}")
    print()
    print(result.route_block)
    if result.nav_needs_manual:
        print()
        print(result.nav_block)
    print()
    print("Prérequis : forge auth:init puis forge db:apply (table users).")
    print("Créez un compte : forge auth:user:create")
