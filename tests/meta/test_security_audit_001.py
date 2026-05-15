"""
Tests documentaires SECURITY-AUDIT-001 — Rapport d'audit de sécurité.

Vérifie que le rapport docs/history/audits/security-audit-001.md :
  - existe ;
  - contient les sections obligatoires ;
  - couvre les dix domaines de sécurité ;
  - mentionne les risques identifiés ;
  - référence les tickets de suivi obligatoires ;
  - que la roadmap mentionne SECURITY-AUDIT-001 comme livré
    et SECURITY-CSRF-AUDIT-001 comme prochaine priorité.
"""
from __future__ import annotations

from pathlib import Path

import pytest
pytestmark = pytest.mark.meta

ROOT  = Path(__file__).resolve().parent.parent.parent
AUDIT = (ROOT / "docs" / "history" / "audits" / "security-audit-001.md").read_text(encoding="utf-8")
ROADMAP = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")


# ── Existence et titre ────────────────────────────────────────────────────────

def test_rapport_existe():
    assert (ROOT / "docs" / "history" / "audits" / "security-audit-001.md").exists()


def test_rapport_titre():
    assert "SECURITY-AUDIT-001" in AUDIT


# ── Sections obligatoires ─────────────────────────────────────────────────────

def test_section_objectif():
    assert "## Objectif" in AUDIT


def test_section_resume_executif():
    assert "Résumé exécutif" in AUDIT


def test_section_methode():
    assert "Méthode" in AUDIT


def test_section_perimetre():
    assert "Périmètre" in AUDIT


def test_section_synthese_risques():
    assert "Synthèse des risques" in AUDIT


def test_section_zones_bien_protegees():
    assert "Zones bien protégées" in AUDIT


def test_section_zones_insuffisantes():
    assert "insuffisantes" in AUDIT.lower() or "Zones insuffisantes" in AUDIT


def test_section_risques_critiques():
    assert "Risques critiques" in AUDIT


def test_section_risques_moyens():
    assert "Risques moyens" in AUDIT


def test_section_risques_faibles():
    assert "Risques faibles" in AUDIT


def test_section_recommandations():
    assert "## Recommandations" in AUDIT


def test_section_tickets_proposes():
    assert "Tickets proposés" in AUDIT


# ── Dix domaines couverts ─────────────────────────────────────────────────────

def test_domaine_csrf():
    assert "CSRF" in AUDIT


def test_domaine_cookies():
    assert "Cookie" in AUDIT or "cookie" in AUDIT.lower()


def test_domaine_sessions():
    assert "Session" in AUDIT or "session" in AUDIT.lower()


def test_domaine_headers():
    assert "Headers" in AUDIT or "header" in AUDIT.lower()


def test_domaine_uploads():
    assert "Upload" in AUDIT or "upload" in AUDIT.lower()


def test_domaine_auth():
    assert "Auth" in AUDIT


def test_domaine_rbac():
    assert "RBAC" in AUDIT


def test_domaine_mfa():
    assert "MFA" in AUDIT


def test_domaine_oidc():
    assert "OIDC" in AUDIT


def test_domaine_runtime_errors():
    assert "Runtime" in AUDIT or "runtime" in AUDIT.lower()


def test_domaine_sql():
    assert "SQL" in AUDIT


def test_domaine_migrations():
    assert "Migration" in AUDIT or "migration" in AUDIT.lower()


def test_domaine_templates():
    assert "Template" in AUDIT or "template" in AUDIT.lower()


def test_domaine_xss():
    assert "XSS" in AUDIT


def test_domaine_static():
    assert "statique" in AUDIT.lower() or "static" in AUDIT.lower()


def test_domaine_deploiement():
    assert "Déploiement" in AUDIT or "déploiement" in AUDIT.lower()


# ── Éléments techniques clés mentionnés ──────────────────────────────────────

def test_mentionne_autoescape():
    assert "autoescape" in AUDIT.lower() or "autoescape" in AUDIT


def test_mentionne_httponly():
    assert "HttpOnly" in AUDIT


def test_mentionne_samesite():
    assert "SameSite" in AUDIT


def test_mentionne_hsts():
    assert "Strict-Transport-Security" in AUDIT or "HSTS" in AUDIT


def test_mentionne_csp():
    assert "Content-Security-Policy" in AUDIT or "CSP" in AUDIT


def test_mentionne_parametrised_sql():
    assert "paramétré" in AUDIT.lower() or "paramétrisé" in AUDIT.lower() or "placeholder" in AUDIT.lower()


def test_mentionne_argon2():
    assert "argon2" in AUDIT.lower() or "Argon2" in AUDIT


def test_mentionne_pkce():
    assert "PKCE" in AUDIT


def test_mentionne_rate_limit():
    assert "rate limit" in AUDIT.lower() or "rate_limit" in AUDIT.lower()


def test_mentionne_commonpath():
    assert "commonpath" in AUDIT.lower() or "anti-traversal" in AUDIT.lower() or "traversal" in AUDIT.lower()


# ── Lacunes / risques identifiés ──────────────────────────────────────────────

def test_signale_audit_log_non_branche():
    assert "audit" in AUDIT.lower()
    assert "auth_controller" in AUDIT.lower() or "auth_controller.py" in AUDIT


def test_signale_csrf_non_teste_http():
    assert "HTTP réel" in AUDIT or "http réel" in AUDIT.lower()


def test_signale_hsts_sur_http():
    assert "dev" in AUDIT.lower() or "HTTP" in AUDIT


def test_signale_permissions_policy_absent():
    assert "Permissions-Policy" in AUDIT


def test_signale_cache_control_absent():
    assert "Cache-Control" in AUDIT or "no-store" in AUDIT


def test_signale_nginx_http_only():
    assert "nginx" in AUDIT.lower()
    assert "http" in AUDIT.lower()


# ── Tickets de suivi obligatoires ────────────────────────────────────────────

def test_ticket_security_csrf_audit():
    assert "SECURITY-CSRF-AUDIT-001" in AUDIT


def test_ticket_security_cookies():
    assert "SECURITY-COOKIES-001" in AUDIT


def test_ticket_security_headers():
    assert "SECURITY-HEADERS-001" in AUDIT


def test_ticket_security_uploads_audit():
    assert "SECURITY-UPLOADS-AUDIT-001" in AUDIT


def test_ticket_security_rbac_audit():
    assert "SECURITY-RBAC-AUDIT-001" in AUDIT


def test_ticket_deploy_prod_security_doc():
    assert "DEPLOY-PROD-SECURITY-DOC-001" in AUDIT


def test_ticket_security_auth_audit():
    assert "SECURITY-AUTH-AUDIT-001" in AUDIT


# ── Roadmap ───────────────────────────────────────────────────────────────────

def test_roadmap_mentionne_security_audit_livre():
    assert "SECURITY-AUDIT-001" in ROADMAP


def test_roadmap_prochaine_priorite_security_csrf():
    assert "SECURITY-CSRF-AUDIT-001" in ROADMAP
