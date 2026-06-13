"""Tests — SECURITY-UPLOAD-RATE-LIMIT-001 : rate limiting des routes d'upload.

Vérifie que :
- is_upload_rate_limited() retourne False sous la limite, True au-delà ;
- record_upload_attempt() incrémente le compteur ;
- la fenêtre glissante expire les anciens timestamps ;
- dans Application.dispatch(), les uploads au-delà de la limite retournent 429 ;
- les uploads sous la limite passent normalement ;
- une IP différente n'est pas bloquée par les uploads d'une autre IP ;
- aucun fichier n'est créé quand la requête est refusée pour rate limit ;
- les validations existantes (extension, taille) fonctionnent toujours.
"""
from __future__ import annotations

import io
import json
from types import SimpleNamespace

import pytest

import core.forge as forge
pytest.importorskip("forge_mvc_files")
# FILES-MOVE-PIPELINE-001 (ADR-019) : le rate-limit d'upload vit dans l'opt-in.
# On importe le VRAI module (et non le shim core) pour que les monkeypatch des
# constantes soient pris en compte par les fonctions.
import forge_mvc_files.rate_limit as _rl
from core.app.application import Application
from core.http.request import Request
from core.http.response import Response
from core.http.router import Router
from tests._malicious_samples import fake_php_shell
from core.forms.upload_exceptions import UploadError
from forge_mvc_files.manager import save_upload

# ---------------------------------------------------------------------------
# Helpers (partagés avec test_e2e_upload_http.py)
# ---------------------------------------------------------------------------

_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
    b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
    b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


class _FakeHeaders:
    def __init__(self, data: dict):
        self._data = {k.lower(): v for k, v in data.items()}

    def get(self, name, default=""):
        return self._data.get(name.lower(), default)


def _http_handler(method="POST", path="/upload", headers=None, body=b"",
                  ip="10.0.0.1"):
    h = headers or {}
    return SimpleNamespace(
        command=method,
        path=path,
        headers=_FakeHeaders(h),
        rfile=io.BytesIO(body),
        client_address=(ip, 12345),
    )


def _multipart_body(boundary: str, filename: str, content: bytes,
                    content_type: str = "image/png") -> bytes:
    head = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="avatar"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode("utf-8")
    tail = f"\r\n--{boundary}--\r\n".encode("utf-8")
    return head + content + tail


