"""Tests SEC-CSP-HARDEN-001 : ajout de object-src 'none' et base-uri 'none'."""

from __future__ import annotations

from core.security.csp import build_csp_header


class TestObjectSrcNone:
    def test_csp_contains_object_src_none(self):
        csp = build_csp_header(nonce="abc123")
        assert "object-src 'none'" in csp

    def test_object_src_none_sans_nonce(self):
        csp = build_csp_header()
        assert "object-src 'none'" in csp

    def test_object_src_none_is_quoted(self):
        """La valeur 'none' doit être dans des single quotes (CSP spec)."""
        csp = build_csp_header(nonce="abc123")
        assert "object-src none" not in csp.replace("'none'", "")
        assert "object-src 'none'" in csp


class TestBaseUriNone:
    def test_csp_contains_base_uri_none(self):
        csp = build_csp_header(nonce="abc123")
        assert "base-uri 'none'" in csp

    def test_base_uri_none_sans_nonce(self):
        csp = build_csp_header()
        assert "base-uri 'none'" in csp

    def test_base_uri_none_is_quoted(self):
        csp = build_csp_header(nonce="abc123")
        assert "base-uri none" not in csp.replace("'none'", "")
        assert "base-uri 'none'" in csp


class TestCspIntegrity:
    def test_existing_directives_still_present(self):
        """Non-régression : les anciennes directives sont toujours là."""
        csp = build_csp_header(nonce="abc123")
        assert "default-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp
        assert "'nonce-abc123'" in csp

    def test_existing_directives_sans_nonce(self):
        csp = build_csp_header()
        assert "default-src 'self'" in csp
        assert "style-src 'self'" in csp
        assert "script-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp

    def test_directives_separated_by_semicolons(self):
        """La CSP utilise '; ' comme séparateur."""
        csp = build_csp_header(nonce="abc123")
        # 6 directives → 5 separators minimum (sans nonce: 5 directives)
        assert csp.count("; ") >= 5

    def test_pas_unsafe_inline(self):
        csp = build_csp_header(nonce="abc123")
        assert "unsafe-inline" not in csp

    def test_pas_unsafe_eval(self):
        csp = build_csp_header(nonce="abc123")
        assert "unsafe-eval" not in csp
