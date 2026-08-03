"""Tests — AUTH-DOC-CONSOLIDATION-001 : cohérence et complétude de la documentation Auth.

Vérifie que :
- docs/features/auth.md couvre toutes les sections majeures Auth ;
- les parcours login/MFA sont documentés ;
- les événements d'audit sont listés ;
- les commandes admin CLI sont documentées avec erreurs et conseils ;
- les liens croisés vers rbac.md, production-security.md et reference.md sont présents ;
- packages/forge-mvc-rbac/docs/reference.md pointe vers docs/features/auth.md ;
- docs/philosophy/security.md pointe vers docs/features/auth.md ;
- les limites restantes sont explicitées.
"""
from __future__ import annotations

import pathlib

import pytest
pytestmark = pytest.mark.meta

AUTH_MD = pathlib.Path("docs/features/auth.md")
RBAC_MD = pathlib.Path("packages/forge-mvc-rbac/docs/reference.md")
SECURITY_MD = pathlib.Path("docs/philosophy/security.md")
PRODUCTION_MD = pathlib.Path("docs/deployment/production-security.md")
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
# Sections principales de docs/features/auth.md
# ---------------------------------------------------------------------------

class TestSectionsPresentes:
    def test_section_vue_ensemble(self):
        assert "Vue d'ensemble" in _auth() or "Vue densemble" in _auth()

    def test_section_session(self):
        a = _auth()
        assert "Session" in a or "session" in a

    def test_section_cookies(self):
        assert "Cookie" in _auth() or "cookie" in _auth()

    # ADR-042 : les sections MFA, Challenge MFA, OIDC et Auth/User vers RBAC
    # ont été retirées du cœur (opt-ins / fonctionnalité non fournie). auth.md
    # ne documente plus que le cœur Auth/User.

    def test_section_audit(self):
        assert "Audit" in _auth()

    def test_section_admin_cli(self):
        assert "Administration CLI" in _auth()

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
    def test_login_applicatif_documente(self):
        a = _auth()
        assert "Login applicatif" in a or ("login_user" in a and "## Flux" in a)

    def test_reset_password_documente(self):
        assert "Reset password" in _auth() or "reset" in _auth().lower()

    def test_auth_md_sans_reference_optin(self):
        # ADR-042 : aucune référence de paquet opt-in dans le cœur.
        import re
        a = _auth()
        hits = sorted(set(re.findall(r"forge-mvc-(?!testing)[a-z0-9]+|forge_mvc_[a-z0-9]+", a)))
        assert not hits, f"docs/features/auth.md ne doit plus référencer d'opt-in (ADR-042) : {hits}"


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
    def test_auth_md_mentionne_rbac(self):
        # ADR-042 : auth.md (cœur) MENTIONNE RBAC mais ne lie plus l'opt-in.
        # L'absence de lien transversal est vérifiée par
        # test_docs_core_optins_decoupled_001.
        a = _auth()
        assert "RBAC" in a
        assert "](../rbac/" not in a, "auth.md ne doit plus lier l'opt-in rbac (ADR-042)."

    def test_auth_md_lien_vers_production_security(self):
        a = _auth()
        assert "production-security.md" in a or "production" in a.lower()

    def test_auth_md_lien_vers_reference(self):
        # DOC-CITED-PATHS-001 : cette assertion cherchait la sous-chaîne
        # `reference.md`, que seule satisfaisait une mention en prose de
        # `docs/reference.md`, monolithe découpé par DOCS-REFERENCE-SPLIT-001.
        # Le vrai lien de « Voir aussi » pointe vers `../reference/api.md` et ne
        # la contient pas : le garde passait donc sur un chemin mort, et serait
        # resté vert si le lien réel avait disparu.
        assert "../reference/api.md" in _auth()

    def test_auth_md_section_voir_aussi(self):
        a = _auth()
        assert "## Voir aussi" in a

    def test_rbac_md_mentionne_auth(self):
        # ADR-042 : la doc rbac (opt-in) peut MENTIONNER Auth/User mais ne lie
        # plus le cœur. L'absence de lien est vérifiée par le garde-fou dédié.
        r = _rbac()
        assert "Auth" in r or "auth" in r
        assert "](../features/auth.md" not in r, (
            "La doc rbac ne doit plus lier le cœur auth.md (ADR-042)."
        )

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
    # Commandes auth admin documentées sur la page CLI Sécurité (DOCS-API-CATALOG-003) ;
    # api.md n'est plus qu'un catalogue de liens.
    _ref = pathlib.Path("cli/security/docs/auth.md").read_text(encoding="utf-8")

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
