"""Tests — AUTH-DOC-CONSOLIDATION-001 : cohérence et complétude de la documentation Auth.

Vérifie que :
- docs/auth.md couvre toutes les sections majeures Auth ;
- les parcours login/MFA sont documentés ;
- les événements d'audit sont listés ;
- les commandes admin CLI sont documentées avec erreurs et conseils ;
- les liens croisés vers rbac.md, production-security.md et reference.md sont présents ;
- docs/rbac.md pointe vers docs/auth.md ;
- docs/security.md pointe vers docs/auth.md ;
- les limites restantes sont explicitées.
"""
from __future__ import annotations

import pathlib

import pytest
pytestmark = pytest.mark.meta

AUTH_MD = pathlib.Path("docs/auth.md")
RBAC_MD = pathlib.Path("docs/rbac.md")
SECURITY_MD = pathlib.Path("docs/security.md")
PRODUCTION_MD = pathlib.Path("docs/production-security.md")
REFERENCE_MD = pathlib.Path("docs/reference/api.md")
ROADMAP_MD = pathlib.Path("docs/roadmap/forge-roadmap.md")


def _auth():
    return AUTH_MD.read_text(encoding="utf-8")


def _rbac():
    return RBAC_MD.read_text(encoding="utf-8")


def _security():
    return SECURITY_MD.read_text(encoding="utf-8")


def _roadmap():
    return ROADMAP_MD.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Existence des fichiers
# ---------------------------------------------------------------------------

class TestFichiersExistent:
    def test_auth_md_existe(self):
        assert AUTH_MD.exists()

    def test_rbac_md_existe(self):
        assert RBAC_MD.exists()

    def test_security_md_existe(self):
        assert SECURITY_MD.exists()

    def test_production_md_existe(self):
        assert PRODUCTION_MD.exists()

    def test_reference_md_existe(self):
        assert REFERENCE_MD.exists()


# ---------------------------------------------------------------------------
# Sections principales de docs/auth.md
# ---------------------------------------------------------------------------

class TestSectionsPresentes:
    def test_section_vue_ensemble(self):
        assert "Vue d'ensemble" in _auth() or "Vue densemble" in _auth()

    def test_section_session(self):
        a = _auth()
        assert "Session" in a or "session" in a

    def test_section_cookies(self):
        assert "Cookie" in _auth() or "cookie" in _auth()

    def test_section_mfa(self):
        assert "## MFA" in _auth()

    def test_section_oidc(self):
        assert "## OIDC" in _auth()

    def test_section_audit(self):
        assert "Audit" in _auth()

    def test_section_admin_cli(self):
        assert "Administration CLI" in _auth()

    def test_section_rbac(self):
        assert "RBAC" in _auth()

    def test_section_limites(self):
        assert "Limites restantes" in _auth()

    def test_section_flux(self):
        assert "Flux" in _auth()

    def test_section_voir_aussi(self):
        assert "Voir aussi" in _auth()


# ---------------------------------------------------------------------------
# Parcours Auth documentés
# ---------------------------------------------------------------------------

class TestParcoursDocumentes:
    def test_login_sans_mfa_documente(self):
        a = _auth()
        assert "Login classique sans MFA" in a or ("login" in a.lower() and "sans MFA" in a)

    def test_login_avec_mfa_documente(self):
        a = _auth()
        assert "Login avec MFA" in a

    def test_parcours_mfa_challenge_documente(self):
        a = _auth()
        assert "_auth_mfa_user_id" in a or "mfa_user_id" in a or "pending" in a.lower()

    def test_parcours_oidc_state_nonce_documente(self):
        a = _auth()
        assert "state" in a and "nonce" in a and "PKCE" in a

    def test_oidc_echange_reseau_non_fourni(self):
        a = _auth()
        assert "echange reseau" in a.lower() or "code -> token" in a or "Limites" in a

    def test_oidc_jwt_non_fourni(self):
        a = _auth()
        assert "JWT" in a


# ---------------------------------------------------------------------------
# Événements d'audit documentés
# ---------------------------------------------------------------------------

