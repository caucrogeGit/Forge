"""Tests — SECURITY-CACHE-001 : Cache-Control: no-store sur les routes auth sensibles.

Deux couches de tests :

1. Tests unitaires — constante _AUTH_NO_STORE_PATHS et logique de sélection.
2. Tests E2E — serveur HTTP réel : vérifie que Cache-Control: no-store est
   effectivement envoyé par le navigateur sur les routes auth.

Routes auditées :
    GET  /login      → 200, Cache-Control: no-store requis
    GET  /login/mfa  → 302 vers /login (sans challenge actif), no-store requis
    POST /logout     → 302, no-store requis (testé via constante, POST difficile sans CSRF)
    GET  /           → non sensible, no-store non forcé
    GET  /static/... → a son propre Cache-Control (max-age), pas no-store

Convention :
    - no-store ajouté si chemin (sans query string) ∈ _AUTH_NO_STORE_PATHS
    - no-store pas ajouté si Cache-Control déjà présent dans response.headers
    - les autres headers sécurité (X-Frame-Options, etc.) sont conservés
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import urllib.error
import urllib.request
import urllib.response
from pathlib import Path
from typing import NamedTuple

import pytest

ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Infrastructure E2E (même pattern que test_security_headers.py)
# ---------------------------------------------------------------------------

class _Response(NamedTuple):
    status: int
    headers: dict[str, str]
    body: bytes


def _get(url: str, timeout: float = 5.0, follow_redirects: bool = True) -> _Response:
    """GET HTTP — suit les redirections par défaut."""
    if not follow_redirects:
        opener = urllib.request.build_opener(_NoRedirectHandler)
    else:
        opener = urllib.request.build_opener()
    try:
        with opener.open(url, timeout=timeout) as resp:
            return _Response(resp.status, dict(resp.headers), resp.read())
    except urllib.error.HTTPError as exc:
        return _Response(exc.code, dict(exc.headers), exc.read())


class _NoRedirectHandler(urllib.request.HTTPErrorProcessor):
    """Intercepte les 3xx sans les suivre."""
    def http_response(self, request, response):
        return response
    https_response = http_response


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def _start_server() -> tuple[subprocess.Popen, str]:
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
            return proc, ""
    except Exception:
        proc.terminate()
        proc.wait(timeout=5)
        return proc, ""
    proc.stdout.close()
    return proc, f"http://127.0.0.1:{port}"


@pytest.fixture(scope="module")
def srv():
    """Serveur Forge réel sur port libre — partagé pour tout le module."""
    proc, base = _start_server()
    if not base:
        pytest.skip("Serveur Forge non disponible")
    yield base
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def _hdrs(srv: str, path: str) -> dict[str, str]:
    """Headers en minuscules, suit les redirections."""
    resp = _get(f"{srv}{path}")
    return {k.lower(): v for k, v in resp.headers.items()}


def _hdrs_no_redirect(srv: str, path: str) -> dict[str, str]:
    """Headers en minuscules, ne suit pas les redirections (pour voir les 302)."""
    resp = _get(f"{srv}{path}", follow_redirects=False)
    return {k.lower(): v for k, v in resp.headers.items()}


# ---------------------------------------------------------------------------
# Tests unitaires — constante _AUTH_NO_STORE_PATHS
# ---------------------------------------------------------------------------

class TestConstanteAuthNoStorePaths:
    """Vérifie que la constante contient exactement les chemins attendus."""

    def test_login_dans_no_store_paths(self):
        from app import _AUTH_NO_STORE_PATHS
        assert "/login" in _AUTH_NO_STORE_PATHS

    def test_logout_dans_no_store_paths(self):
        from app import _AUTH_NO_STORE_PATHS
        assert "/logout" in _AUTH_NO_STORE_PATHS

    def test_login_mfa_dans_no_store_paths(self):
        from app import _AUTH_NO_STORE_PATHS
        assert "/login/mfa" in _AUTH_NO_STORE_PATHS

    def test_no_store_paths_est_un_frozenset(self):
        from app import _AUTH_NO_STORE_PATHS
        assert isinstance(_AUTH_NO_STORE_PATHS, frozenset)

    def test_racine_non_dans_no_store_paths(self):
        from app import _AUTH_NO_STORE_PATHS
        assert "/" not in _AUTH_NO_STORE_PATHS

    def test_static_non_dans_no_store_paths(self):
        from app import _AUTH_NO_STORE_PATHS
        assert "/static" not in _AUTH_NO_STORE_PATHS
        assert "/static/app.css" not in _AUTH_NO_STORE_PATHS


# ---------------------------------------------------------------------------
# Tests E2E — GET /login → Cache-Control: no-store
# ---------------------------------------------------------------------------

class TestCacheControlLogin:
    """La page login retourne Cache-Control: no-store."""

    def test_login_retourne_200_ou_302(self, srv):
        resp = _get(f"{srv}/login")
        assert resp.status in (200, 302)

    def test_login_cache_control_present(self, srv):
        hdrs = _hdrs(srv, "/login")
        assert "cache-control" in hdrs

    def test_login_cache_control_no_store(self, srv):
        hdrs = _hdrs(srv, "/login")
        assert "no-store" in hdrs.get("cache-control", "").lower()

    def test_login_x_frame_options_conserve(self, srv):
        hdrs = _hdrs(srv, "/login")
        assert hdrs.get("x-frame-options", "").upper() == "DENY"

    def test_login_x_content_type_options_conserve(self, srv):
        hdrs = _hdrs(srv, "/login")
        assert "nosniff" in hdrs.get("x-content-type-options", "").lower()

    def test_login_hsts_conserve(self, srv):
        hdrs = _hdrs(srv, "/login")
        assert "strict-transport-security" in hdrs

    def test_login_csp_conserve(self, srv):
        hdrs = _hdrs(srv, "/login")
        assert "content-security-policy" in hdrs

    def test_login_referrer_policy_conserve(self, srv):
        hdrs = _hdrs(srv, "/login")
        assert "referrer-policy" in hdrs

    def test_login_permissions_policy_conserve(self, srv):
        hdrs = _hdrs(srv, "/login")
        assert "permissions-policy" in hdrs


# ---------------------------------------------------------------------------
# Tests E2E — GET /login/mfa → Cache-Control: no-store (même si 302)
# ---------------------------------------------------------------------------

class TestCacheControlLoginMfa:
    """La page MFA retourne Cache-Control: no-store (redirigée ou non)."""

    def test_mfa_cache_control_present_sans_redirect(self, srv):
        hdrs = _hdrs_no_redirect(srv, "/login/mfa")
        assert "cache-control" in hdrs

    def test_mfa_cache_control_no_store_sans_redirect(self, srv):
        hdrs = _hdrs_no_redirect(srv, "/login/mfa")
        assert "no-store" in hdrs.get("cache-control", "").lower()

    def test_mfa_x_frame_options_present(self, srv):
        hdrs = _hdrs_no_redirect(srv, "/login/mfa")
        assert "x-frame-options" in hdrs

    def test_mfa_hsts_present(self, srv):
        hdrs = _hdrs_no_redirect(srv, "/login/mfa")
        assert "strict-transport-security" in hdrs


# ---------------------------------------------------------------------------
# Tests E2E — fichiers statiques ne reçoivent pas no-store
# ---------------------------------------------------------------------------

class TestPasDeCacheControlSurStatique:
    """Les fichiers statiques conservent leur propre Cache-Control (pas no-store)."""

    def test_static_pas_de_no_store(self, srv):
        hdrs = _hdrs(srv, "/static/favicon.ico")
        cc = hdrs.get("cache-control", "").lower()
        assert "no-store" not in cc

    def test_static_a_son_propre_cache_control(self, srv):
        hdrs = _hdrs(srv, "/static/favicon.ico")
        cc = hdrs.get("cache-control", "")
        assert "max-age" in cc.lower()

    def test_static_x_frame_options_conserve(self, srv):
        hdrs = _hdrs(srv, "/static/favicon.ico")
        assert "x-frame-options" in hdrs


# ---------------------------------------------------------------------------
# Tests E2E — routes non-auth n'ont pas no-store forcé
# ---------------------------------------------------------------------------

class TestPasDeCacheControlSurNonAuth:
    """Les routes non-auth (404, /) ne reçoivent pas no-store automatiquement."""

    def test_404_pas_de_no_store_force(self, srv):
        hdrs = _hdrs(srv, "/route-inconnue-cache-test-xyz")
        cc = hdrs.get("cache-control", "").lower()
        # Une 404 n'est pas une route auth, aucun no-store ajouté par _AUTH_NO_STORE_PATHS
        assert "no-store" not in cc

    def test_404_headers_securite_conserves(self, srv):
        hdrs = _hdrs(srv, "/route-inconnue-cache-test-xyz2")
        assert "x-frame-options" in hdrs
        assert "strict-transport-security" in hdrs
        assert "content-security-policy" in hdrs
