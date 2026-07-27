"""SKELETON-DEVSERVER-STREAM-001 : le serveur de dev honore les réponses en flux.

`Response.file()` (CORE-HTTP-FILE-RANGE-001) laisse `body` vide et pose
`stream` plus `content_length`. Le chemin WSGI le gère depuis l'origine ;
`_send_response` du serveur de développement annonçait `len(body)`, soit **0**,
et n'écrivait jamais le flux.

Conséquence mesurée avant correctif, sur un fichier de 5000 octets :
`Content-Length: 0` et **zéro octet écrit**. Tout téléchargement, toute lecture
vidéo ou audio et tout `/media/` étaient donc servis **vides** en
développement, sans la moindre erreur. Le contrat HTTP Range du cœur était
correct, mais inobservable par un développeur.

Les tests couvrent le contrat au niveau de `_send_response`, puis un aller
retour HTTP réel sur une socket, requête `Range` comprise.
"""
from __future__ import annotations

import importlib.util
import io
import sys
import threading
import urllib.error
import urllib.request
from collections.abc import Iterator
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from core.http.response import Response

SKELETON_APP = Path(__file__).resolve().parent.parent / "skeleton" / "data" / "app.py"
CONTENU = bytes(range(256)) * 40  # 10240 octets, non compressibles en une valeur


@pytest.fixture(scope="module")
def app_module() -> Any:
    """Importe le `app.py` du squelette, sans déclencher son `__main__`."""
    directory = str(SKELETON_APP.parent)
    if directory not in sys.path:
        sys.path.insert(0, directory)
    spec = importlib.util.spec_from_file_location("_devserver_stream_app", SKELETON_APP)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["_devserver_stream_app"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def fichier(tmp_path: Path) -> Path:
    path = tmp_path / "demo.bin"
    path.write_bytes(CONTENU)
    return path


class _CaptureHandler:
    """Capture ce que `_send_response` écrit réellement, sans socket."""

    def __init__(self, path: str = "/telechargement/demo.bin") -> None:
        self.path = path
        self.status: int | None = None
        self.sent_headers: dict[str, str] = {}
        self.wfile = io.BytesIO()

    def send_response(self, status: int) -> None:
        self.status = status

    def send_header(self, key: str, value: str) -> None:
        self.sent_headers[key] = value

    def end_headers(self) -> None:
        pass


def _send(app_module: Any, response: Response) -> _CaptureHandler:
    handler = _CaptureHandler()
    app_module.RequestHandler._send_response(handler, response)
    return handler


# ── Contrat de `_send_response` ──────────────────────────────────────────────

def test_une_reponse_en_flux_est_reellement_ecrite(app_module: Any, fichier: Path) -> None:
    handler = _send(app_module, Response.file(str(fichier), request=None))

    assert handler.status == 200
    assert handler.sent_headers["Content-Length"] == str(len(CONTENU))
    assert handler.wfile.getvalue() == CONTENU


def test_une_reponse_ordinaire_reste_inchangee(app_module: Any) -> None:
    """Le cas courant ne doit rien changer : pas de flux, `len(body)` fait foi."""
    handler = _send(app_module, Response(200, b"<h1>Bonjour</h1>", "text/html"))

    assert handler.sent_headers["Content-Length"] == str(len(b"<h1>Bonjour</h1>"))
    assert handler.wfile.getvalue() == b"<h1>Bonjour</h1>"


def test_une_deconnexion_du_client_ne_fait_pas_remonter_d_erreur(
    app_module: Any, fichier: Path,
) -> None:
    """Les en-têtes sont déjà partis : il n'y a plus de réponse d'erreur possible."""
    handler = _CaptureHandler()

    def _rompt(_chunk: bytes) -> int:
        raise BrokenPipeError("client parti")

    handler.wfile.write = _rompt  # type: ignore[method-assign]
    app_module.RequestHandler._send_response(handler, Response.file(str(fichier), request=None))

    assert handler.status == 200


# ── Aller retour HTTP réel, requête Range comprise ───────────────────────────

@pytest.fixture()
def serveur(app_module: Any, fichier: Path) -> Iterator[str]:
    """Un vrai serveur de développement, dont seul le dispatch est contrôlé."""

    class _Handler(app_module.RequestHandler):  # pyright: ignore[reportUntypedBaseClass]
        def _dispatch(self, request: Any) -> Response:
            return Response.file(str(fichier), request=request)

        def log_message(self, format: str, *args: Any) -> None:
            pass

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_address[1]}"
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)


def test_e2e_telechargement_complet(serveur: str) -> None:
    with urllib.request.urlopen(f"{serveur}/telechargement/demo.bin", timeout=10) as reponse:
        recu = reponse.read()
        assert reponse.status == 200
        assert reponse.headers["Content-Length"] == str(len(CONTENU))
        assert reponse.headers["Accept-Ranges"] == "bytes"
    assert recu == CONTENU


def test_e2e_requete_range_rend_la_bonne_tranche(serveur: str) -> None:
    """Le contrat Range du cœur devient enfin observable en développement."""
    requete = urllib.request.Request(
        f"{serveur}/telechargement/demo.bin", headers={"Range": "bytes=100-199"}
    )
    with urllib.request.urlopen(requete, timeout=10) as reponse:
        recu = reponse.read()
        assert reponse.status == 206
        assert reponse.headers["Content-Range"] == f"bytes 100-199/{len(CONTENU)}"
        assert reponse.headers["Content-Length"] == "100"
    assert recu == CONTENU[100:200]


def test_e2e_range_hors_limites_rend_416(serveur: str) -> None:
    requete = urllib.request.Request(
        f"{serveur}/telechargement/demo.bin",
        headers={"Range": f"bytes={len(CONTENU) + 500}-"},
    )
    with pytest.raises(urllib.error.HTTPError) as erreur:
        urllib.request.urlopen(requete, timeout=10)

    assert erreur.value.code == 416
    assert erreur.value.headers["Content-Range"] == f"bytes */{len(CONTENU)}"
