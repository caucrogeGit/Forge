"""Tests — E2E-UPLOAD-HTTP-001 : cycle upload HTTP multipart quasi-E2E.

Approche retenue : Option A — quasi-E2E via Application.dispatch().
Les tests passent par la pile Application.dispatch() → contrôleur → save_upload()
→ stockage disque → vérification fichier. Aucun serveur TCP n'est lancé.

LIMITE DOCUMENTÉE : les headers de sécurité globaux (X-Frame-Options, HSTS, CSP,
Permissions-Policy, Cache-Control) sont ajoutés par `app.py._send_response()`,
couche HTTP absente ici. Ils ne figurent pas dans la réponse de dispatch().
Les tests de ces headers restent dans test_security_headers.py (E2E TCP réel).

Ce qui est couvert :
- parsing HTTP multipart (Request._parse_multipart / Request complet) ;
- fichier reçu dans request.files ;
- Application.dispatch() → contrôleur → save_upload() → stockage disque ;
- chemin relatif sous storage/uploads/ ;
- extension autorisée acceptée ;
- extension interdite (.php, .exe) refusée, aucun fichier créé ;
- fichier trop gros refusé, aucun fichier créé ;
- champ fichier absent géré proprement ;
- path traversal neutralisé, aucun fichier hors uploads/ créé ;
- nettoyage par tmp_path (automatique).

Hors périmètre :
- magic bytes / MIME sniffing binaire ;
- rate limiting upload (ticket SECURITY-UPLOAD-RATE-LIMIT-001) ;
- galerie média ;
- authentification upload avancée.
"""
from __future__ import annotations

import io
import json
from types import SimpleNamespace

import pytest

import core.forge as forge
from core.application import Application
from core.http.request import Request, UploadedFile
from core.http.response import Response
from core.http.router import Router
from core.uploads.exceptions import UploadError
from core.uploads.manager import save_upload
from tests.fake_request import FakeRequest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
    b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
    b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


class _FakeHeaders:
    """Simule http.client.HTTPMessage pour les tests de parsing Request."""

    def __init__(self, data: dict):
        self._data = {k.lower(): v for k, v in data.items()}

    def get(self, name, default=""):
        return self._data.get(name.lower(), default)


def _http_handler(method="POST", path="/test/upload", headers=None, body=b""):
    h = headers or {}
    return SimpleNamespace(
        command=method,
        path=path,
        headers=_FakeHeaders(h),
        rfile=io.BytesIO(body),
        client_address=("127.0.0.1", 12345),
    )


def _multipart_body(boundary: str, filename: str, content: bytes,
                    content_type: str = "image/png") -> bytes:
    """Construit un body multipart valide avec un champ fichier."""
    head = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="avatar"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode("utf-8")
    tail = f"\r\n--{boundary}--\r\n".encode("utf-8")
    return head + content + tail


# ---------------------------------------------------------------------------
# Fixture : Application minimale avec route d'upload de test
# ---------------------------------------------------------------------------

@pytest.fixture()
def upload_app(tmp_path):
    """
    Application.dispatch() avec une route POST /test/upload (public, sans CSRF).
    Stockage dans tmp_path/uploads. Retourne (app, upload_dir).
    """
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()

    forge.configure(
        upload_root=str(upload_dir),
        upload_max_size=512,          # 512 octets pour garder les tests rapides
        upload_allowed_extensions=["png", "jpg", "pdf"],
        upload_allowed_mime_types=["image/png", "image/jpeg", "application/pdf"],
    )

    def _upload_handler(request):
        file = request.files.get("avatar")
        if file is None:
            return Response(422, b'{"error": "champ avatar absent"}', "application/json")
        try:
            saved = save_upload(file, category="images")
            body = json.dumps({"path": saved.path, "size": saved.size}).encode()
            return Response(201, body, "application/json")
        except UploadError as exc:
            body = json.dumps({"error": str(exc)}).encode()
            return Response(422, body, "application/json")

    router = Router()
    router.add("POST", "/test/upload", _upload_handler, public=True, csrf=False)
    app = Application(router, middlewares=[], api_routes_module=None)

    return app, upload_dir


# ---------------------------------------------------------------------------
# Parsing HTTP multipart réel (Request._parse_multipart / Request complet)
# ---------------------------------------------------------------------------

