"""Garde-fou MFA-SECRET-STORAGE-POLICY-001.

Vérifie que la politique officielle de stockage des secrets MFA est documentée
dans docs/reference/auth-mfa.md avec toutes les sections requises.

Règles vérifiées :
- La section "Politique de stockage" existe.
- La politique distingue dev/test de production.
- La politique couvre les secrets TOTP et les codes de récupération séparément.
- La distinction hash (codes de récupération) vs chiffrement (TOTP) est présente.
- Les exigences avant production-ready sont listées.
- Aucune affirmation "production-ready" non qualifiée.
- MFA reste opt-in (Beta), hors [all] par choix de sécurité explicite.
- pyotp n'est pas une dépendance runtime du core.
- forge-mvc-mfa n'est pas dans le core.
"""
from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
# Doc embarquée par paquet depuis l'ADR-038.
AUTH_MFA_REF = PROJECT_ROOT / "packages" / "forge-mvc-mfa" / "docs" / "reference.md"
MFA_PYPROJECT = PROJECT_ROOT / "packages" / "forge-mvc-mfa" / "pyproject.toml"
ROOT_PYPROJECT = PROJECT_ROOT / "pyproject.toml"
CORE_DIR = PROJECT_ROOT / "core"


class TestStoragePolicySectionExists:
    """La section 'Politique de stockage des secrets MFA' existe."""

    def test_section_header_present(self):
        text = AUTH_MFA_REF.read_text(encoding="utf-8")
        assert "Politique de stockage des secrets MFA" in text, (
            "docs/reference/auth-mfa.md doit contenir une section "
            "'Politique de stockage des secrets MFA'."
        )

    def test_subsection_etat_des_lieux(self):
        """La page dit ce qui est en place, quel que soit le titre retenu.

        Ce contrôle exigeait le libellé exact « Statut actuel »
        (`OPTINS-MATURITY-FOLLOWS-CORE-001`). Le titre a changé en même temps
        que la prose de maturité, sans que la fin visée cesse d'être vraie :
        un lecteur doit trouver ce que le module protège et comment.
        """
        text = AUTH_MFA_REF.read_text(encoding="utf-8")
        assert "Ce qui est en place" in text or "Statut actuel" in text, (
            "La section politique doit dire ce qui est en place."
        )

    def test_subsection_developpement(self):
        text = AUTH_MFA_REF.read_text(encoding="utf-8")
        assert (
            "Développement" in text or "Developpement" in text or "développement" in text
        ), "La section politique doit couvrir le contexte développement."

    def test_subsection_production(self):
        text = AUTH_MFA_REF.read_text(encoding="utf-8")
        assert "Production" in text or "production" in text, (
            "La section politique doit couvrir le contexte production."
        )

    def test_subsection_exigences_avant_production(self):
        text = AUTH_MFA_REF.read_text(encoding="utf-8")
        assert (
            "Exigences avant production" in text
            or "exigences avant production" in text
            or "production-ready" in text.lower()
        ), (
            "La section politique doit lister les exigences avant production-ready."
        )

    def test_subsection_tickets_lies(self):
        text = AUTH_MFA_REF.read_text(encoding="utf-8")
        assert "Tickets liés" in text or "SEC-MFA-SECRET-ENCRYPTION-001" in text, (
            "La section politique doit référencer les tickets liés (en particulier "
            "SEC-MFA-SECRET-ENCRYPTION-001)."
        )


class TestTotpSecretStorageDocumented:
    """Le stockage du secret TOTP est documenté avec précision."""

    def test_totp_encryption_documented(self):
        text = AUTH_MFA_REF.read_text(encoding="utf-8")
        assert (
            "chiffré" in text.lower()
            or "chiffrement" in text.lower()
            or "encrypt" in text.lower()
            or "Fernet" in text
        ), (
            "docs/reference/auth-mfa.md doit documenter que le secret TOTP "
            "est chiffré au repos (SEC-MFA-SECRET-ENCRYPTION-001 livré)."
        )

    def test_totp_cannot_be_hashed(self):
        text = AUTH_MFA_REF.read_text(encoding="utf-8")
        assert (
            "hash" in text.lower() and (
                "sens unique" in text
                or "irréversible" in text
                or "impossible" in text
                or "recalcul" in text.lower()
            )
        ), (
            "La politique doit expliquer pourquoi on ne peut pas simplement "
            "hasher le secret TOTP (le serveur doit pouvoir recalculer l'OTP)."
        )

    def test_encryption_required_for_totp(self):
        text = AUTH_MFA_REF.read_text(encoding="utf-8")
        assert (
            "chiffrement" in text.lower()
            or "encryption" in text.lower()
            or "SEC-MFA-SECRET-ENCRYPTION-001" in text
        ), (
            "La politique doit mentionner que le secret TOTP nécessite un "
            "chiffrement applicatif (pas un simple hash)."
        )


