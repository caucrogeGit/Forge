"""Tests SEC-CSP-COMPLETENESS-001 : img-src 'self' data: et form-action 'self'.

Verifie que :
- img-src 'self' data: est present dans la CSP (images encodees autorisees) ;
- form-action 'self' est present (anti-exfiltration via formulaires injectes) ;
- les directives precedentes sont preservees (non-regression ticket #8) ;
- le nombre total de directives est correct (garde-fou structurel).
"""
from __future__ import annotations

from core.security.csp import build_csp_header


# ---------------------------------------------------------------------------
# Classe 1 — directive img-src
# ---------------------------------------------------------------------------


class TestImgSrcDirective:

    def test_csp_contains_img_src_self_data(self):
        csp = build_csp_header(nonce="abc123")
        assert "img-src 'self' data:" in csp

    def test_img_src_present_sans_nonce(self):
        csp = build_csp_header()
        assert "img-src 'self' data:" in csp

    def test_img_src_dans_sa_directive(self):
        """data: est bien dans la directive img-src, pas ailleurs."""
        csp = build_csp_header(nonce="abc123")
        directives = [d.strip() for d in csp.split(";")]
        img_directives = [d for d in directives if d.startswith("img-src")]
        assert len(img_directives) == 1
        assert "data:" in img_directives[0]
        assert "'self'" in img_directives[0]

    def test_img_src_pas_de_typo_data_sans_deux_points(self):
        """Pas de 'data;' (sans deux-points) qui serait invalide."""
        csp = build_csp_header(nonce="abc123")
        assert "data;" not in csp

    def test_img_src_pas_de_typo_data_avec_espace(self):
        """Pas de 'data :' (espace avant deux-points) qui serait invalide."""
        csp = build_csp_header(nonce="abc123")
        assert "data :" not in csp


# ---------------------------------------------------------------------------
# Classe 2 — directive form-action
# ---------------------------------------------------------------------------


class TestFormActionDirective:

    def test_csp_contains_form_action_self(self):
        csp = build_csp_header(nonce="abc123")
        assert "form-action 'self'" in csp

    def test_form_action_present_sans_nonce(self):
        csp = build_csp_header()
        assert "form-action 'self'" in csp

    def test_form_action_avec_quotes(self):
        """form-action self sans quotes est invalide — les quotes sont obligatoires."""
        csp = build_csp_header(nonce="abc123")
        assert "form-action self" not in csp.replace("form-action 'self'", "")

    def test_form_action_dans_sa_directive(self):
        """form-action est bien une directive independante."""
        csp = build_csp_header(nonce="abc123")
        directives = [d.strip() for d in csp.split(";")]
        form_directives = [d for d in directives if d.startswith("form-action")]
        assert len(form_directives) == 1
        assert "'self'" in form_directives[0]


# ---------------------------------------------------------------------------
# Classe 3 — integrite apres ajout des deux directives (non-regression)
# ---------------------------------------------------------------------------


class TestCspIntegriteComplete:

    def test_default_src_preserve(self):
        csp = build_csp_header(nonce="abc123")
        assert "default-src 'self'" in csp

    def test_script_src_avec_nonce_preserve(self):
        csp = build_csp_header(nonce="abc123")
        assert "script-src 'self' 'nonce-abc123'" in csp

    def test_script_src_sans_nonce_preserve(self):
        csp = build_csp_header()
        assert "script-src 'self'" in csp

    def test_frame_ancestors_preserve(self):
        csp = build_csp_header(nonce="abc123")
        assert "frame-ancestors 'none'" in csp

    def test_object_src_preserve(self):
        csp = build_csp_header(nonce="abc123")
        assert "object-src 'none'" in csp

    def test_base_uri_preserve(self):
        csp = build_csp_header(nonce="abc123")
        assert "base-uri 'none'" in csp

    def test_nombre_total_de_directives(self):
        """8 directives = 7 separateurs point-virgule."""
        csp = build_csp_header(nonce="abc123")
        assert csp.count(";") == 7

    def test_nombre_total_de_directives_sans_nonce(self):
        csp = build_csp_header()
        assert csp.count(";") == 7

    def test_pas_unsafe_inline(self):
        csp = build_csp_header(nonce="abc123")
        assert "unsafe-inline" not in csp

    def test_pas_unsafe_eval(self):
        csp = build_csp_header(nonce="abc123")
        assert "unsafe-eval" not in csp