class TestMultipartParsingHTTP:
    """Vérifie que la couche HTTP Forge parse correctement un body multipart."""

    def test_parse_multipart_cree_uploaded_file(self):
        boundary = "----TestBoundary001"
        body = _multipart_body(boundary, "photo.png", _PNG_BYTES)
        content_type = f"multipart/form-data; boundary={boundary}"
        parsed_body, files = Request._parse_multipart(content_type, body)
        assert "avatar" in files

    def test_parse_multipart_filename_correct(self):
        boundary = "----TestBoundary002"
        body = _multipart_body(boundary, "photo.png", _PNG_BYTES)
        content_type = f"multipart/form-data; boundary={boundary}"
        _, files = Request._parse_multipart(content_type, body)
        assert files["avatar"].filename == "photo.png"

    def test_parse_multipart_content_preserve(self):
        boundary = "----TestBoundary003"
        body = _multipart_body(boundary, "photo.png", _PNG_BYTES)
        content_type = f"multipart/form-data; boundary={boundary}"
        _, files = Request._parse_multipart(content_type, body)
        assert files["avatar"].read() == _PNG_BYTES

    def test_parse_multipart_content_type_preserve(self):
        boundary = "----TestBoundary004"
        body = _multipart_body(boundary, "photo.png", _PNG_BYTES, "image/png")
        content_type = f"multipart/form-data; boundary={boundary}"
        _, files = Request._parse_multipart(content_type, body)
        assert files["avatar"].content_type == "image/png"

    def test_parse_multipart_size_correct(self):
        boundary = "----TestBoundary005"
        body = _multipart_body(boundary, "photo.png", _PNG_BYTES)
        content_type = f"multipart/form-data; boundary={boundary}"
        _, files = Request._parse_multipart(content_type, body)
        assert files["avatar"].size == len(_PNG_BYTES)

    def test_request_complet_parse_fichier(self):
        boundary = "----TestBoundary006"
        body = _multipart_body(boundary, "avatar.png", _PNG_BYTES)
        req = Request(_http_handler(
            body=body,
            headers={
                "Content-Length": str(len(body)),
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
        ))
        assert "avatar" in req.files
        assert req.files["avatar"].filename == "avatar.png"
        assert req.files["avatar"].read() == _PNG_BYTES

    def test_request_complet_corps_texte_et_fichier(self):
        boundary = "----TestBoundary007"
        text_part = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="titre"\r\n\r\n'
            "Mon titre\r\n"
        ).encode("utf-8")
        file_part = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="avatar"; filename="doc.png"\r\n'
            "Content-Type: image/png\r\n\r\n"
        ).encode("utf-8") + _PNG_BYTES + f"\r\n--{boundary}--\r\n".encode("utf-8")
        body = text_part + file_part
        req = Request(_http_handler(
            body=body,
            headers={
                "Content-Length": str(len(body)),
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
        ))
        assert req.body == {"titre": ["Mon titre"]}
        assert req.files["avatar"].filename == "doc.png"

    def test_fake_request_files_transmis(self):
        file = UploadedFile(
            field_name="avatar",
            filename="photo.png",
            content=_PNG_BYTES,
            content_type="image/png",
        )
        req = FakeRequest("POST", "/test/upload", files={"avatar": file})
        assert req.files["avatar"].filename == "photo.png"
        assert req.files["avatar"].read() == _PNG_BYTES


# ---------------------------------------------------------------------------
# Upload valide — Application.dispatch() → contrôleur → stockage
# ---------------------------------------------------------------------------

class TestDispatchUploadValide:
    """Cycle complet upload valide via Application.dispatch()."""

    def _file(self, filename="avatar.png", content=_PNG_BYTES, ct="image/png"):
        return UploadedFile(
            field_name="avatar",
            filename=filename,
            content=content,
            content_type=ct,
        )

    def test_dispatch_retourne_201(self, upload_app):
        app, _ = upload_app
        req = FakeRequest("POST", "/test/upload", files={"avatar": self._file()})
        resp = app.dispatch(req)
        assert resp.status == 201

    def test_dispatch_reponse_json_valide(self, upload_app):
        app, _ = upload_app
        req = FakeRequest("POST", "/test/upload", files={"avatar": self._file()})
        resp = app.dispatch(req)
        data = json.loads(resp.body.decode())
        assert "path" in data

    def test_dispatch_fichier_stocke_sur_disque(self, upload_app):
        app, upload_dir = upload_app
        req = FakeRequest("POST", "/test/upload", files={"avatar": self._file()})
        resp = app.dispatch(req)
        data = json.loads(resp.body.decode())
        stored = upload_dir / data["path"]
        assert stored.exists(), f"Fichier attendu sous {stored}"

    def test_dispatch_contenu_stocke_correct(self, upload_app):
        app, upload_dir = upload_app
        req = FakeRequest("POST", "/test/upload", files={"avatar": self._file()})
        resp = app.dispatch(req)
        data = json.loads(resp.body.decode())
        stored = upload_dir / data["path"]
        assert stored.read_bytes() == _PNG_BYTES

    def test_dispatch_chemin_relatif(self, upload_app):
        app, _ = upload_app
        req = FakeRequest("POST", "/test/upload", files={"avatar": self._file()})
        resp = app.dispatch(req)
        data = json.loads(resp.body.decode())
        assert not data["path"].startswith("/")

    def test_dispatch_chemin_sous_images(self, upload_app):
        app, _ = upload_app
        req = FakeRequest("POST", "/test/upload", files={"avatar": self._file()})
        resp = app.dispatch(req)
        data = json.loads(resp.body.decode())
        assert data["path"].startswith("images/")

    def test_dispatch_chemin_sans_points_points(self, upload_app):
        app, _ = upload_app
        req = FakeRequest("POST", "/test/upload", files={"avatar": self._file()})
        resp = app.dispatch(req)
        data = json.loads(resp.body.decode())
        assert ".." not in data["path"]

    def test_dispatch_taille_retournee_correcte(self, upload_app):
        app, _ = upload_app
        req = FakeRequest("POST", "/test/upload", files={"avatar": self._file()})
        resp = app.dispatch(req)
        data = json.loads(resp.body.decode())
        assert data["size"] == len(_PNG_BYTES)


# ---------------------------------------------------------------------------
# Extension interdite — refus, aucun fichier créé
# ---------------------------------------------------------------------------

class TestDispatchExtensionInterdite:
    """L'extension non whitelistée est refusée — aucun fichier créé."""

    def _php_file(self):
        return UploadedFile(
            field_name="avatar",
            filename="shell.php",
            content=b"<?php system($_GET['cmd']); ?>",
            content_type="application/x-php",
        )

    def _exe_file(self):
        return UploadedFile(
            field_name="avatar",
            filename="malware.exe",
            content=b"MZ\x90\x00",
            content_type="application/octet-stream",
        )

    def test_extension_php_retourne_422(self, upload_app):
        app, _ = upload_app
        req = FakeRequest("POST", "/test/upload", files={"avatar": self._php_file()})
        resp = app.dispatch(req)
        assert resp.status == 422

    def test_extension_php_aucun_fichier_cree(self, upload_app):
        app, upload_dir = upload_app
        avant = list(upload_dir.rglob("*"))
        req = FakeRequest("POST", "/test/upload", files={"avatar": self._php_file()})
        app.dispatch(req)
        apres = list(upload_dir.rglob("*"))
        assert apres == avant, "Un fichier a été créé malgré l'extension interdite"

    def test_extension_exe_retourne_422(self, upload_app):
        app, _ = upload_app
        req = FakeRequest("POST", "/test/upload", files={"avatar": self._exe_file()})
        resp = app.dispatch(req)
        assert resp.status == 422

    def test_extension_exe_aucun_fichier_cree(self, upload_app):
        app, upload_dir = upload_app
        avant = list(upload_dir.rglob("*"))
        req = FakeRequest("POST", "/test/upload", files={"avatar": self._exe_file()})
        app.dispatch(req)
        apres = list(upload_dir.rglob("*"))
        assert apres == avant, "Un fichier a été créé malgré l'extension .exe"

    def test_reponse_json_contient_erreur(self, upload_app):
        app, _ = upload_app
        req = FakeRequest("POST", "/test/upload", files={"avatar": self._php_file()})
        resp = app.dispatch(req)
        data = json.loads(resp.body.decode())
        assert "error" in data


# ---------------------------------------------------------------------------
# Fichier trop gros — refus, aucun fichier créé
# ---------------------------------------------------------------------------

class TestDispatchFichierTropGros:
    """Le fichier dépassant upload_max_size est refusé — aucun fichier créé."""

    def _big_file(self):
        return UploadedFile(
            field_name="avatar",
            filename="big.png",
            content=b"\x89PNG" + b"x" * 600,  # > 512 octets (limite fixture)
            content_type="image/png",
        )

    def test_fichier_trop_gros_retourne_422(self, upload_app):
        app, _ = upload_app
        req = FakeRequest("POST", "/test/upload", files={"avatar": self._big_file()})
        resp = app.dispatch(req)
        assert resp.status == 422

    def test_fichier_trop_gros_aucun_fichier_cree(self, upload_app):
        app, upload_dir = upload_app
        avant = list(upload_dir.rglob("*"))
        req = FakeRequest("POST", "/test/upload", files={"avatar": self._big_file()})
        app.dispatch(req)
        apres = list(upload_dir.rglob("*"))
        assert apres == avant, "Un fichier a été créé malgré le dépassement de taille"


# ---------------------------------------------------------------------------
# Champ fichier absent — géré proprement
# ---------------------------------------------------------------------------

class TestDispatchFichierAbsent:
    """Le champ fichier manquant est géré sans exception non contrôlée."""

    def test_champ_absent_retourne_422(self, upload_app):
        app, _ = upload_app
        req = FakeRequest("POST", "/test/upload")
        resp = app.dispatch(req)
        assert resp.status == 422

    def test_champ_absent_aucun_fichier_cree(self, upload_app):
        app, upload_dir = upload_app
        avant = list(upload_dir.rglob("*"))
        req = FakeRequest("POST", "/test/upload")
        app.dispatch(req)
        apres = list(upload_dir.rglob("*"))
        assert apres == avant

    def test_mauvais_champ_retourne_422(self, upload_app):
        app, _ = upload_app
        file = UploadedFile(
            field_name="autre_champ",
            filename="photo.png",
            content=_PNG_BYTES,
            content_type="image/png",
        )
        req = FakeRequest("POST", "/test/upload", files={"autre_champ": file})
        resp = app.dispatch(req)
        assert resp.status == 422


# ---------------------------------------------------------------------------
# Path traversal — neutralisation, aucun fichier hors uploads/
# ---------------------------------------------------------------------------

class TestDispatchPathTraversal:
    """
    Les noms de fichier avec traversal (../) sont neutralisés par secure_filename()
    via os.path.basename(). Le fichier est stocké dans uploads/ (sécurisé).
    Aucun fichier ne sort de l'arborescence uploads/.
    """

    def _traversal_file(self, filename="../../evil.png"):
        return UploadedFile(
            field_name="avatar",
            filename=filename,
            content=_PNG_BYTES,
            content_type="image/png",
        )

    def test_traversal_dispatch_retourne_201(self, upload_app):
        app, _ = upload_app
        req = FakeRequest("POST", "/test/upload", files={"avatar": self._traversal_file()})
        resp = app.dispatch(req)
        assert resp.status == 201

    def test_traversal_fichier_stocke_sous_uploads(self, upload_app):
        app, upload_dir = upload_app
        req = FakeRequest("POST", "/test/upload", files={"avatar": self._traversal_file()})
        resp = app.dispatch(req)
        data = json.loads(resp.body.decode())
        stored = (upload_dir / data["path"]).resolve()
        assert str(stored).startswith(str(upload_dir.resolve()))

    def test_traversal_chemin_sans_points_points(self, upload_app):
        app, _ = upload_app
        req = FakeRequest("POST", "/test/upload", files={"avatar": self._traversal_file()})
        resp = app.dispatch(req)
        data = json.loads(resp.body.decode())
        assert ".." not in data["path"]

    def test_traversal_aucun_fichier_hors_uploads(self, upload_app):
        app, upload_dir = upload_app
        parent = upload_dir.parent
        avant = set(p for p in parent.rglob("*") if p != upload_dir and not str(p).startswith(str(upload_dir)))
        req = FakeRequest("POST", "/test/upload", files={"avatar": self._traversal_file()})
        app.dispatch(req)
        apres = set(p for p in parent.rglob("*") if p != upload_dir and not str(p).startswith(str(upload_dir)))
        assert apres == avant, "Un fichier a été créé hors du dossier uploads/"

