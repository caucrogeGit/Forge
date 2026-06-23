"""Tests — SECURITY-CACHE-001 : ticket livré et documention cohérente.

Vérifie que :
- la roadmap marque SECURITY-CACHE-001 comme livré ;
- la prochaine priorité est SECURITY-COOKIES-HOST-PREFIX-001 ;
- docs/deployment/production-security.md documente le Cache-Control sur les routes auth ;
- docs/features/auth.md mentionne Cache-Control: no-store.
"""
from __future__ import annotations

import pathlib

import pytest
pytestmark = pytest.mark.meta

ROADMAP = pathlib.Path("docs/roadmap/forge-roadmap.md")
PROD_SECURITY = pathlib.Path("docs/deployment/production-security.md")
AUTH_MD = pathlib.Path("docs/features/auth.md")


def _roadmap():
    return ROADMAP.read_text(encoding="utf-8")


def _prod():
    return PROD_SECURITY.read_text(encoding="utf-8")


def _auth():
    return AUTH_MD.read_text(encoding="utf-8")


class TestSecurityCache001Livre:
    def test_ticket_present_dans_roadmap(self):
        assert "SECURITY-CACHE-001" in _roadmap()

    def test_ticket_marque_livre(self):
        r = _roadmap()
        idx = r.index("SECURITY-CACHE-001")
        assert "livré" in r[idx: idx + 80]

    def test_security_cookies_host_prefix_livre(self):
        r = _roadmap()
        idx = r.index("SECURITY-COOKIES-HOST-PREFIX-001")
        assert "livré" in r[idx: idx + 80]


class TestDocumentationSecurityCache:
    def test_prod_security_mentionne_no_store(self):
        assert "no-store" in _prod().lower()

    def test_prod_security_mentionne_login_route(self):
        assert "/login" in _prod()

    def test_prod_security_mentionne_logout_route(self):
        assert "/logout" in _prod()

    def test_prod_security_mentionne_login_mfa(self):
        assert "/login/mfa" in _prod()

    def test_auth_md_mentionne_no_store(self):
        assert "no-store" in _auth()

    def test_auth_md_mentionne_cache_control(self):
        assert "Cache-Control" in _auth()


# ADR-044 : la constante _AUTH_NO_STORE_PATHS (liste des routes sensibles
# no-store) est du câblage applicatif, désormais hors du dépôt framework.
# Le mécanisme Cache-Control: no-store reste couvert côté core/CRUD
# (test_crud_export_csv, test_crud_export_audit, métas sécurité).
