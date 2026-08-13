"""HSTS-TWIN-DIVERGENCE-001 — les deux serveurs n'émettent pas HSTS pareil, et c'est écrit.

Le serveur de développement pose `Strict-Transport-Security` sur toutes les
réponses ; l'adaptateur WSGI ne le pose que si `wsgi.url_scheme` vaut `https`.

Les deux comportements sont délibérés et documentés séparément. Le défaut était
que **la documentation générale affirmait le premier sans mentionner le
second** : deux pages annonçaient l'en-tête « sur toutes les réponses, y
compris en dev ».

La conséquence n'est pas cosmétique. Derrière un proxy inverse qui termine le
TLS, ce qui est le déploiement décrit par le guide de mise en production,
`wsgi.url_scheme` vaut `http` : Forge n'émet donc pas l'en-tête, et c'est au
proxy de le poser. Un exploitant qui lisait la page d'audit croyait disposer
d'une protection que son déploiement n'avait pas.

Ce fichier fixe la divergence pour qu'elle reste **délibérée** : si l'un des
deux serveurs change, un test le dit, plutôt que la documentation vieillisse
une fois de plus sous le code.
"""
from __future__ import annotations

import ast
from io import BytesIO
from pathlib import Path
from typing import Any

from forge_mvc_testing.source_scan import code_sans_prose

PROJECT_ROOT = Path(__file__).parent.parent

_HSTS = "strict-transport-security"


def _capture():
    capture: dict[str, Any] = {"status": None, "headers": None}

    def start_response(status: str, headers: list[Any], exc_info: Any = None):
        capture["status"] = status
        capture["headers"] = headers
        return lambda chunk: None

    return start_response, capture


def _environ(scheme: str) -> dict[str, Any]:
    return {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": "/",
        "QUERY_STRING": "",
        "SERVER_NAME": "test",
        "SERVER_PORT": "80",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "REMOTE_ADDR": "127.0.0.1",
        "wsgi.input": BytesIO(b""),
        "wsgi.errors": BytesIO(),
        "wsgi.url_scheme": scheme,
    }


def _app():
    from core.app.application import Application
    from core.app.wsgi import create_wsgi_app
    from core.http.response import Response
    from core.http.router import Router

    router = Router()
    router.add("GET", "/", lambda _r: Response(200, "ok"), public=True, csrf=False)
    return create_wsgi_app(Application(router, middlewares=[], api_routes_module=None))


def _entetes(scheme: str) -> set[str]:
    start_response, capture = _capture()
    list(_app()(_environ(scheme), start_response))
    return {nom.lower() for nom, _ in capture["headers"]}


# ── Le comportement des deux serveurs ────────────────────────────────────────


def test_le_wsgi_n_emet_pas_hsts_en_clair() -> None:
    """LE cas du déploiement réel : Gunicorn derrière un proxy qui termine le TLS.

    `wsgi.url_scheme` vaut alors `http`, et l'en-tête n'est pas émis. Émettre
    HSTS quand on ignore si la réponse voyagera en clair reviendrait à
    l'affirmer sans le savoir.
    """
    assert _HSTS not in _entetes("http")


def test_le_wsgi_emet_hsts_en_https() -> None:
    """La contrepartie : ne jamais l'émettre ferait passer le test précédent."""
    assert _HSTS in _entetes("https")


def test_le_serveur_de_dev_emet_hsts_sans_condition() -> None:
    """L'autre jumeau, dont le choix est inverse et tout aussi délibéré.

    Le serveur de développement sait s'il sert du TLS (`APP_SSL_ENABLED`) et
    considère l'en-tête inoffensif en local. Le relevé passe par l'arbre
    syntaxique du squelette, le serveur n'étant pas démarrable ici.
    """
    source = (PROJECT_ROOT / "skeleton" / "data" / "app.py").read_text(encoding="utf-8")
    arbre = ast.parse(source)

    appels = [
        noeud
        for noeud in ast.walk(arbre)
        if isinstance(noeud, ast.Call)
        and isinstance(noeud.func, ast.Name)
        and noeud.func.id == "apply_security_headers"
    ]
    assert appels, "le serveur de développement doit poser le socle de sécurité"

    valeurs = [
        mot.value
        for appel in appels
        for mot in appel.keywords
        if mot.arg == "include_hsts"
    ]
    assert valeurs, "`include_hsts` doit être passé explicitement, jamais laissé au défaut"
    assert all(isinstance(v, ast.Constant) and v.value is True for v in valeurs), (
        "le serveur de développement pose HSTS sans condition ; si ce choix "
        "change, la documentation d'audit et celle de l'authentification "
        "doivent changer avec lui"
    )


def test_l_adaptateur_wsgi_conditionne_hsts_au_schema() -> None:
    """Le pendant du test précédent, relevé sur le code plutôt que sur la réponse.

    Le contrôle par la réponse ne dirait pas **d'où** vient la condition. Un
    jour où l'adaptateur poserait `include_hsts=True` en dur, les deux tests de
    comportement plus haut le verraient ; celui-ci nomme la cause.
    """
    source = (PROJECT_ROOT / "core" / "app" / "wsgi.py").read_text(encoding="utf-8")
    code = code_sans_prose(source)

    assert "include_hsts=is_https" in code, (
        "l'adaptateur WSGI doit conditionner HSTS au schéma de la requête"
    )


# ── La documentation qui décrit la divergence ────────────────────────────────


def test_la_documentation_ne_promet_pas_hsts_sans_condition() -> None:
    """Deux pages l'annonçaient « sur toutes les réponses », sans réserve.

    Un exploitant qui lisait cela croyait disposer d'une protection que son
    déploiement n'avait pas. C'est la troisième fois de ce cycle qu'une page
    affirme ce que le code ne fait plus, ou pas partout.
    """
    fautes: list[str] = []
    for relatif in ("docs/reference/audit-auth.md", "docs/features/auth.md"):
        texte = (PROJECT_ROOT / relatif).read_text(encoding="utf-8")
        for numero, ligne in enumerate(texte.splitlines(), start=1):
            if "Strict-Transport-Security" not in ligne:
                continue
            if "toutes les réponses" in ligne and "wsgi" not in ligne.lower():
                fautes.append(f"{relatif}:{numero}")

    assert not fautes, (
        "ces lignes promettent HSTS sans condition, alors que l'adaptateur WSGI "
        "ne l'émet qu'en HTTPS :\n  " + "\n  ".join(fautes)
    )
