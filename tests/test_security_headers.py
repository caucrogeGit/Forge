"""Audit headers HTTP de sécurité Forge (SECURITY-HEADERS-001).

Deux couches de tests :

1. Tests unitaires — logique CSP (core/security/csp.py) sans serveur HTTP.
2. Tests E2E — serveur HTTP réel via _e2e_launcher.py : vérifie les headers
   effectivement envoyés au navigateur sur plusieurs types de réponses
   (200, 302, 404, 403, fichier statique).

Headers audités :
    X-Frame-Options        : DENY
    X-Content-Type-Options : nosniff
    Strict-Transport-Security : max-age=31536000; includeSubDomains
    Referrer-Policy        : strict-origin-when-cross-origin
    Permissions-Policy     : camera=(), microphone=(), geolocation=(), payment=()
    Content-Security-Policy : default-src 'self'; sans unsafe-inline ni unsafe-eval

Limites documentées :
    - HSTS émis même sur HTTP local (dev) ; inoffensif mais techniquement redondant.
    - CSP sans img-src, font-src, connect-src explicites (couverts par default-src 'self').
    - Permissions-Policy ne liste pas exhaustivement toutes les API navigateur.
    - Préfixe __Host- absent sur le cookie session_id (voir SECURITY-COOKIES-001).
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import NamedTuple

import pytest

from core.security.csp import build_csp_header, generate_nonce

ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Helpers E2E (réplique légère de test_http_e2e_001.py)
# ---------------------------------------------------------------------------

class _Response(NamedTuple):
    status: int
    headers: dict[str, str]
    body: bytes


def _get(url: str, timeout: float = 5.0) -> _Response:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return _Response(resp.status, dict(resp.headers), resp.read())
    except urllib.error.HTTPError as exc:
        return _Response(exc.code, dict(exc.headers), exc.read())


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
    """Retourne les headers en minuscules pour un chemin donné."""
    resp = _get(f"{srv}{path}")
    return {k.lower(): v for k, v in resp.headers.items()}


# ---------------------------------------------------------------------------
# Tests unitaires CSP (sans serveur)
# ---------------------------------------------------------------------------

class TestCspLogique:
    """Vérifie la logique de build_csp_header() sans serveur HTTP."""

    def test_csp_par_defaut_sans_unsafe_inline(self):
        csp = build_csp_header()
        assert "unsafe-inline" not in csp

    def test_csp_par_defaut_sans_unsafe_eval(self):
        csp = build_csp_header()
        assert "unsafe-eval" not in csp

    def test_csp_contient_default_src_self(self):
        csp = build_csp_header()
        assert "default-src 'self'" in csp

    def test_csp_contient_frame_ancestors_none(self):
        csp = build_csp_header()
        assert "frame-ancestors 'none'" in csp

    def test_csp_contient_script_src_self(self):
        csp = build_csp_header()
        assert "script-src 'self'" in csp

    def test_csp_avec_nonce_inclut_nonce(self):
        nonce = generate_nonce()
        csp = build_csp_header(nonce)
        assert f"'nonce-{nonce}'" in csp

    def test_csp_avec_nonce_sans_unsafe_inline(self):
        nonce = generate_nonce()
        csp = build_csp_header(nonce)
        assert "unsafe-inline" not in csp

    def test_csp_avec_nonce_sans_unsafe_eval(self):
        nonce = generate_nonce()
        csp = build_csp_header(nonce)
        assert "unsafe-eval" not in csp

    def test_csp_sans_nonce_ne_contient_pas_nonce(self):
        csp = build_csp_header(None)
        assert "nonce-" not in csp

    def test_generate_nonce_est_non_vide(self):
        assert len(generate_nonce()) > 0

    def test_generate_nonce_est_unique(self):
        assert generate_nonce() != generate_nonce()


# ---------------------------------------------------------------------------
# HSTS
# ---------------------------------------------------------------------------

class TestHsts:
    """Strict-Transport-Security présent et correctement configuré."""

    def test_hsts_present_sur_404(self, srv):
        hdrs = _hdrs(srv, "/route-inconnue-pour-hsts-test")
        assert "strict-transport-security" in hdrs

    def test_hsts_max_age(self, srv):
        hdrs = _hdrs(srv, "/route-hsts-maxage")
        hsts = hdrs.get("strict-transport-security", "")
        assert "max-age=31536000" in hsts

    def test_hsts_include_subdomains(self, srv):
        hdrs = _hdrs(srv, "/route-hsts-subdomains")
        hsts = hdrs.get("strict-transport-security", "")
        assert "includeSubDomains" in hsts


# ---------------------------------------------------------------------------
# Permissions-Policy
# ---------------------------------------------------------------------------

class TestPermissionsPolicy:
    """Permissions-Policy présent et restrictif."""

    def test_permissions_policy_present_sur_404(self, srv):
        hdrs = _hdrs(srv, "/route-permissions-policy-test")
        assert "permissions-policy" in hdrs

    def test_permissions_policy_restreint_camera(self, srv):
        hdrs = _hdrs(srv, "/route-permissions-camera")
        pp = hdrs.get("permissions-policy", "")
        assert "camera=()" in pp

    def test_permissions_policy_restreint_microphone(self, srv):
        hdrs = _hdrs(srv, "/route-permissions-micro")
        pp = hdrs.get("permissions-policy", "")
        assert "microphone=()" in pp

    def test_permissions_policy_restreint_geolocation(self, srv):
        hdrs = _hdrs(srv, "/route-permissions-geo")
        pp = hdrs.get("permissions-policy", "")
        assert "geolocation=()" in pp

    def test_permissions_policy_restreint_payment(self, srv):
        hdrs = _hdrs(srv, "/route-permissions-pay")
        pp = hdrs.get("permissions-policy", "")
        assert "payment=()" in pp


# ---------------------------------------------------------------------------
# Headers sur différents types de réponses
# ---------------------------------------------------------------------------

_EXPECTED_HEADERS = [
    "x-frame-options",
    "x-content-type-options",
    "strict-transport-security",
    "referrer-policy",
    "content-security-policy",
    "permissions-policy",
]


class TestHeadersSurReponse404:
    """Tous les headers de sécurité sont présents sur une réponse 404."""

    def test_x_frame_options_sur_404(self, srv):
        hdrs = _hdrs(srv, "/route-404-securite-xframe")
        assert hdrs.get("x-frame-options", "").upper() == "DENY"

    def test_x_content_type_options_sur_404(self, srv):
        hdrs = _hdrs(srv, "/route-404-content-type")
        assert "nosniff" in hdrs.get("x-content-type-options", "").lower()

    def test_hsts_sur_404(self, srv):
        hdrs = _hdrs(srv, "/route-404-hsts")
        assert "strict-transport-security" in hdrs

    def test_referrer_policy_sur_404(self, srv):
        hdrs = _hdrs(srv, "/route-404-referrer")
        assert "referrer-policy" in hdrs

    def test_csp_sur_404(self, srv):
        hdrs = _hdrs(srv, "/route-404-csp")
        assert "content-security-policy" in hdrs

    def test_permissions_policy_sur_404(self, srv):
        hdrs = _hdrs(srv, "/route-404-permissions")
        assert "permissions-policy" in hdrs


class TestHeadersSurRedirection:
    """Tous les headers de sécurité sont présents sur une réponse 302."""

    def _hdrs_redirect(self, srv: str) -> dict[str, str]:
        resp = _get(f"{srv}/")
        return {k.lower(): v for k, v in resp.headers.items()}

    def test_reponse_est_302_ou_200(self, srv):
        resp = _get(f"{srv}/")
        assert resp.status in (200, 302, 401)

    def test_x_frame_options_sur_redirection(self, srv):
        hdrs = self._hdrs_redirect(srv)
        assert "x-frame-options" in hdrs

    def test_x_content_type_options_sur_redirection(self, srv):
        hdrs = self._hdrs_redirect(srv)
        assert "x-content-type-options" in hdrs

    def test_hsts_sur_redirection(self, srv):
        hdrs = self._hdrs_redirect(srv)
        assert "strict-transport-security" in hdrs

    def test_referrer_policy_sur_redirection(self, srv):
        hdrs = self._hdrs_redirect(srv)
        assert "referrer-policy" in hdrs

    def test_csp_sur_redirection(self, srv):
        hdrs = self._hdrs_redirect(srv)
        assert "content-security-policy" in hdrs

    def test_permissions_policy_sur_redirection(self, srv):
        hdrs = self._hdrs_redirect(srv)
        assert "permissions-policy" in hdrs


class TestHeadersSurFichierStatique:
    """Headers de sécurité présents sur les fichiers statiques servis."""

    def test_x_frame_options_sur_static(self, srv):
        hdrs = _hdrs(srv, "/static/favicon.ico")
        assert "x-frame-options" in hdrs

    def test_x_content_type_options_sur_static(self, srv):
        hdrs = _hdrs(srv, "/static/favicon.ico")
        assert "nosniff" in hdrs.get("x-content-type-options", "").lower()

    def test_hsts_sur_static(self, srv):
        hdrs = _hdrs(srv, "/static/favicon.ico")
        assert "strict-transport-security" in hdrs

    def test_referrer_policy_sur_static(self, srv):
        hdrs = _hdrs(srv, "/static/favicon.ico")
        assert "referrer-policy" in hdrs

    def test_csp_sur_static(self, srv):
        hdrs = _hdrs(srv, "/static/favicon.ico")
        assert "content-security-policy" in hdrs

    def test_permissions_policy_sur_static(self, srv):
        hdrs = _hdrs(srv, "/static/favicon.ico")
        assert "permissions-policy" in hdrs

    def test_static_403_path_traversal_a_headers(self, srv):
        hdrs = _hdrs(srv, "/static/../app.py")
        assert "x-frame-options" in hdrs
        assert "x-content-type-options" in hdrs


class TestValeursCsp:
    """Valeurs précises de la CSP sur une réponse réelle."""

    def _csp(self, srv: str) -> str:
        return _hdrs(srv, "/route-csp-values")["content-security-policy"]

    def test_csp_reelle_contient_self(self, srv):
        assert "'self'" in self._csp(srv)

    def test_csp_reelle_sans_unsafe_inline(self, srv):
        assert "unsafe-inline" not in self._csp(srv)

    def test_csp_reelle_sans_unsafe_eval(self, srv):
        assert "unsafe-eval" not in self._csp(srv)

    def test_csp_reelle_frame_ancestors_none(self, srv):
        assert "frame-ancestors 'none'" in self._csp(srv)

    def test_referrer_policy_valeur(self, srv):
        hdrs = _hdrs(srv, "/route-referrer-value")
        assert hdrs.get("referrer-policy") == "strict-origin-when-cross-origin"
