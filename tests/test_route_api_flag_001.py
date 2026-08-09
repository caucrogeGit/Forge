"""CORE-ROUTE-API-FLAG-001 : le drapeau `api` d'une route tient sa promesse.

Le drapeau était déclaré dans `RouteEntry`, propagé par `RouteGroup`, affiché
par `routes:list`, et **lu par aucun code applicatif**. Ses seules lectures dans
tout le dépôt étaient `forge.py`, pour l'afficher, et des tests vérifiant qu'il
valait ce qu'on lui avait passé.

La documentation en promettait pourtant un comportement, « route d'API,
réponses JSON, pas de redirection login ». Une route marquée `api=True`
recevant une requête non authentifiée était traitée comme n'importe quelle
autre, et son client JSON recevait une redirection 302 vers une page HTML de
connexion. Il échouait donc loin de la cause, en tentant de désérialiser du
HTML.

Ce que ces tests verrouillent, cas par cas.

Le drapeau ne gouverne que ce que le framework rend **après** avoir trouvé la
route. Sur un 404 aucune route n'est trouvée, donc rien ne dit que le chemin
visait une API : les 404 et 405 restent en HTML, et c'est une limite, pas un
oubli.

Les cookies posés par le refus doivent survivre à la conversion. C'est le piège
du ticket : `AuthMiddleware` efface le cookie de session quand il détecte une
session orpheline (ADR-080), et reconstruire la réponse sans le reprendre
laisserait cette session ouverte.
"""
from __future__ import annotations

import json

import pytest

from core.app.application import Application
from core.database.errors import DatabaseUnavailableError
from core.http.request import Request
from core.http.response import Response
from core.http.router import Router
from core.templating.manager import template_manager
from integrations.jinja2.renderer import Jinja2Renderer


@pytest.fixture
def gabarits_erreur(tmp_path):
    """Pages d'erreur minimales, sur le gabarit de `test_core_http_405_allow_001`.

    Les cas 404 et 405 rendent du HTML : sans moteur enregistré, `_html` lève et
    le test mesurerait l'absence de gabarit au lieu du comportement visé.
    """
    errors = tmp_path / "errors"
    errors.mkdir()
    (errors / "404.html").write_text("introuvable", encoding="utf-8")
    (errors / "405.html").write_text("methode non autorisee", encoding="utf-8")
    import core.forge as forge

    forge._cfg["views_dir"] = str(tmp_path)  # pyright: ignore[reportPrivateUsage]
    template_manager.register(Jinja2Renderer(str(tmp_path)))
    return tmp_path


def _requete(method: str = "GET", path: str = "/api/x") -> Request:
    from tests.fake_request import FakeRequest

    return FakeRequest(method, path)  # pyright: ignore[reportReturnType]


class _RefusRedirection:
    """Middleware qui refuse comme le fait `AuthMiddleware` : une redirection."""

    def check(self, request: Request) -> Response:
        return Response(302, headers={"Location": "/login"})


class _RefusAvecCookie:
    """Refus qui ferme la session, cas de la session orpheline (ADR-080)."""

    def check(self, request: Request) -> Response:
        reponse = Response(302, headers={"Location": "/login"})
        reponse.headers["Set-Cookie"] = "forge_session=; Max-Age=0; Path=/"
        return reponse


class _RefusInterdit:
    """Refus déjà explicite : son statut ne doit pas être réécrit."""

    def check(self, request: Request) -> Response:
        return Response(403, body=b"<html>interdit</html>")


def _corps(reponse: Response) -> dict[str, str]:
    return json.loads(reponse.body.decode("utf-8"))


# ── La promesse principale : plus de redirection login ───────────────────────


def test_une_route_api_non_authentifiee_rend_401_json() -> None:
    """LE test du ticket. Avant, le client JSON recevait une 302 vers du HTML."""
    routeur = Router()
    routeur.add("GET", "/api/x", lambda r: Response.json({"ok": True}), api=True)
    app = Application(routeur, middlewares=[_RefusRedirection()], api_routes_module=None)

    reponse = app.dispatch(_requete())

    assert reponse.status == 401
    assert reponse.content_type.startswith("application/json")
    assert _corps(reponse) == {"error": "unauthenticated"}
    assert "Location" not in reponse.headers


def test_une_route_ordinaire_redirige_toujours() -> None:
    """Le comportement historique ne bouge pas hors des routes d'API."""
    routeur = Router()
    routeur.add("GET", "/page", lambda r: Response(200), api=False)
    app = Application(routeur, middlewares=[_RefusRedirection()], api_routes_module=None)

    reponse = app.dispatch(_requete(path="/page"))

    assert reponse.status == 302
    assert reponse.headers["Location"] == "/login"


