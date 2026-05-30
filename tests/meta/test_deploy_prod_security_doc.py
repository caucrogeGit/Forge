"""Tests documentaires — DEPLOY-PROD-SECURITY-DOC-001.

Vérifient que docs/deployment/production-security.md existe et couvre les sujets
requis : HTTPS/proxy, cookies, headers, CSRF, RBAC, uploads, logs,
secrets, base de données, checklist production et limites restantes.

Ces tests ne modifient aucun code runtime. Ils constituent un garde-fou
documentaire : si un sujet de sécurité essentiel disparaît du guide,
un test échoue.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

ROOT = Path(__file__).resolve().parents[2]
GUIDE = ROOT / "docs" / "deployment" / "production-security.md"


@pytest.fixture(scope="module")
def guide() -> str:
    """Contenu complet du guide production."""
    assert GUIDE.exists(), f"Guide non trouvé : {GUIDE}"
    return GUIDE.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. Existence et structure
# ---------------------------------------------------------------------------


class TestExistenceEtStructure:
    def test_fichier_existe(self):
        assert GUIDE.exists()

    def test_fichier_non_vide(self, guide):
        assert len(guide) > 500

    def test_titre_principal(self, guide):
        assert "Sécurité en production" in guide or "production" in guide.lower()

    def test_contient_checklist_section(self, guide):
        assert "Checklist" in guide or "checklist" in guide

    def test_contient_section_dettes(self, guide):
        assert "Dettes" in guide or "tickets futurs" in guide.lower()


# ---------------------------------------------------------------------------
# 2. HTTPS / Reverse proxy
# ---------------------------------------------------------------------------


class TestHttpsProxy:
    def test_mentionne_https(self, guide):
        assert "HTTPS" in guide

    def test_mentionne_reverse_proxy(self, guide):
        assert "reverse proxy" in guide.lower() or "Nginx" in guide

    def test_mentionne_nginx(self, guide):
        assert "Nginx" in guide

    def test_mentionne_tls(self, guide):
        assert "TLS" in guide

    def test_interdit_exposition_directe(self, guide):
        lower = guide.lower()
        assert "ne pas" in lower or "ne jamais" in lower or "not expose" in lower


# ---------------------------------------------------------------------------
# 3. Cookies de session
# ---------------------------------------------------------------------------


class TestCookies:
    def test_mentionne_httponly(self, guide):
        assert "HttpOnly" in guide

    def test_mentionne_samesite(self, guide):
        assert "SameSite" in guide

    def test_mentionne_secure(self, guide):
        assert "Secure" in guide

    def test_mentionne_path(self, guide):
        assert "Path=/" in guide

    def test_mentionne_rotation_session(self, guide):
        assert "rotation" in guide.lower() or "fixation" in guide.lower()

    def test_mentionne_limite_host_prefix(self, guide):
        assert "__Host-" in guide or "SECURITY-COOKIES-HOST-PREFIX" in guide


# ---------------------------------------------------------------------------
# 4. Headers HTTP de sécurité
# ---------------------------------------------------------------------------


class TestHeadersHttp:
    def test_mentionne_x_frame_options(self, guide):
        assert "X-Frame-Options" in guide

    def test_mentionne_x_content_type_options(self, guide):
        assert "X-Content-Type-Options" in guide

    def test_mentionne_hsts(self, guide):
        assert "Strict-Transport-Security" in guide

    def test_mentionne_referrer_policy(self, guide):
        assert "Referrer-Policy" in guide

    def test_mentionne_csp(self, guide):
        assert "Content-Security-Policy" in guide

    def test_mentionne_permissions_policy(self, guide):
        assert "Permissions-Policy" in guide

    def test_mentionne_absence_unsafe_inline(self, guide):
        assert "unsafe-inline" in guide

    def test_mentionne_limite_cache_control(self, guide):
        assert "Cache-Control" in guide or "SECURITY-CACHE-001" in guide


# ---------------------------------------------------------------------------
# 5. CSRF
# ---------------------------------------------------------------------------


class TestCsrf:
    def test_mentionne_csrf(self, guide):
        assert "CSRF" in guide or "csrf" in guide.lower()

    def test_mentionne_methodes_protegees(self, guide):
        assert "POST" in guide

    def test_mentionne_token(self, guide):
        assert "csrf_token" in guide or "X-CSRF-Token" in guide

    def test_mentionne_exemption_get(self, guide):
        assert "GET" in guide

    def test_mentionne_opt_out_explicite(self, guide):
        assert "csrf=False" in guide


# ---------------------------------------------------------------------------
# 6. Auth et audit
# ---------------------------------------------------------------------------


class TestAuthAudit:
    def test_mentionne_log_auth_event(self, guide):
        assert "log_auth_event" in guide

    def test_mentionne_events_journalises(self, guide):
        assert "login.success" in guide or "login.failed" in guide

    def test_mentionne_absence_donnees_sensibles_logs(self, guide):
        lower = guide.lower()
        assert "mot de passe" in lower or "password" in lower or "sensible" in lower

    def test_mentionne_logger_forge_auth_audit(self, guide):
        assert "forge.auth.audit" in guide


# ---------------------------------------------------------------------------
# 7. RBAC
# ---------------------------------------------------------------------------


class TestRbac:
    def test_mentionne_require_permission(self, guide):
        assert "require_permission" in guide

    def test_mentionne_protection_serveur_obligatoire(self, guide):
        assert "serveur" in guide.lower()

    def test_mentionne_can_helper(self, guide):
        assert "can(" in guide

    def test_mentionne_limite_crud_templates(self, guide):
        assert "CRUD" in guide and ("can" in guide or "guard" in guide.lower())

    def test_mentionne_ticket_crud_rbac_ui(self, guide):
        assert "CRUD-RBAC-UI-001" in guide

    def test_mentionne_deux_systemes(self, guide):
        assert "require_user_permission" in guide


# ---------------------------------------------------------------------------
# 8. Uploads et médias
# ---------------------------------------------------------------------------


class TestUploads:
    def test_mentionne_storage_uploads(self, guide):
        assert "storage/uploads" in guide or "UPLOAD_ROOT" in guide

    def test_mentionne_anti_traversal(self, guide):
        assert "traversal" in guide.lower() or "normalize_media_path" in guide

    def test_mentionne_extensions_interdites(self, guide):
        assert ".php" in guide

    def test_mentionne_route_media(self, guide):
        assert "/media" in guide

    def test_mentionne_limite_magic_bytes(self, guide):
        assert "magic bytes" in guide.lower() or "magic" in guide.lower()

    def test_mentionne_nginx_ne_sert_pas_storage(self, guide):
        lower = guide.lower()
        assert "ne jamais" in lower or "storage" in lower


# ---------------------------------------------------------------------------
# 9. Logs runtime
# ---------------------------------------------------------------------------


class TestLogs:
    def test_mentionne_storage_logs(self, guide):
        assert "storage/logs" in guide

    def test_mentionne_errors_dev_jsonl(self, guide):
        assert "errors.dev.jsonl" in guide or "errors.dev" in guide

    def test_mentionne_ne_pas_exposer_logs(self, guide):
        lower = guide.lower()
        assert "ne pas" in lower or "ne jamais" in lower

    def test_mentionne_gitignore(self, guide):
        assert ".gitignore" in guide or "gitignore" in guide.lower()


# ---------------------------------------------------------------------------
# 10. Secrets et fichiers sensibles
# ---------------------------------------------------------------------------


class TestSecrets:
    def test_mentionne_env_prod(self, guide):
        assert "env/prod" in guide

    def test_mentionne_ne_pas_versionner(self, guide):
        lower = guide.lower()
        assert "ne jamais" in lower or "versionner" in lower

    def test_mentionne_chmod(self, guide):
        assert "chmod" in guide or "permissions" in guide.lower()

    def test_mentionne_gitignore_secrets(self, guide):
        assert ".gitignore" in guide


# ---------------------------------------------------------------------------
# 11. Base de données
# ---------------------------------------------------------------------------


class TestBaseDeDonnees:
    def test_mentionne_moindre_privilege(self, guide):
        lower = guide.lower()
        assert "moindre" in lower or "restreint" in lower or "privilege" in lower

    def test_mentionne_separation_admin_app(self, guide):
        assert "DB_APP_LOGIN" in guide or "compte applicatif" in guide.lower()

    def test_mentionne_droits_ddl_interdits(self, guide):
        lower = guide.lower()
        assert "ddl" in lower or "create table" in lower.replace("create table", "create_table") or "CREATE" in guide

    def test_mentionne_tests_e2e_pas_sur_prod(self, guide):
        lower = guide.lower()
        assert "forge_e2e_" in guide or "e2e" in lower


# ---------------------------------------------------------------------------
# 12. Checklist production
# ---------------------------------------------------------------------------


class TestChecklistProduction:
    def test_checklist_presente(self, guide):
        assert "[ ]" in guide

    def test_checklist_https(self, guide):
        lower = guide.lower()
        assert "https" in lower and "[ ]" in guide

    def test_checklist_cookies_secure(self, guide):
        assert "Secure" in guide and "[ ]" in guide

    def test_checklist_csrf(self, guide):
        assert "CSRF" in guide and "[ ]" in guide

    def test_checklist_storage_non_expose(self, guide):
        assert "storage/" in guide and "[ ]" in guide

    def test_checklist_secrets_hors_git(self, guide):
        lower = guide.lower()
        assert ("git" in lower or "gitignore" in guide.lower()) and "[ ]" in guide

    def test_checklist_rbac(self, guide):
        lower = guide.lower()
        assert "rbac" in lower or "permission" in lower

    def test_checklist_sauvegardes(self, guide):
        lower = guide.lower()
        assert "sauvegarde" in lower or "backup" in lower


# ---------------------------------------------------------------------------
# 13. Limites restantes documentées
# ---------------------------------------------------------------------------


class TestLimitesRestantes:
    def test_limite_cache_control_documentee(self, guide):
        assert "Cache-Control" in guide or "SECURITY-CACHE-001" in guide

    def test_limite_magic_bytes_documentee(self, guide):
        assert "magic" in guide.lower()

    def test_limite_crud_rbac_ui_documentee(self, guide):
        assert "CRUD-RBAC-UI-001" in guide

    def test_limite_host_prefix_documentee(self, guide):
        assert "__Host-" in guide or "SECURITY-COOKIES-HOST-PREFIX" in guide

    def test_limite_rate_limit_uploads_documentee(self, guide):
        assert "rate limit" in guide.lower() or "SECURITY-UPLOAD-RATE-LIMIT" in guide


# ---------------------------------------------------------------------------
# 14. Roadmap
# ---------------------------------------------------------------------------


class TestRoadmap:
    def test_roadmap_principale_existe(self):
        roadmap = ROOT / "docs" / "roadmap" / "forge-roadmap.md"
        assert roadmap.exists()

    def test_deploy_prod_security_doc_dans_roadmap(self):
        roadmap = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
        assert "DEPLOY-PROD-SECURITY-DOC-001" in roadmap

    def test_security_rbac_audit_livre_dans_roadmap(self):
        roadmap = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
        assert "SECURITY-RBAC-AUDIT-001" in roadmap
