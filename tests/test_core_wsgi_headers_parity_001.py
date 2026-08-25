"""CORE-WSGI-HEADERS-PARITY-001 — les deux serveurs lisent les en-têtes pareil.

Relevé sur le terrain (SéquenCiel, ticket 66) : un en-tête absent rendait `None`
sur un serveur et `""` sur l'autre, si bien que onze contrôleurs ne rendaient
plus que leur fragment. Le symptôme rapporté par l'utilisateur était « le CSS
est perdu ».

En mesurant, l'écart s'est révélé bien plus large que le cas signalé : le chemin
WSGI portait une classe maison qui IMITAIT `http.client.HTTPMessage`, le type
que le serveur de développement fournit. Dix comportements divergeaient, dont
trois qui cassent du code applicatif ordinaire :

    headers.get("X-Absent")     → ''  en production, None en développement
    "X-Absent" in headers       → TypeError en production, False en dév
    headers["X-Header"]         → TypeError en production, la valeur en dév

L'écart traversait l'API publique : `request.header("X-Absent", "repli")`
rendait `""` en production alors que les `@overload` de `Request.header`
promettent le défaut.

`CORE-WSGI-HEADERS-CONTRACT-001` avait déjà ajouté `keys()` et `items()` après
un `AttributeError`. C'était la première rustine, le ticket 66 en demandait une
deuxième : la cause est donc retirée, et les deux serveurs emploient le MÊME
type plutôt que deux qui se ressemblent.

Ces tests comparent les deux chemins côte à côte, sur les appels qu'un
contrôleur écrit réellement. Ils ne vérifient pas une implémentation : ils
vérifient que les deux donnent la même chose.
"""
from __future__ import annotations

from email.parser import Parser
from http.client import HTTPMessage
from io import BytesIO

import pytest

from core.app.wsgi import _headers_from_environ, _WsgiHandlerStub
from core.http.request import Request


class _HandlerDev:
    """Reproduit ce que `BaseHTTPRequestHandler` fournit à `Request`."""

    def __init__(self, texte: str) -> None:
        self.path = "/"
        self.command = "GET"
        self.headers = Parser(_class=HTTPMessage).parsestr(texte)
        self.client_address = ("127.0.0.1", 0)
        self.rfile = BytesIO(b"")


ENTETES = (
    ("HX-Request", "true"),
    ("Accept", "text/html"),
    ("Authorization", "Bearer secret"),
    ("X-Vide", ""),
)


@pytest.fixture
def requetes() -> tuple[Request, Request]:
    """La même requête, vue par le chemin WSGI et par le serveur de dév."""
    environ = {
        "REQUEST_METHOD": "GET", "PATH_INFO": "/", "QUERY_STRING": "",
        "REMOTE_ADDR": "127.0.0.1", "wsgi.input": BytesIO(b""),
        "CONTENT_TYPE": "application/json",
    }
    for nom, valeur in ENTETES:
        environ["HTTP_" + nom.upper().replace("-", "_")] = valeur

    texte = "".join(f"{n}: {v}\r\n" for n, v in ENTETES)
    texte += "Content-Type: application/json\r\n"

    return Request(_WsgiHandlerStub(environ)), Request(_HandlerDev(texte))


