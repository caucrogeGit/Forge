"""CORE-WSGI-AUTH-GATE-001 — la protection d'accès tient sous WSGI réel.

Le sous-système d'authentification comptait cinquante-six fonctions publiques,
et **aucune** n'était atteinte par un appel WSGI réel. Tout était vérifié soit
en appel direct, soit à travers `FakeRequest`, soit en appelant
`Application.dispatch` sans passer par l'adaptateur.

C'est la lacune la plus coûteuse possible, parce que la propriété qui compte
ici n'est pas « le middleware rend une redirection » mais « **le contrôleur
protégé ne s'exécute pas** ». La première se vérifie en appelant le middleware,
la seconde exige de parcourir toute la chaîne.

Un middleware qui rendrait la bonne réponse tout en laissant le contrôleur
tourner passerait tous les tests unitaires du dépôt. La différence n'est
visible qu'ici, et elle sépare une redirection d'une fuite de données.

Aucun socket n'est ouvert : tout passe par le callable WSGI en mémoire.
"""
from __future__ import annotations

import json
from io import BytesIO
from typing import Any

import pytest

from core.app.application import Application
from core.app.wsgi import create_wsgi_app
from core.http.response import Response
from core.http.router import Router
from core.security.middleware import AuthMiddleware

#: Ce que le contrôleur protégé rendrait s'il s'exécutait. Une chaîne
#: reconnaissable, pour que sa présence dans une réponse soit sans ambiguïté.
_SECRET = "dossier-medical-de-madame-durand"

#: Témoin d'exécution : un booléen dit ce qu'un code de statut ne dit pas.
_execute: dict[str, bool] = {"controleur": False}


def _capture():
    capture: dict[str, Any] = {"status": None, "headers": None}

    def start_response(status: str, headers: list[Any], exc_info: Any = None):
        capture["status"] = status
        capture["headers"] = headers
        return lambda chunk: None

    return start_response, capture


def _environ(path: str, method: str = "GET", cookie: str | None = None) -> dict[str, Any]:
    env: dict[str, Any] = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": "",
        "SERVER_NAME": "test",
        "SERVER_PORT": "80",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "REMOTE_ADDR": "127.0.0.1",
        "wsgi.input": BytesIO(b""),
        "wsgi.errors": BytesIO(),
        "wsgi.url_scheme": "http",
    }
    if cookie is not None:
        env["HTTP_COOKIE"] = cookie
    return env


def controleur_protege(request: Any) -> Response:
    """Ce contrôleur ne doit **jamais** s'exécuter sans session valide."""
    _execute["controleur"] = True
    return Response(200, _SECRET)


def controleur_api_protege(request: Any) -> Response:
    _execute["controleur"] = True
    return Response.json({"dossier": _SECRET})


def controleur_public(request: Any) -> Response:
    return Response(200, "page de connexion")


@pytest.fixture(autouse=True)
def temoin():
    _execute["controleur"] = False
    yield
    _execute["controleur"] = False


def _app(*, user_loader: Any = None):
    router = Router()
    router.add("GET", "/dossier", controleur_protege, public=False, csrf=False)
    router.add("GET", "/api/dossier", controleur_api_protege, public=False, csrf=False, api=True)
    router.add("GET", "/login", controleur_public, public=True, csrf=False)
    middleware = AuthMiddleware(login_url="/login", user_loader=user_loader)
    return create_wsgi_app(
        Application(router, middlewares=[middleware], api_routes_module=None)
    )


@pytest.fixture
def wsgi_app():
    return _app()


# ── La propriété qui compte ──────────────────────────────────────────────────


def test_le_controleur_protege_ne_s_execute_pas_sans_session(wsgi_app) -> None:
    """LE test : ce n'est pas le code de statut qui importe, c'est l'exécution.

    Un middleware qui rendrait la bonne redirection tout en laissant le
    contrôleur tourner passerait tous les tests unitaires du dépôt. Le témoin
    booléen dit ce qu'un `302` ne dit pas.
    """
    start_response, capture = _capture()

    corps = b"".join(wsgi_app(_environ("/dossier"), start_response))

    assert _execute["controleur"] is False, (
        "le contrôleur protégé s'est exécuté sans session : la redirection "
        "masque une fuite de données"
    )
    assert capture["status"].startswith("302")
    assert _SECRET.encode() not in corps


