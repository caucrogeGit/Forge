"""CORE-WSGI-HEALTH-PARITY-001 — la sonde `/health` répond aussi sous WSGI.

`GET /health` → `200 {"status": "ok"}` figure au contrat de stabilité
(`docs/release/stability-contract.md`) comme surface publique garantie.

Elle n'était pourtant servie que par le serveur de développement. Sous WSGI,
seul chemin de production supporté, elle répondait **404**. Un superviseur
branché dessus derrière Gunicorn déclarait morte une application qui servait.

Le défaut a tenu parce que les deux tests de `test_health_endpoint_001.py`
exercent le même serveur : l'un appelle `do_GET` sur le handler du squelette,
l'autre lance `python app.py` en sous-processus. Aucun ne traverse le callable
WSGI. C'est la leçon du chantier précédent, où le serveur de développement
servait des fichiers que son jumeau WSGI refusait.

Ces tests passent donc par `create_wsgi_app`, et par lui seul.
"""
from __future__ import annotations

import io
import json
import sys
from typing import Any

import pytest

from core.app.wsgi import create_wsgi_app
from core.http.health import HEALTH_BODY, HEALTH_PATH, health_response
from core.http.response import Response

pytestmark = pytest.mark.smoke


class _ApplicationQuiRefuseTout:
    """Application dont le routage répond 404 à tout.

    La sonde doit être servie **avant** le dispatch. Une application qui
    n'expose aucune route est donc le cas décisif : si `/health` répond 200
    ici, c'est que le chemin WSGI la traite lui-même.
    """

    def __init__(self) -> None:
        self.chemins_dispatches: "list[str]" = []

    def dispatch(self, request: Any) -> Response:
        self.chemins_dispatches.append(request.path)
        return Response(404, b"introuvable", "text/plain; charset=utf-8")


def _appeler(app: Any, chemin: str, methode: str = "GET") -> "tuple[str, bytes, dict[str, str]]":
    """Joue une requête WSGI complète et retourne (statut, corps, en-têtes)."""
    environ: "dict[str, Any]" = {
        "REQUEST_METHOD": methode,
        "PATH_INFO": chemin,
        "QUERY_STRING": "",
        "SERVER_NAME": "127.0.0.1",
        "SERVER_PORT": "8000",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "wsgi.url_scheme": "http",
        "wsgi.input": io.BytesIO(b""),
        "wsgi.errors": sys.stderr,
    }
    vu: "dict[str, Any]" = {}

    def start_response(statut: str, entetes: "list[tuple[str, str]]") -> None:
        vu["statut"] = statut
        vu["entetes"] = entetes

    corps = b"".join(app(environ, start_response))
    entetes = {cle.lower(): valeur for cle, valeur in vu["entetes"]}
    return vu["statut"], corps, entetes


# ── Le cas mesuré ────────────────────────────────────────────────────────────

def test_health_repond_200_sous_wsgi() -> None:
    """Le défaut exact : 404 sous Gunicorn, 200 sur le serveur de dev."""
    app = create_wsgi_app(_ApplicationQuiRefuseTout())

    statut, corps, _ = _appeler(app, HEALTH_PATH)

    assert statut == "200 OK"
    assert json.loads(corps) == {"status": "ok"}


def test_health_annonce_du_json() -> None:
    """Le contrat porte sur le corps ET sur le type."""
    app = create_wsgi_app(_ApplicationQuiRefuseTout())

    _, _, entetes = _appeler(app, HEALTH_PATH)

    assert entetes["content-type"] == "application/json"
    assert entetes["content-length"] == str(len(HEALTH_BODY))


def test_health_ne_passe_pas_par_le_routage() -> None:
    """Servie avant le dispatch, comme sur le serveur de dev.

    Sans cela, la sonde dépendrait des routes du projet, et un projet neuf
    sans route la perdrait.
    """
    application = _ApplicationQuiRefuseTout()
    app = create_wsgi_app(application)

    _appeler(app, HEALTH_PATH)

    assert application.chemins_dispatches == []


def test_le_reste_continue_d_etre_route() -> None:
    """Contre-épreuve : sans elle, on pourrait court-circuiter tout le routage."""
    application = _ApplicationQuiRefuseTout()
    app = create_wsgi_app(application)

    statut, _, _ = _appeler(app, "/une-page")

    assert statut == "404 Not Found"
    assert application.chemins_dispatches == ["/une-page"]


def test_health_garde_les_entetes_de_securite() -> None:
    """La sonde passe par le même adaptateur, donc le même socle d'en-têtes."""
    app = create_wsgi_app(_ApplicationQuiRefuseTout())

    _, _, entetes = _appeler(app, HEALTH_PATH)

    assert "x-frame-options" in entetes
    assert "content-security-policy" in entetes


# ── Une seule source, pas deux ───────────────────────────────────────────────

def test_les_deux_serveurs_lisent_la_meme_reponse() -> None:
    """La cause retirée (règle A).

    Tant que la réponse était un littéral inscrit dans chaque serveur, rien
    n'empêchait les deux de diverger. Ce test tient la source unique.
    """
    reponse = health_response()

    assert reponse.status == 200
    assert reponse.body == HEALTH_BODY
    assert reponse.content_type == "application/json"


def test_le_squelette_ne_reecrit_pas_la_reponse() -> None:
    """Le serveur de développement doit consommer `core.http.health`.

    Un littéral `{"status": "ok"}` réintroduit dans `app.py` recréerait
    exactement le défaut corrigé ici, sans que rien ne le signale.
    """
    from pathlib import Path

    source = (Path(__file__).resolve().parent.parent
              / "skeleton" / "data" / "app.py").read_text(encoding="utf-8")

    assert "is_health_request" in source
    assert "health_response()" in source
    assert '{"status": "ok"}' not in source
