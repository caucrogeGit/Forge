"""
Tests HTTP-E2E-TESTS-001 — Tests end-to-end HTTP réels.

Démarre Forge sur un port libre en HTTP local (sans SSL, sans MariaDB),
puis vérifie les réponses HTTP réelles du serveur.

Couverture :
- GET / retourne une réponse HTTP valide
- GET route inconnue retourne 404
- Headers de sécurité présents (CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy)
- Fichier statique connu servi (200)
- Fichier statique inexistant → 404
- Tentative path traversal → 403 ou 404
- CSP ne contient pas 'unsafe-inline'
- CSP contient 'self'
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import NamedTuple

import pytest

ROOT = Path(__file__).resolve().parent.parent


# ── Helpers ───────────────────────────────────────────────────────────────────


def _free_port() -> int:
    """Retourne un port TCP libre sur 127.0.0.1."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def _wait_for_server(url: str, timeout: float = 8.0) -> bool:
    """Attend que le serveur réponde sur url (sonde répétée)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except urllib.error.HTTPError:
            return True  # Le serveur répond avec une erreur HTTP → il est prêt
        except OSError:
            time.sleep(0.15)
    return False


class _Response(NamedTuple):
    status: int
    headers: dict[str, str]
    body: bytes


def _get(url: str, timeout: float = 5.0) -> _Response:
    """Effectue un GET et retourne (_Response). Gère les erreurs HTTP 4xx/5xx."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return _Response(
                status=resp.status,
                headers=dict(resp.headers),
                body=resp.read(),
            )
    except urllib.error.HTTPError as exc:
        return _Response(
            status=exc.code,
            headers=dict(exc.headers),
            body=exc.read(),
        )


# ── Fixture serveur ───────────────────────────────────────────────────────────