def test_la_redirection_pointe_la_page_de_connexion(wsgi_app) -> None:
    """Une redirection sans `Location` laisse le navigateur sans destination."""
    start_response, capture = _capture()
    list(wsgi_app(_environ("/dossier"), start_response))

    entetes = {nom.lower(): valeur for nom, valeur in capture["headers"]}

    assert entetes.get("location") == "/login"


def test_une_route_publique_reste_accessible(wsgi_app) -> None:
    """Sans ce test, tout refuser passerait le précédent."""
    start_response, capture = _capture()

    corps = b"".join(wsgi_app(_environ("/login"), start_response))

    assert capture["status"].startswith("200")
    assert b"page de connexion" in corps


# ── Le drapeau `api` sur une route protégée ──────────────────────────────────


def test_une_api_protegee_rend_du_json_et_non_une_redirection(wsgi_app) -> None:
    """Une redirection HTML vers `/login` est inexploitable par un client d'API.

    Il la suit, reçoit une page de connexion en `200`, et croit avoir réussi.
    Le drapeau `api` existe pour cela ; ici il est exercé sur le chemin complet.
    """
    start_response, capture = _capture()

    corps = b"".join(wsgi_app(_environ("/api/dossier"), start_response))

    assert _execute["controleur"] is False
    assert not capture["status"].startswith("302"), (
        "une route d'API ne doit pas rendre une redirection de navigateur"
    )
    entetes = {nom.lower(): valeur for nom, valeur in capture["headers"]}
    assert "application/json" in entetes.get("content-type", "")
    charge = json.loads(corps.decode("utf-8"))
    assert _SECRET not in json.dumps(charge)


# ── La session orpheline (ADR-080) ───────────────────────────────────────────


def _session_avec_utilisateur(user_id: int) -> str:
    """Ouvre une session serveur portant un id d'auth, et rend son cookie."""
    from core.auth.session import AUTH_USER_ID_SESSION_KEY
    from core.sessions.access import SESSION_COOKIE_NAME
    from core.sessions.manager import get_session_store

    store = get_session_store()
    session_id = store.create({AUTH_USER_ID_SESSION_KEY: user_id})
    # Le cookie s'appelle `__Host-session_id`, pas `session_id`. Employer le
    # mauvais nom rendrait la session invisible, et le test « pas d'accès »
    # passerait alors pour la mauvaise raison : il ne prouverait plus rien.
    return f"{SESSION_COOKIE_NAME}={session_id}"


def test_la_session_de_test_est_bien_vue_par_le_coeur(temoin) -> None:
    """Contrôle de montage, sans lequel les tests suivants passeraient à vide.

    Une session que le cœur ne voit pas se comporte comme une absence de
    session : le contrôleur est refusé, et les tests « pas d'accès » passent
    sans rien prouver. Le nom du cookie est `__Host-session_id` ; s'en tromper
    est silencieux.
    """
    from core.auth.session import AUTH_USER_ID_SESSION_KEY
    from core.sessions.access import SESSION_COOKIE_NAME, get_session

    cookie = _session_avec_utilisateur(4242)
    identifiant = cookie.split("=", 1)[1]

    assert cookie.startswith(SESSION_COOKIE_NAME + "=")
    donnees = get_session(identifiant)
    assert donnees is not None, "la session créée doit être relisible"
    assert donnees.get(AUTH_USER_ID_SESSION_KEY) == 4242


