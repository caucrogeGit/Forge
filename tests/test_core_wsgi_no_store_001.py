"""NO-STORE-ROUTE-FLAG-001 — `Cache-Control: no-store` vient de la route.

La règle vivait dans une liste de chemins codée en dur du serveur de
développement : `{"/login", "/login/mfa", "/logout"}`. L'adaptateur WSGI ne la
connaissait pas, si bien que le déploiement de production servait la page de
connexion **sans** l'en-tête, et qu'un navigateur pouvait la conserver dans son
cache local.

Le cœur ne pouvait pas déduire la règle : `/login` est une route **publique**,
donc indiscernable d'une page ordinaire par le contrat de route. Elle est donc
déclarée, `no_store=True`, et honorée par `Application.dispatch`, point commun
des deux serveurs. C'est le même endroit que le chemin d'erreur et pour la même
raison : une règle posée ailleurs se dédouble et diverge.

Le drapeau ouvre au passage ce que la liste fermait : une application peut
marquer ses propres pages sensibles, une fiche de paie ou un export nominatif,
sans modifier Forge.

Aucun socket n'est ouvert : tout passe par le callable WSGI en mémoire.
"""
from __future__ import annotations

from io import BytesIO
from typing import Any

import pytest

from core.app.application import Application
from core.app.wsgi import create_wsgi_app
from core.http.response import Response
from core.http.router import Router


def _capture():
    capture: dict[str, Any] = {"status": None, "headers": None}

    def start_response(status: str, headers: list[Any], exc_info: Any = None):
        capture["status"] = status
        capture["headers"] = headers
        return lambda chunk: None

    return start_response, capture


def _environ(path: str, method: str = "GET") -> dict[str, Any]:
    return {
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


def _page(_request: Any) -> Response:
    return Response(200, "page")


def _page_avec_son_cache(_request: Any) -> Response:
    return Response(200, "page", headers={"Cache-Control": "private, max-age=60"})


@pytest.fixture
def wsgi_app():
    router = Router()
    router.add("GET", "/login", _page, public=True, csrf=False, no_store=True)
    router.add("GET", "/accueil", _page, public=True, csrf=False)
    router.add("GET", "/mon-cache", _page_avec_son_cache, public=True, csrf=False,
               no_store=True)
    return create_wsgi_app(Application(router, middlewares=[], api_routes_module=None))


def _cache_control(capture: dict[str, Any]) -> str:
    for nom, valeur in capture["headers"]:
        if nom.lower() == "cache-control":
            return valeur
    return ""


def test_une_route_marquee_porte_no_store_sous_wsgi(wsgi_app) -> None:
    """LE test : c'est sous WSGI que l'en-tête manquait, pas en développement."""
    start_response, capture = _capture()
    list(wsgi_app(_environ("/login"), start_response))

    assert "no-store" in _cache_control(capture), (
        "la route déclare `no_store=True` et l'adaptateur WSGI ne pose pas "
        f"l'en-tête : Cache-Control = {_cache_control(capture)!r}"
    )


def test_une_route_ordinaire_ne_le_porte_pas(wsgi_app) -> None:
    """Sans ce contrôle, poser l'en-tête partout ferait passer le précédent.

    Ce serait une régression silencieuse : toutes les pages d'une application
    cesseraient d'être mises en cache, sans que rien ne le signale.
    """
    start_response, capture = _capture()
    list(wsgi_app(_environ("/accueil"), start_response))

    assert "no-store" not in _cache_control(capture)


def test_un_controleur_garde_la_main_sur_sa_directive(wsgi_app) -> None:
    """`setdefault`, pas d'écrasement : un contrôleur sait parfois mieux.

    Une page marquée `no_store` qui pose elle-même `private, max-age=60` a une
    raison de le faire, et le framework n'a pas à la contredire en silence.
    """
    start_response, capture = _capture()
    list(wsgi_app(_environ("/mon-cache"), start_response))

    assert _cache_control(capture) == "private, max-age=60"


def test_le_drapeau_traverse_un_groupe_de_routes() -> None:
    """Un groupe est la façon naturelle de marquer plusieurs pages d'un coup.

    Le drapeau doit y survivre, sans quoi il faudrait le répéter route par
    route et quelqu'un finirait par en oublier une.
    """
    router = Router()
    groupe = router.group("/rh")
    groupe.add("GET", "/paie", _page, public=True, csrf=False, no_store=True)
    app = create_wsgi_app(Application(router, middlewares=[], api_routes_module=None))

    start_response, capture = _capture()
    list(app(_environ("/rh/paie"), start_response))

    assert "no-store" in _cache_control(capture)


def test_les_routes_engendrees_par_make_auth_sont_marquees() -> None:
    """Ce que Forge engendre doit porter la protection, sans geste de l'utilisateur.

    Le gabarit est lu comme du texte : le fichier engendré est du code
    utilisateur, que Forge affiche et n'exécute pas ici.
    """
    from pathlib import Path

    from forge_mvc_testing.source_scan import code_sans_prose

    source = code_sans_prose(
        (Path(__file__).parent.parent / "cli" / "security" / "make_auth.py")
        .read_text(encoding="utf-8")
    )

    debut = source.index("def register_auth_routes")
    bloc = source[debut:debut + 900]

    assert bloc.count("no_store=True") == 3, (
        "les trois routes d'authentification engendrées doivent porter "
        f"`no_store=True` ; trouvé {bloc.count('no_store=True')}"
    )


def test_aucun_serveur_de_dev_ne_garde_sa_liste_de_chemins() -> None:
    """La règle ne doit vivre qu'à un endroit (principe 11).

    Elle vivait dans une liste codée en dur, propre au serveur de
    développement. La garder en plus du drapeau recréerait exactement la
    divergence que ce ticket ferme, et la liste gagnerait silencieusement
    quand les deux ne diraient pas la même chose.
    """
    from pathlib import Path

    racine = Path(__file__).parent.parent
    for rel in ("skeleton/data/app.py", "tests/fixtures/app/app.py"):
        source = (racine / rel).read_text(encoding="utf-8")
        assert "_AUTH_NO_STORE_PATHS" not in source, (
            f"{rel} garde une liste de chemins en propre, alors que la règle "
            "est portée par le drapeau `no_store` de la route"
        )