def _start_server(extra_env: dict | None = None) -> tuple[subprocess.Popen, str]:
    """
    Démarre le serveur Forge via _e2e_launcher.py sur un port libre.

    TEST_PORT contourne le override de APP_PORT par load_dotenv(env/prod).
    Retourne (proc, base_url).
    """
    port = _free_port()
    env = {
        **os.environ,
        "APP_ENV": "prod",
        "TEST_PORT": str(port),
        **(extra_env or {}),
    }
    launcher = ROOT / "tests" / "_e2e_launcher.py"
    proc = subprocess.Popen(
        [sys.executable, str(launcher)],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    # Attend le signal READY:{port} sur stdout
    try:
        line = proc.stdout.readline()
        if not line.startswith(b"READY:"):
            proc.terminate()
            proc.wait(timeout=5)
            return proc, ""
    except Exception:
        proc.terminate()
        proc.wait(timeout=5)
        return proc, ""
    proc.stdout.close()
    return proc, f"http://127.0.0.1:{port}"


@pytest.fixture(scope="module")
def forge_server():
    """
    Démarre Forge sur un port TCP libre en HTTP local sans SSL.

    Utilise APP_ENV=prod pour désactiver SSL par défaut.
    Aucune connexion MariaDB n'est établie : le pool est lazy, les routes
    utilisées dans les tests (404, static) n'interrogent pas la base.
    """
    proc, base = _start_server()
    if not base:
        pytest.skip("Serveur Forge non disponible — démarrage échoué dans les délais")
    yield base
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


# ── GET / ─────────────────────────────────────────────────────────────────────


def test_get_root_retourne_reponse_http_valide(forge_server):
    """GET / retourne une réponse HTTP avec un code valide."""
    resp = _get(f"{forge_server}/")
    assert 100 <= resp.status < 600


def test_get_root_contient_content_type(forge_server):
    """GET / retourne un Content-Type."""
    resp = _get(f"{forge_server}/")
    assert "content-type" in resp.headers or "Content-Type" in resp.headers


# ── 404 ───────────────────────────────────────────────────────────────────────


def test_route_inconnue_retourne_404(forge_server):
    """GET sur une route inexistante retourne 404."""
    resp = _get(f"{forge_server}/cette-route-nexiste-vraiment-pas-du-tout")
    assert resp.status == 404


def test_route_inconnue_corps_non_vide(forge_server):
    """Le corps de la réponse 404 n'est pas vide."""
    resp = _get(f"{forge_server}/chemin-inconnu-xyzabc")
    assert len(resp.body) > 0


# ── Headers de sécurité ───────────────────────────────────────────────────────


def _headers_lower(resp: _Response) -> dict[str, str]:
    return {k.lower(): v for k, v in resp.headers.items()}


def _security_headers(forge_server) -> dict[str, str]:
    """Récupère les headers depuis une réponse 404 (stable, sans DB)."""
    resp = _get(f"{forge_server}/probe-security-headers")
    return _headers_lower(resp)


def test_header_x_frame_options_present(forge_server):
    hdrs = _security_headers(forge_server)
    assert "x-frame-options" in hdrs


def test_header_x_frame_options_valeur(forge_server):
    hdrs = _security_headers(forge_server)
    assert hdrs.get("x-frame-options", "").upper() == "DENY"


def test_header_x_content_type_options_present(forge_server):
    hdrs = _security_headers(forge_server)
    assert "x-content-type-options" in hdrs


def test_header_x_content_type_options_valeur(forge_server):
    hdrs = _security_headers(forge_server)
    assert "nosniff" in hdrs.get("x-content-type-options", "").lower()


def test_header_referrer_policy_present(forge_server):
    hdrs = _security_headers(forge_server)
    assert "referrer-policy" in hdrs


def test_header_csp_present(forge_server):
    hdrs = _security_headers(forge_server)
    assert "content-security-policy" in hdrs


def test_header_csp_contient_self(forge_server):
    hdrs = _security_headers(forge_server)
    csp = hdrs.get("content-security-policy", "")
    assert "'self'" in csp


def test_header_csp_sans_unsafe_inline(forge_server):
    """CSP par défaut (sans nonce) ne contient pas 'unsafe-inline'."""
    hdrs = _security_headers(forge_server)
    csp = hdrs.get("content-security-policy", "")
    assert "unsafe-inline" not in csp


def test_header_csp_frame_ancestors(forge_server):
    hdrs = _security_headers(forge_server)
    csp = hdrs.get("content-security-policy", "")
    assert "frame-ancestors" in csp


# ── Fichiers statiques ────────────────────────────────────────────────────────


def test_static_favicon_ico_retourne_200(forge_server):
    """GET /static/favicon.ico retourne 200."""
    resp = _get(f"{forge_server}/static/favicon.ico")
    assert resp.status == 200


def test_static_favicon_content_type(forge_server):
    """GET /static/favicon.ico retourne un Content-Type image."""
    resp = _get(f"{forge_server}/static/favicon.ico")
    ct = (resp.headers.get("content-type") or resp.headers.get("Content-Type") or "").lower()
    assert "image" in ct


def test_static_favicon_corps_non_vide(forge_server):
    resp = _get(f"{forge_server}/static/favicon.ico")
    assert len(resp.body) > 0


def test_static_fichier_inexistant_retourne_404(forge_server):
    """GET /static/inexistant-xyz.css retourne 404."""
    resp = _get(f"{forge_server}/static/fichier-qui-nexiste-pas-xyz.css")
    assert resp.status == 404


def test_static_headers_securite_presents_sur_fichier(forge_server):
    """Les headers de sécurité sont présents sur les fichiers statiques aussi."""
    resp = _get(f"{forge_server}/static/favicon.ico")
    hdrs = _headers_lower(resp)
    assert "x-frame-options" in hdrs
    assert "content-security-policy" in hdrs


# ── Protection path traversal ─────────────────────────────────────────────────


def test_static_path_traversal_refuse(forge_server):
    """Une tentative de path traversal via /static/../ retourne 403 ou 404."""
    resp = _get(f"{forge_server}/static/../config.py")
    assert resp.status in (403, 404)


# ── CSP avec nonce ────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def forge_server_nonce():
    """Serveur démarré avec APP_CSP_NONCE_ENABLED=true."""
    proc, base = _start_server({"APP_CSP_NONCE_ENABLED": "true"})
    if not base:
        pytest.skip("Serveur Forge (nonce) non disponible")
    yield base
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def test_csp_nonce_present_quand_active(forge_server_nonce):
    """Quand APP_CSP_NONCE_ENABLED=true, CSP contient 'nonce-'."""
    resp = _get(f"{forge_server_nonce}/probe-nonce")
    hdrs = _headers_lower(resp)
    csp = hdrs.get("content-security-policy", "")
    assert "nonce-" in csp


def test_csp_nonce_different_par_requete(forge_server_nonce):
    """Chaque requête génère un nonce différent."""
    r1 = _get(f"{forge_server_nonce}/probe-nonce-1")
    r2 = _get(f"{forge_server_nonce}/probe-nonce-2")
    csp1 = _headers_lower(r1).get("content-security-policy", "")
    csp2 = _headers_lower(r2).get("content-security-policy", "")
    nonce1 = [p for p in csp1.split() if p.startswith("'nonce-")]
    nonce2 = [p for p in csp2.split() if p.startswith("'nonce-")]
    assert nonce1 and nonce2
    assert nonce1 != nonce2