def _make_request(ip="10.0.0.1", body=None, filename="photo.png"):
    if body is None:
        body = _PNG_BYTES
    boundary = "----RLBoundary"
    raw_body = _multipart_body(boundary, filename, body)
    return Request(_http_handler(
        body=raw_body,
        headers={
            "Content-Length": str(len(raw_body)),
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        ip=ip,
    ))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _isolate_upload_env(monkeypatch):
    """ADR-032 : vide les variables d'upload extraites du core avant chaque test."""
    for key in (
        "UPLOAD_ALLOWED_EXTENSIONS",
        "UPLOAD_ALLOWED_MIME_TYPES",
        "UPLOAD_MAX_IMAGE_PIXELS",
    ):
        monkeypatch.delenv(key, raising=False)


@pytest.fixture()
def low_limit(monkeypatch):
    """Réduit la limite à 3 uploads par fenêtre pour les tests."""
    monkeypatch.setattr(_rl, "UPLOAD_MAX_PAR_FENETRE", 3)


@pytest.fixture()
def rate_limited_app(tmp_path, low_limit, monkeypatch):
    """Application.dispatch() avec handler upload protégé par rate limiting."""
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()

    # ADR-032 : upload_root, extensions et types MIME lus depuis l'environnement
    # par l'opt-in files ; seul upload_max_size reste détenu par le noyau.
    monkeypatch.setenv("UPLOAD_ROOT", str(upload_dir))
    monkeypatch.setenv("UPLOAD_ALLOWED_EXTENSIONS", "png,jpg,pdf")
    monkeypatch.setenv("UPLOAD_ALLOWED_MIME_TYPES", "image/png,image/jpeg,application/pdf")
    forge.configure(upload_max_size=512)

    def _handler(request):
        if _rl.is_upload_rate_limited(request.ip):
            body = json.dumps({
                "success": False,
                "error": {"code": "rate_limited", "message": "Trop d'uploads en peu de temps."},
            }).encode()
            return Response(429, body, "application/json")
        _rl.record_upload_attempt(request.ip)
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
    router.add("POST", "/upload", _handler, public=True, csrf=False)
    app = Application(router, middlewares=[], api_routes_module=None)
    return app, upload_dir


# ---------------------------------------------------------------------------
# Tests unitaires du module rate_limit
# ---------------------------------------------------------------------------

class TestRateLimitUnit:
    def test_ip_inconnue_non_limitee(self):
        assert _rl.is_upload_rate_limited("1.2.3.4") is False

    def test_sous_la_limite_non_bloquee(self, monkeypatch):
        monkeypatch.setattr(_rl, "UPLOAD_MAX_PAR_FENETRE", 3)
        for _ in range(2):
            _rl.record_upload_attempt("1.2.3.4")
        assert _rl.is_upload_rate_limited("1.2.3.4") is False

    def test_exactement_a_la_limite_bloquee(self, monkeypatch):
        monkeypatch.setattr(_rl, "UPLOAD_MAX_PAR_FENETRE", 3)
        for _ in range(3):
            _rl.record_upload_attempt("1.2.3.4")
        assert _rl.is_upload_rate_limited("1.2.3.4") is True

    def test_au_dela_limite_bloquee(self, monkeypatch):
        monkeypatch.setattr(_rl, "UPLOAD_MAX_PAR_FENETRE", 3)
        for _ in range(5):
            _rl.record_upload_attempt("1.2.3.4")
        assert _rl.is_upload_rate_limited("1.2.3.4") is True

    def test_ip_differentes_independantes(self, monkeypatch):
        monkeypatch.setattr(_rl, "UPLOAD_MAX_PAR_FENETRE", 3)
        for _ in range(3):
            _rl.record_upload_attempt("1.1.1.1")
        assert _rl.is_upload_rate_limited("2.2.2.2") is False

    def test_timestamps_anciens_expirés(self, monkeypatch):
        import time
        monkeypatch.setattr(_rl, "UPLOAD_MAX_PAR_FENETRE", 3)
        monkeypatch.setattr(_rl, "UPLOAD_RATE_LIMIT_WINDOW", 60)
        # Insérer manuellement des timestamps périmés
        _rl._compteurs["9.9.9.9"] = [time.time() - 120, time.time() - 90]
        assert _rl.is_upload_rate_limited("9.9.9.9") is False

    def test_compteur_nettoye_si_vide(self, monkeypatch):
        import time
        monkeypatch.setattr(_rl, "UPLOAD_RATE_LIMIT_WINDOW", 60)
        _rl._compteurs["9.9.9.9"] = [time.time() - 120]
        _rl.is_upload_rate_limited("9.9.9.9")
        assert "9.9.9.9" not in _rl._compteurs

    def test_enregistrer_incremente_compteur(self, monkeypatch):
        monkeypatch.setattr(_rl, "UPLOAD_MAX_PAR_FENETRE", 10)
        for i in range(5):
            _rl.record_upload_attempt("5.5.5.5")
        assert len(_rl._compteurs["5.5.5.5"]) == 5


# ---------------------------------------------------------------------------
# Tests dispatch avec rate limit
# ---------------------------------------------------------------------------

class TestDispatchAvecRateLimit:
    def test_uploads_sous_limite_acceptes(self, rate_limited_app):
        app, upload_dir = rate_limited_app
        for _ in range(3):  # UPLOAD_MAX_PAR_FENETRE = 3 → 3 uploads OK
            req = _make_request(ip="10.0.0.1")
            resp = app.dispatch(req)
            assert resp.status == 201

    def test_upload_au_dela_limite_retourne_429(self, rate_limited_app):
        app, upload_dir = rate_limited_app
        for _ in range(3):
            req = _make_request(ip="10.0.0.2")
            app.dispatch(req)
        req = _make_request(ip="10.0.0.2")
        resp = app.dispatch(req)
        assert resp.status == 429

    def test_reponse_429_est_json(self, rate_limited_app):
        app, _ = rate_limited_app
        for _ in range(3):
            app.dispatch(_make_request(ip="10.0.0.3"))
        resp = app.dispatch(_make_request(ip="10.0.0.3"))
        assert resp.content_type == "application/json"
        data = json.loads(resp.body)
        assert data["success"] is False
        assert data["error"]["code"] == "rate_limited"

    def test_ip_differente_non_bloquee(self, rate_limited_app):
        app, _ = rate_limited_app
        for _ in range(3):
            app.dispatch(_make_request(ip="10.0.0.4"))
        resp = app.dispatch(_make_request(ip="10.0.0.5"))
        assert resp.status == 201


# ---------------------------------------------------------------------------
# Aucun fichier créé quand refusé pour rate limit
# ---------------------------------------------------------------------------

class TestRateLimitAucunFichierCree:
    def test_aucun_fichier_apres_429(self, rate_limited_app):
        app, upload_dir = rate_limited_app
        for _ in range(3):
            app.dispatch(_make_request(ip="10.0.0.6"))
        fichiers_avant = list(upload_dir.rglob("*"))
        app.dispatch(_make_request(ip="10.0.0.6"))
        fichiers_apres = list(upload_dir.rglob("*"))
        assert len(fichiers_avant) == len(fichiers_apres)

    def test_trois_fichiers_crees_pour_trois_uploads_valides(self, rate_limited_app):
        app, upload_dir = rate_limited_app
        for _ in range(3):
            app.dispatch(_make_request(ip="10.0.0.7"))
        fichiers = [f for f in upload_dir.rglob("*") if f.is_file()]
        assert len(fichiers) == 3


# ---------------------------------------------------------------------------
# Pas de régression sur les validations existantes
# ---------------------------------------------------------------------------

class TestRateLimitEtValidationsExistantes:
    def test_extension_interdite_retourne_422(self, rate_limited_app):
        app, upload_dir = rate_limited_app
        boundary = "----RLExt"
        body = _multipart_body(boundary, "malware.php", fake_php_shell("echo 1;"),
                               "application/x-php")
        raw_body = body
        req = Request(_http_handler(
            body=raw_body,
            headers={
                "Content-Length": str(len(raw_body)),
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            ip="10.0.0.8",
        ))
        resp = app.dispatch(req)
        assert resp.status == 422

    def test_fichier_trop_gros_retourne_422(self, rate_limited_app):
        app, _ = rate_limited_app
        big = b"X" * 600  # > 512 octets
        boundary = "----RLSize"
        raw_body = _multipart_body(boundary, "big.png", big)
        req = Request(_http_handler(
            body=raw_body,
            headers={
                "Content-Length": str(len(raw_body)),
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            ip="10.0.0.9",
        ))
        resp = app.dispatch(req)
        assert resp.status == 422

    def test_constantes_defaut_coherentes(self):
        assert _rl.UPLOAD_MAX_PAR_FENETRE == 10
        assert _rl.UPLOAD_RATE_LIMIT_WINDOW == 60
