"""CORE-WSGI-CSP-NONCE-001 — le nonce CSP existe aussi sous WSGI.

Le nonce CSP est documenté comme un réglage de **production** :
`docs/deployment/production-security.md` et `docs/deployment/deployment.md`
prescrivent `APP_CSP_NONCE_ENABLED=true`, puis
`<script nonce="{{ csp_nonce() }}">` dans les gabarits.

Il n'existait que sur le serveur de développement. L'adaptateur WSGI appelait
`build_csp_header(None)` et n'établissait aucun nonce de requête.

## Ce que cela produisait

    serveur de dev   script-src 'self' 'nonce-abc123'   le script s'exécute
    WSGI (Gunicorn)  script-src 'self'                  le script est bloqué

Le script inline était donc **silencieusement inerte en production**. Pas
d'erreur serveur, pas de page cassée : la fonctionnalité ne marchait
simplement pas, et rien ne le disait. Le développeur l'avait vue fonctionner
chez lui.

Les tests E2E du nonce existaient, et ils passaient : ils lancent le **serveur
de développement**. C'est la démonstration la plus nette de la règle apprise
à `/health` et à `request.data` : un test qui passe par le jumeau ne prouve
rien sur la production.

Aucun socket n'est ouvert : tout passe par le callable WSGI en mémoire.
"""
from __future__ import annotations

import re
from io import BytesIO
from typing import Any

import pytest

from core.app.application import Application
from core.app.wsgi import create_wsgi_app
from core.http.response import Response
from core.http.router import Router
from core.security import csp as _csp

#: `nonce-<valeur>` dans une directive `script-src`.
_MOTIF_NONCE = re.compile(r"script-src[^;]*'nonce-([A-Za-z0-9_\-]+)'")


def _capture():
    capture: dict[str, Any] = {"status": None, "headers": None}

    def start_response(status: str, headers: list[Any], exc_info: Any = None):
        capture["status"] = status
        capture["headers"] = headers
        return lambda chunk: None

    return start_response, capture


def _environ(path: str = "/") -> dict[str, Any]:
    return {
        "REQUEST_METHOD": "GET",
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


#: Ce que le nonce vaut **pendant** le rendu, tel qu'un gabarit le verrait.
_vu_au_rendu: list[str] = []


def controleur(request: Any) -> Response:
    """Relève `csp_nonce()` au moment du rendu, comme le ferait un gabarit."""
    _vu_au_rendu.append(_csp.get_request_nonce() or "")
    return Response(200, "ok")


@pytest.fixture(autouse=True)
def releve_vide():
    _vu_au_rendu.clear()
    yield
    _vu_au_rendu.clear()


@pytest.fixture
def wsgi_app():
    router = Router()
    router.add("GET", "/", controleur, public=True, csrf=False)
    return create_wsgi_app(Application(router, middlewares=[], api_routes_module=None))


def _csp_de(capture: dict[str, Any]) -> str:
    for nom, valeur in capture["headers"]:
        if nom.lower() == "content-security-policy":
            return valeur
    return ""


@pytest.fixture
def nonce_actif(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("APP_CSP_NONCE_ENABLED", "true")
    yield


@pytest.fixture
def nonce_inactif(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("APP_CSP_NONCE_ENABLED", "false")
    yield


# ── Le nonce activé ──────────────────────────────────────────────────────────


def test_la_csp_wsgi_porte_un_nonce_quand_il_est_active(wsgi_app, nonce_actif) -> None:
    """LE test : le réglage est documenté pour la production, il doit y agir."""
    start_response, capture = _capture()
    list(wsgi_app(_environ(), start_response))

    entete = _csp_de(capture)

    assert _MOTIF_NONCE.search(entete), (
        "la CSP servie par l'adaptateur WSGI ne porte aucun nonce alors que "
        f"`APP_CSP_NONCE_ENABLED=true` : {entete}"
    )


def test_le_gabarit_voit_le_meme_nonce_que_l_entete(wsgi_app, nonce_actif) -> None:
    """La propriété qui rend le mécanisme utile, et la seule qui compte.

    Un nonce dans l'en-tête que le gabarit ne connaît pas ne sert à rien : le
    script portera une autre valeur, ou aucune, et sera bloqué. Les deux
    doivent venir de la même requête.
    """
    start_response, capture = _capture()
    list(wsgi_app(_environ(), start_response))

    correspondance = _MOTIF_NONCE.search(_csp_de(capture))
    assert correspondance is not None
    dans_entete = correspondance.group(1)

    assert _vu_au_rendu == [dans_entete], (
        f"le gabarit a vu « {_vu_au_rendu} » et l'en-tête porte « {dans_entete} » : "
        "le script inline sera bloqué"
    )


def test_deux_requetes_recoivent_deux_nonces(wsgi_app, nonce_actif) -> None:
    """Un nonce réutilisé perd sa raison d'être, qui est d'être imprévisible."""
    valeurs: list[str] = []
    for _ in range(2):
        start_response, capture = _capture()
        list(wsgi_app(_environ(), start_response))
        correspondance = _MOTIF_NONCE.search(_csp_de(capture))
        assert correspondance is not None
        valeurs.append(correspondance.group(1))

    assert valeurs[0] != valeurs[1], f"nonce identique sur deux requêtes : {valeurs[0]}"


def test_le_nonce_ne_survit_pas_a_la_requete(wsgi_app, nonce_actif) -> None:
    """Le stockage est propre au fil d'exécution, et les fils sont réutilisés.

    Sans remise à zéro, le nonce d'une requête fuiterait dans la CSP de la
    suivante, servie sur le même fil. C'est la raison d'être du gestionnaire
    de contexte `request_nonce`.
    """
    start_response, _ = _capture()
    list(wsgi_app(_environ(), start_response))

    assert _csp.get_request_nonce() is None, (
        "le nonce est resté posé après la réponse : la requête suivante servie "
        "sur ce fil hériterait de sa valeur"
    )


# ── Le nonce désactivé, qui est le défaut ────────────────────────────────────


def test_sans_le_reglage_la_csp_reste_stricte_et_sans_nonce(wsgi_app, nonce_inactif) -> None:
    """Le défaut ne change pas : `script-src 'self'`, sans `unsafe-inline`.

    Sans ce test, poser un nonce systématiquement ferait passer les précédents
    tout en modifiant le comportement par défaut de toutes les applications.
    """
    start_response, capture = _capture()
    list(wsgi_app(_environ(), start_response))

    entete = _csp_de(capture)

    assert "script-src 'self'" in entete
    assert "nonce-" not in entete
    assert "unsafe-inline" not in entete
    assert _vu_au_rendu == [""], (
        f"`csp_nonce()` doit rendre une chaîne vide quand le réglage est absent : {_vu_au_rendu}"
    )