#: Ce qu'un contrôleur écrit réellement. Chaque entrée est jouée des deux côtés.
APPELS = [
    ("get d'un en-tête absent", lambda r: r.headers.get("X-Absent")),
    ("get absent avec défaut", lambda r: r.headers.get("X-Absent", "repli")),
    ("get présent", lambda r: r.headers.get("HX-Request")),
    ("get insensible à la casse", lambda r: r.headers.get("hx-request")),
    ("get d'un en-tête vide", lambda r: r.headers.get("X-Vide")),
    ("test d'absence par is None", lambda r: r.headers.get("X-Absent") is None),
    ("test de présence par in", lambda r: "HX-Request" in r.headers),
    ("test d'absence par in", lambda r: "X-Absent" in r.headers),
    ("in insensible à la casse", lambda r: "hx-request" in r.headers),
    ("accès par crochets", lambda r: r.headers["HX-Request"]),
    ("crochets sur un absent", lambda r: r.headers["X-Absent"]),
    ("nombre d'en-têtes", lambda r: len(r.headers)),
    ("get_all", lambda r: r.headers.get_all("HX-Request")),
    ("Request.header sans défaut", lambda r: r.header("X-Absent")),
    ("Request.header avec défaut", lambda r: r.header("X-Absent", "repli")),
    ("Request.header présent", lambda r: r.header("HX-Request")),
    ("vérité d'un en-tête vide", lambda r: bool(r.headers.get("X-Vide"))),
]


@pytest.mark.parametrize(("libelle", "appel"), APPELS, ids=[a[0] for a in APPELS])
def test_les_deux_serveurs_repondent_pareil(requetes, libelle, appel) -> None:
    """LE test du ticket : la comparaison, pas l'implémentation."""
    prod, dev = requetes

    def _jouer(requete):
        try:
            return ("valeur", appel(requete))
        except Exception as exc:  # noqa: BLE001 — une exception est un résultat
            return ("exception", type(exc).__name__)

    assert _jouer(prod) == _jouer(dev), (
        f"« {libelle} » ne donne pas la même chose sur les deux serveurs : "
        f"production {_jouer(prod)}, développement {_jouer(dev)}")


class TestLeCasDuTerrain:
    """Le motif exact qui a cassé onze contrôleurs, isolé."""

    def test_un_entete_absent_est_none_des_deux_cotes(self, requetes) -> None:
        prod, dev = requetes

        assert prod.headers.get("HX-Request-Absent") is None
        assert dev.headers.get("HX-Request-Absent") is None

    def test_le_defaut_de_request_header_est_rendu(self, requetes) -> None:
        """Les `@overload` promettent le défaut : la promesse doit tenir."""
        prod, _ = requetes

        assert prod.header("X-Absent", "repli") == "repli"

    def test_le_test_de_presence_ne_leve_pas(self, requetes) -> None:
        """`in` levait TypeError en production, faute de `__contains__`."""
        prod, _ = requetes

        assert ("X-Absent" in prod.headers) is False


class TestTypeUnique:
    """La cause retirée : un seul type, pas deux qui se ressemblent."""

    def test_le_chemin_wsgi_construit_un_httpmessage(self) -> None:
        entetes = _headers_from_environ({"HTTP_X_TEST": "1"})

        assert isinstance(entetes, HTTPMessage)

    def test_aucune_classe_maison_ne_subsiste(self) -> None:
        """Une imitation reviendrait avec ses propres trous."""
        import core.app.wsgi as module

        assert not hasattr(module, "_WsgiHeaders")

    def test_les_valeurs_ne_sont_jamais_parsees_comme_du_texte(self) -> None:
        """Un saut de ligne dans une valeur ne doit pas créer un en-tête."""
        entetes = _headers_from_environ({"HTTP_X_RUSE": "a\r\nX-Injecte: b"})

        assert entetes.get("X-Injecte") is None
        assert len(entetes) == 1


class TestLimiteDeLaCasse:
    """WSGI perd la casse d'origine des noms : c'est une limite, pas un défaut."""

    def test_le_nom_est_restitue_en_title_case(self) -> None:
        entetes = _headers_from_environ({"HTTP_HX_REQUEST": "true"})

        assert entetes.keys() == ["Hx-Request"]

    def test_mais_toute_lecture_reste_insensible_a_la_casse(self) -> None:
        """Ce qui compte pour du code applicatif, et qui est garanti."""
        entetes = _headers_from_environ({"HTTP_HX_REQUEST": "true"})

        for graphie in ("HX-Request", "hx-request", "Hx-Request", "HX-REQUEST"):
            assert entetes.get(graphie) == "true"
            assert graphie in entetes