class TestRecoveryCodesStorageDocumented:
    """Le stockage des codes de récupération est documenté séparément."""

    def test_recovery_codes_mentioned(self):
        text = AUTH_MFA_REF.read_text(encoding="utf-8")
        assert (
            "codes de récupération" in text.lower()
            or "recovery" in text.lower()
            or "récupération" in text.lower()
        ), (
            "La politique doit couvrir les codes de récupération séparément "
            "des secrets TOTP."
        )

    def test_recovery_codes_are_hashed(self):
        text = AUTH_MFA_REF.read_text(encoding="utf-8")
        assert (
            "hashé" in text.lower()
            or "hash" in text.lower()
            or "hash_recovery_code" in text
        ), (
            "La politique doit mentionner que les codes de récupération sont "
            "hashés (et non stockés en clair)."
        )


class TestNoUnqualifiedProductionReadyClaim:
    """Aucune affirmation non qualifiée de 'production-ready' pour MFA."""

    def test_no_mfa_production_ready_claim(self):
        text = AUTH_MFA_REF.read_text(encoding="utf-8")
        lines = text.splitlines()
        for i, line in enumerate(lines, start=1):
            line_lower = line.lower()
            # Détecter les affirmations positives non qualifiées
            if any(phrase in line_lower for phrase in [
                "mfa est production-ready",
                "mfa prêt pour la production",
                "totp secret stored securely by default",
                "secret totp sécurisé par défaut",
                "mfa is production-ready",
                "mfa ready for production",
            ]):
                raise AssertionError(
                    f"Affirmation production-ready non qualifiée détectée "
                    f"(ligne {i}) : {line.strip()!r}"
                )


class TestMfaRemainsOptIn:
    """MFA reste opt-in (Beta, hors [all] par choix de sécurité explicite)."""

    def test_mfa_beta_in_pyproject(self):
        text = MFA_PYPROJECT.read_text(encoding="utf-8")
        assert "Development Status :: 4 - Beta" in text, (
            "forge-mvc-mfa est 'Development Status :: 4 - Beta' (tous les opt-ins en Beta)."
        )

    def test_pyotp_not_in_core_dependencies(self):
        text = ROOT_PYPROJECT.read_text(encoding="utf-8")
        data = tomllib.loads(text)
        core_deps = data.get("project", {}).get("dependencies", [])
        for dep in core_deps:
            assert "pyotp" not in dep.lower(), (
                f"pyotp est dans les dépendances runtime du core : {dep!r}. "
                f"pyotp doit rester une dépendance de forge-mvc-mfa uniquement "
                f"(ADR-004)."
            )

    def test_forge_mvc_mfa_not_imported_from_core(self):
        offenders = []
        for py_file in CORE_DIR.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            if "forge_mvc_mfa" in text or "from forge_mvc_mfa" in text:
                offenders.append(str(py_file.relative_to(PROJECT_ROOT)))
        assert not offenders, (
            f"core/ importe forge_mvc_mfa (ADR-004 interdit) : {offenders}"
        )

    def test_mfa_excluded_from_all_extra(self):
        data = tomllib.loads(ROOT_PYPROJECT.read_text(encoding="utf-8"))
        all_deps = data.get("project", {}).get("optional-dependencies", {}).get("all", [])
        for dep in all_deps:
            assert "forge-mvc-mfa" not in dep, (
                f"forge-mvc-mfa est dans l'extra [all] : {dep!r}. "
                f"Activer MFA est un choix de sécurité explicite ; il reste hors de forge-mvc[all]."
            )


class TestEncryptionTicketReferenced:
    """Le ticket de chiffrement SEC-MFA-SECRET-ENCRYPTION-001 est référencé."""

    def test_encryption_ticket_in_auth_mfa_ref(self):
        text = AUTH_MFA_REF.read_text(encoding="utf-8")
        assert "SEC-MFA-SECRET-ENCRYPTION-001" in text, (
            "docs/reference/auth-mfa.md doit référencer SEC-MFA-SECRET-ENCRYPTION-001 "
            "comme ticket planifié pour le chiffrement des secrets TOTP."
        )

    def test_storage_policy_ticket_referenced(self):
        text = AUTH_MFA_REF.read_text(encoding="utf-8")
        assert "MFA-SECRET-STORAGE-POLICY-001" in text, (
            "docs/reference/auth-mfa.md doit référencer MFA-SECRET-STORAGE-POLICY-001 "
            "comme ticket livré (politique de stockage documentée)."
        )