def test_le_cookie_de_fermeture_de_session_survit_a_la_conversion() -> None:
    """Le piège du ticket : perdre ce cookie laisserait la session ouverte."""
    routeur = Router()
    routeur.add("GET", "/api/x", lambda r: Response(200), api=True)
    app = Application(routeur, middlewares=[_RefusAvecCookie()], api_routes_module=None)

    reponse = app.dispatch(_requete())

    assert reponse.status == 401
    assert reponse.headers.get("Set-Cookie") == "forge_session=; Max-Age=0; Path=/"


def test_un_refus_deja_explicite_garde_son_statut() -> None:
    """Seule la forme change : un middleware qui rend 403 doit rendre 403."""
    routeur = Router()
    routeur.add("GET", "/api/x", lambda r: Response(200), api=True)
    app = Application(routeur, middlewares=[_RefusInterdit()], api_routes_module=None)

    reponse = app.dispatch(_requete())

    assert reponse.status == 403
    assert _corps(reponse) == {"error": "forbidden"}


def test_une_route_api_publique_n_est_pas_refusee() -> None:
    """Le drapeau ne doit pas transformer une route ouverte en route protégée."""
    routeur = Router()
    routeur.add("GET", "/api/x", lambda r: Response.json({"ok": True}), api=True, public=True)
    app = Application(routeur, middlewares=[_RefusRedirection()], api_routes_module=None)

    reponse = app.dispatch(_requete())

    assert reponse.status == 200


# ── Les autres réponses du framework sur une route d'API ─────────────────────


def test_une_base_indisponible_rend_503_json() -> None:
    def handler(request: Request) -> Response:
        raise DatabaseUnavailableError("pool saturé")

    routeur = Router()
    routeur.add("GET", "/api/x", handler, api=True, public=True)
    app = Application(routeur, api_routes_module=None)

    reponse = app.dispatch(_requete())

    assert reponse.status == 503
    assert _corps(reponse) == {"error": "service_unavailable"}
    assert reponse.headers["Retry-After"] == "2"


def test_une_erreur_non_geree_rend_500_json_sans_detail() -> None:
    """Aucun détail, même en dev.

    Une page HTML est lue par un humain devant son navigateur, une réponse
    d'API part vers un client qui la journalise, la stocke ou la réexpose. La
    cause reste dans les journaux du serveur.
    """
    def handler(request: Request) -> Response:
        raise RuntimeError("secret de fabrication")

    routeur = Router()
    routeur.add("GET", "/api/x", handler, api=True, public=True)
    app = Application(routeur, api_routes_module=None)

    reponse = app.dispatch(_requete())

    assert reponse.status == 500
    assert _corps(reponse) == {"error": "internal_error"}
    assert "secret de fabrication" not in reponse.body.decode("utf-8")


# ── La limite assumée : avant la résolution, le drapeau ne peut rien ─────────


def test_un_404_reste_en_html_meme_sous_un_prefixe_api(gabarits_erreur) -> None:
    """Aucune route trouvée, donc rien ne dit que le chemin visait une API."""
    routeur = Router()
    routeur.add("GET", "/api/x", lambda r: Response(200), api=True, public=True)
    app = Application(routeur, api_routes_module=None)

    reponse = app.dispatch(_requete(path="/api/inconnu"))

    assert reponse.status == 404
    assert not reponse.content_type.startswith("application/json")


def test_un_405_reste_en_html_avec_son_en_tete_allow(gabarits_erreur) -> None:
    routeur = Router()
    routeur.add("GET", "/api/x", lambda r: Response(200), api=True, public=True)
    app = Application(routeur, api_routes_module=None)

    reponse = app.dispatch(_requete(method="DELETE"))

    assert reponse.status == 405
    assert reponse.headers["Allow"] == "GET"


# ── Le drapeau se propage par les groupes ────────────────────────────────────


def test_un_groupe_api_marque_ses_routes() -> None:
    routeur = Router()
    with routeur.group("/api", api=True, public=False) as g:
        g.add("GET", "/x", lambda r: Response(200))
    app = Application(routeur, middlewares=[_RefusRedirection()], api_routes_module=None)

    reponse = app.dispatch(_requete(path="/api/x"))

    assert reponse.status == 401
    assert _corps(reponse) == {"error": "unauthenticated"}


@pytest.mark.parametrize("statut_refus", [401, 403, 429])
def test_les_statuts_de_refus_non_redirection_sont_conserves(statut_refus: int) -> None:
    class Refus:
        def check(self, request: Request) -> Response:
            return Response(statut_refus, body=b"<html/>")

    routeur = Router()
    routeur.add("GET", "/api/x", lambda r: Response(200), api=True)
    app = Application(routeur, middlewares=[Refus()], api_routes_module=None)

    reponse = app.dispatch(_requete())

    assert reponse.status == statut_refus
    assert reponse.content_type.startswith("application/json")