def _compte(user_id: int) -> dict[str, Any]:
    """Une ligne d'utilisateur complète, telle qu'un loader applicatif doit la rendre.

    `password_hash` est obligatoire : l'omettre fait rendre `None` à
    `current_user`, donc refuser l'accès. C'est le piège traité par
    `test_un_loader_incomplet_laisse_une_trace`.
    """
    return {
        "id": user_id,
        "login": "durand",
        "password_hash": "$argon2id$factice",
        "is_active": True,
    }


def test_une_session_orpheline_ne_donne_pas_acces(temoin) -> None:
    """Un compte supprimé laisse un id en session qui ne pointe plus rien.

    C'est la situation de l'ADR-080, et elle est plus dangereuse qu'une absence
    de session : l'id **est** là, donc un contrôle par simple présence laisse
    passer. Le sujet doit être validé, pas seulement son identifiant.
    """
    wsgi_app = _app(user_loader=lambda _uid: None)  # aucun compte ne répond
    cookie = _session_avec_utilisateur(4242)
    start_response, capture = _capture()

    corps = b"".join(wsgi_app(_environ("/dossier", cookie=cookie), start_response))

    assert _execute["controleur"] is False, (
        "un id d'auth orphelin a suffi à exécuter le contrôleur protégé"
    )
    assert capture["status"].startswith("302")
    assert _SECRET.encode() not in corps


def test_une_session_orpheline_est_fermee(temoin) -> None:
    """Fermer la session évite de reboucler indéfiniment sur `/login`.

    Sans la purge du cookie, le navigateur repart avec la même session morte à
    chaque tour, et l'utilisateur ne peut plus se connecter.
    """
    wsgi_app = _app(user_loader=lambda _uid: None)
    cookie = _session_avec_utilisateur(4242)
    start_response, capture = _capture()

    list(wsgi_app(_environ("/dossier", cookie=cookie), start_response))

    cookies = [v for nom, v in capture["headers"] if nom.lower() == "set-cookie"]
    assert cookies, "la session orpheline doit être purgée du navigateur"
    assert any("session_id=" in c for c in cookies)


def test_un_sujet_valide_ouvre_l_acces(temoin) -> None:
    """La contrepartie : tout refuser ferait passer les deux tests précédents."""
    wsgi_app = _app(user_loader=lambda uid: _compte(uid))
    cookie = _session_avec_utilisateur(4242)
    start_response, capture = _capture()

    corps = b"".join(wsgi_app(_environ("/dossier", cookie=cookie), start_response))

    assert capture["status"].startswith("200"), (
        f"un sujet valide doit accéder à la ressource, obtenu {capture['status']}"
    )
    assert _execute["controleur"] is True
    assert _SECRET.encode() in corps


def test_un_loader_incomplet_laisse_une_trace(temoin, caplog) -> None:
    """Un loader qui oublie un champ produisait une boucle de redirection muette.

    La session est valide, le compte existe, et l'utilisateur ne peut plus
    entrer. Sans trace, on cherche le défaut du côté de la session ou du
    cookie, c'est-à-dire partout sauf là où il est.

    Le refus reste le bon comportement : c'est le silence qui ne l'était pas.
    La branche voisine, celle du loader qui lève, journalisait déjà.
    """
    import logging

    incomplet = {"id": 4242, "login": "durand", "is_active": True}  # sans password_hash
    wsgi_app = _app(user_loader=lambda _uid: incomplet)
    cookie = _session_avec_utilisateur(4242)
    start_response, capture = _capture()

    with caplog.at_level(logging.WARNING, logger="core.auth.session"):
        list(wsgi_app(_environ("/dossier", cookie=cookie), start_response))

    assert capture["status"].startswith("302"), "le refus reste le bon comportement"
    assert _execute["controleur"] is False
    # `getMessage()` applique les arguments du journal, ce que `.message`
    # laisse en attente ; les composer à la main casse dès qu'un `%` figure
    # dans le texte.
    messages = " ".join(enregistrement.getMessage() for enregistrement in caplog.records)
    assert "password_hash" in messages, (
        f"le champ manquant doit être nommé, sinon la trace n'aide pas :\n{messages}"
    )