class TestEvenementsAuditDocumentes:
    def test_login_success_documente(self):
        assert "login.success" in _auth()

    def test_login_failed_documente(self):
        assert "login.failed" in _auth()

    def test_mfa_required_documente(self):
        assert "mfa.challenge.required" in _auth()

    def test_mfa_success_documente(self):
        assert "mfa.challenge.success" in _auth()

    def test_user_disabled_documente(self):
        assert "user.disabled" in _auth()

    def test_user_enabled_documente(self):
        assert "user.enabled" in _auth()

    def test_user_password_changed_documente(self):
        assert "user.password_changed" in _auth()

    def test_user_not_found_documente(self):
        assert "user.not_found" in _auth()

    def test_donnees_sensibles_filtrees_mentionnees(self):
        a = _auth()
        assert "password" in a and ("sensible" in a.lower() or "filtr" in a.lower() or "jamais" in a.lower())


# ---------------------------------------------------------------------------
# Commandes admin CLI documentées
# ---------------------------------------------------------------------------

class TestCommandesAdminDocumentees:
    def test_auth_user_disable_documente(self):
        assert "auth:user:disable" in _auth()

    def test_auth_user_enable_documente(self):
        assert "auth:user:enable" in _auth()

    def test_auth_user_password_documente(self):
        assert "auth:user:password" in _auth()

    def test_auth_user_role_add_documente(self):
        assert "auth:user:role:add" in _auth()

    def test_auth_user_roles_documente(self):
        assert "auth:user:roles" in _auth()

    def test_auth_user_create_documente(self):
        assert "auth:user:create" in _auth()

    def test_auth_user_list_documente(self):
        assert "auth:user:list" in _auth()

    def test_erreur_convention_documentee(self):
        a = _auth()
        assert "Erreur :" in a and "Conseil :" in a

    def test_audit_admin_documente(self):
        a = _auth()
        assert "user.disabled" in a and "user.enabled" in a


# ---------------------------------------------------------------------------
# Liens croisés présents
# ---------------------------------------------------------------------------

class TestLiensCroises:
    def test_auth_md_lien_vers_rbac(self):
        a = _auth()
        assert "rbac.md" in a or "[RBAC" in a

    def test_auth_md_lien_vers_production_security(self):
        a = _auth()
        assert "production-security.md" in a or "production" in a.lower()

    def test_auth_md_lien_vers_reference(self):
        assert "reference.md" in _auth()

    def test_auth_md_section_voir_aussi(self):
        a = _auth()
        assert "## Voir aussi" in a

    def test_rbac_md_lien_vers_auth(self):
        r = _rbac()
        assert "auth.md" in r

    def test_security_md_lien_vers_auth(self):
        s = _security()
        assert "auth.md" in s


# ---------------------------------------------------------------------------
# Limites restantes explicites
# ---------------------------------------------------------------------------

class TestLimitesRestantes:
    def test_interface_admin_non_fournie(self):
        assert "interface" in _auth().lower() and "admin" in _auth().lower()

    def test_jwt_non_fourni(self):
        assert "JWT" in _auth()

    def test_webauthn_non_fourni(self):
        assert "WebAuthn" in _auth() or "passkeys" in _auth()

    def test_saml_non_fourni(self):
        assert "SAML" in _auth()

    def test_multi_tenant_non_fourni(self):
        assert "multi-tenant" in _auth()


# ---------------------------------------------------------------------------
# Commandes admin dans reference.md
# ---------------------------------------------------------------------------

class TestReferenceDocumentee:
    _ref = REFERENCE_MD.read_text(encoding="utf-8")

    def test_auth_user_disable_dans_reference(self):
        assert "auth:user:disable" in self._ref

    def test_auth_user_enable_dans_reference(self):
        assert "auth:user:enable" in self._ref

    def test_auth_user_password_dans_reference(self):
        assert "auth:user:password" in self._ref

    def test_auth_user_role_add_dans_reference(self):
        assert "auth:user:role:add" in self._ref

    def test_auth_user_role_remove_dans_reference(self):
        assert "auth:user:role:remove" in self._ref


# ---------------------------------------------------------------------------
# Roadmap
# ---------------------------------------------------------------------------

class TestRoadmap:
    def test_auth_doc_consolidation_livre(self):
        r = _roadmap()
        assert "AUTH-DOC-CONSOLIDATION-001" in r
        idx = r.index("AUTH-DOC-CONSOLIDATION-001")
        assert "livré" in r[idx: idx + 60]

    def test_prochaine_priorite_workflow_statuts(self):
        r = _roadmap()
        idx = r.find("Prochaine priorité immédiate")
        assert idx != -1
        bloc = r[idx: idx + 200]
        assert "FORGE-DESIGN-ROADMAP-001" in bloc
