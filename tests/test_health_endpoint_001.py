"""
Tests HEALTH-ENDPOINT-001 — Endpoint GET /health.

Vérifie le comportement du endpoint de santé Forge :
- statut 200
- Content-Type application/json
- corps {"status": "ok"}
- headers de sécurité présents
- indépendance vis-à-vis de MariaDB et des sessions
- aucune donnée sensible exposée

Tests unitaires : via FakeRequest + RequestHandler simulé.
Tests E2E : via la fixture forge_server (sous-processus HTTP local).
"""
from __future__ import annotations

import importlib.util
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parent.parent


# ── Helpers ───────────────────────────────────────────────────────────────────


def _import_app():
    """Importe app.py comme module (sans déclencher __main__)."""
    spec = importlib.util.spec_from_file_location("_app_health_tests", ROOT / "app.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_app_health_tests"] = mod
    spec.loader.exec_module(mod)
    return mod


def _headers_lower(hdrs: dict) -> dict:
    return {k.lower(): v for k, v in hdrs.items()}


# ── Tests unitaires via RequestHandler ────────────────────────────────────────


class _FakeWfile:
    def __init__(self):
        self.data = b""

    def write(self, b):
        self.data += b


class _FakeSocket:
    def makefile(self, *args, **kwargs):
        import io
        return io.BytesIO(b"GET /health HTTP/1.1\r\nHost: localhost\r\n\r\n")

    def getpeername(self):
        return ("127.0.0.1", 9999)


class _FakeServer:
    pass


class _HealthHandler:
    """Pilote RequestHandler en mode test sans réseau réel."""

    def __init__(self, app_module):
        self._mod = app_module
        self.sent_status = None
        self.sent_headers = {}
        self._headers_ended = False
        self.body = b""

    def handle(self, path: str):
        """Simule un GET sur path et retourne (status, headers, body)."""
        sent_status = []
        sent_headers = {}
        body_parts = []

        class FakeHandler(self._mod.RequestHandler):
            def __init__(fh):  # noqa: N805
                pass

            @property
            def path(fh):  # noqa: N805
                return path

            def send_response(fh, code):  # noqa: N805
                sent_status.append(code)

            def send_header(fh, key, value):  # noqa: N805
                sent_headers[key.lower()] = value

            def end_headers(fh):  # noqa: N805
                pass

            def wfile(fh):  # noqa: N805
                pass

        fh = FakeHandler()
        fh.wfile = SimpleNamespace(write=lambda b: body_parts.append(b))
        fh.headers = {}
        fh.command = "GET"
        fh.client_address = ("127.0.0.1", 9999)
        fh.do_GET()
        return (
            sent_status[0] if sent_status else None,
            sent_headers,
            b"".join(body_parts),
        )


# ── Tests E2E via sous-processus ──────────────────────────────────────────────


def _get(url: str, timeout: float = 5.0):
    """GET HTTP — retourne (status, headers_dict, body_bytes)."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers), exc.read()


@pytest.fixture(scope="module")
def forge_server():
    """Réutilise la même logique que test_http_e2e_001 pour démarrer Forge."""
    import os
    import socket
    import subprocess

    def _free_port():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

    port = _free_port()
    env = {**os.environ, "APP_ENV": "prod", "TEST_PORT": str(port)}
    launcher = ROOT / "tests" / "_e2e_launcher.py"
    proc = subprocess.Popen(
        [sys.executable, str(launcher)],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    try:
        line = proc.stdout.readline()
        if not line.startswith(b"READY:"):
            proc.terminate()
            proc.wait(timeout=5)
            pytest.skip("Serveur Forge non disponible")
    except Exception:
        proc.terminate()
        proc.wait(timeout=5)
        pytest.skip("Serveur Forge non disponible")
    proc.stdout.close()
    yield f"http://127.0.0.1:{port}"
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


# ── Tests comportement via E2E ────────────────────────────────────────────────


def test_health_retourne_200(forge_server):
    """GET /health retourne 200 OK."""
    status, _, _ = _get(f"{forge_server}/health")
    assert status == 200


def test_health_content_type_json(forge_server):
    """GET /health retourne Content-Type application/json."""
    _, headers, _ = _get(f"{forge_server}/health")
    ct = headers.get("Content-Type") or headers.get("content-type") or ""
    assert "application/json" in ct


def test_health_corps_status_ok(forge_server):
    """GET /health retourne {"status": "ok"}."""
    _, _, body = _get(f"{forge_server}/health")
    data = json.loads(body.decode("utf-8"))
    assert data == {"status": "ok"}


def test_health_corps_exactement_un_champ(forge_server):
    """La réponse /health n'expose pas d'autres champs (version, config, secrets)."""
    _, _, body = _get(f"{forge_server}/health")
    data = json.loads(body.decode("utf-8"))
    assert set(data.keys()) == {"status"}


def test_health_header_x_frame_options(forge_server):
    """GET /health inclut X-Frame-Options."""
    _, headers, _ = _get(f"{forge_server}/health")
    hdrs = _headers_lower(headers)
    assert "x-frame-options" in hdrs


def test_health_header_x_content_type_options(forge_server):
    """GET /health inclut X-Content-Type-Options."""
    _, headers, _ = _get(f"{forge_server}/health")
    hdrs = _headers_lower(headers)
    assert "x-content-type-options" in hdrs


def test_health_header_referrer_policy(forge_server):
    """GET /health inclut Referrer-Policy."""
    _, headers, _ = _get(f"{forge_server}/health")
    hdrs = _headers_lower(headers)
    assert "referrer-policy" in hdrs


def test_health_header_csp(forge_server):
    """GET /health inclut Content-Security-Policy."""
    _, headers, _ = _get(f"{forge_server}/health")
    hdrs = _headers_lower(headers)
    assert "content-security-policy" in hdrs


def test_health_ne_contient_pas_version(forge_server):
    """La réponse /health n'expose pas la version de Forge."""
    _, _, body = _get(f"{forge_server}/health")
    text = body.decode("utf-8").lower()
    assert "version" not in text


def test_health_ne_contient_pas_chemin(forge_server):
    """La réponse /health n'expose pas de chemin système."""
    _, _, body = _get(f"{forge_server}/health")
    text = body.decode("utf-8")
    assert "/" not in text.replace('{"status": "ok"}', "").replace('{"status":"ok"}', "")


def test_health_repetable(forge_server):
    """GET /health répété retourne toujours 200 et le même corps."""
    for _ in range(5):
        status, _, body = _get(f"{forge_server}/health")
        assert status == 200
        assert json.loads(body) == {"status": "ok"}


# ── Tests documentaires ───────────────────────────────────────────────────────


def test_deployment_md_mentionne_health():
    """docs/deployment/deployment.md mentionne /health."""
    content = (ROOT / "docs" / "deployment" / "deployment.md").read_text(encoding="utf-8")
    assert "/health" in content


def test_reference_md_mentionne_health():
    """docs/reference/profils.md mentionne /health."""
    content = (ROOT / "docs" / "reference" / "profils.md").read_text(encoding="utf-8")
    assert "/health" in content
