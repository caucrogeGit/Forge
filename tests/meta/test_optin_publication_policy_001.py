"""Garde-fou OPTIN-PACKAGES-PUBLICATION-POLICY-001.

Vérifie que la politique officielle de publication des packages opt-in est
documentée dans docs/release/release-policy.md avec toutes les sections requises.

Règles vérifiées :
- La section "Politique de publication des opt-ins" existe.
- Les jalons beta.4 et beta.5 sont référencés.
- "publication coordonnée" est utilisé (pas "publication atomique").
- Les opt-ins publiables à beta.5 sont listés (rbac, workflow, stats).
- forge-mvc-mfa est explicitement non publié en série 1.0.
- pyotp n'est pas une dépendance runtime du core.
- Aucune affirmation active "pip install forge-mvc[mfa]".
"""
from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
RELEASE_POLICY = PROJECT_ROOT / "docs" / "release" / "release-policy.md"
ROOT_PYPROJECT = PROJECT_ROOT / "pyproject.toml"


class TestPolicySectionExists:
    """La section 'Politique de publication des opt-ins' existe."""

    def test_section_header_present(self):
        text = RELEASE_POLICY.read_text(encoding="utf-8")
        assert "Politique de publication des opt-ins" in text, (
            "docs/release/release-policy.md doit contenir une section "
            "'Politique de publication des opt-ins'."
        )

    def test_subsection_etat_actuel(self):
        text = RELEASE_POLICY.read_text(encoding="utf-8")
        assert "État actuel" in text or "Etat actuel" in text, (
            "La section politique doit inclure un sous-titre 'État actuel'."
        )

    def test_subsection_cas_particulier_mfa(self):
        text = RELEASE_POLICY.read_text(encoding="utf-8")
        assert "forge-mvc-mfa" in text, (
            "La section politique doit couvrir le cas particulier de forge-mvc-mfa."
        )

    def test_subsection_regles_interdiction(self):
        text = RELEASE_POLICY.read_text(encoding="utf-8")
        assert "interdit" in text.lower(), (
            "La section politique doit lister ce qui est interdit avant "
            "publication coordonnée."
        )

    def test_tickets_lies_present(self):
        text = RELEASE_POLICY.read_text(encoding="utf-8")
        assert "OPTIN-PACKAGES-PUBLICATION-POLICY-001" in text, (
            "docs/release/release-policy.md doit référencer OPTIN-PACKAGES-PUBLICATION-POLICY-001 "
            "comme ticket livré."
        )


class TestBetaMilestonesReferenced:
    """Les jalons beta.4 et beta.5 sont explicitement référencés."""

    def test_beta4_referenced(self):
        text = RELEASE_POLICY.read_text(encoding="utf-8")
        assert "beta.4" in text or "beta-4" in text or "beta.4" in text, (
            "docs/release/release-policy.md doit référencer le jalon beta.4 "
            "(limite où seul le core est publié)."
        )

    def test_beta5_referenced(self):
        text = RELEASE_POLICY.read_text(encoding="utf-8")
        assert "beta.5" in text or "beta-5" in text, (
            "docs/release/release-policy.md doit référencer le jalon beta.5 "
            "(publication coordonnée des opt-ins)."
        )


class TestPublicationCoordonnee:
    """Le terme 'publication coordonnée' est utilisé, pas 'publication atomique'."""

    def test_publication_coordonnee_used(self):
        text = RELEASE_POLICY.read_text(encoding="utf-8")
        assert "publication coordonnée" in text, (
            "docs/release/release-policy.md doit utiliser le terme "
            "'publication coordonnée' (pas 'publication atomique')."
        )

    def test_publication_atomique_absent(self):
        text = RELEASE_POLICY.read_text(encoding="utf-8")
        assert "publication atomique" not in text, (
            "docs/release/release-policy.md ne doit pas utiliser 'publication atomique' — "
            "le terme officiel est 'publication coordonnée'."
        )


class TestOptinsPubliablesListed:
    """Les opt-ins publiables à beta.5 sont explicitement listés."""

    def test_rbac_listed(self):
        text = RELEASE_POLICY.read_text(encoding="utf-8")
        assert "forge-mvc-rbac" in text, (
            "docs/release/release-policy.md doit lister forge-mvc-rbac comme opt-in "
            "publiable à beta.5."
        )

    def test_workflow_listed(self):
        text = RELEASE_POLICY.read_text(encoding="utf-8")
        assert "forge-mvc-workflow" in text, (
            "docs/release/release-policy.md doit lister forge-mvc-workflow comme opt-in "
            "publiable à beta.5."
        )

    def test_stats_listed(self):
        text = RELEASE_POLICY.read_text(encoding="utf-8")
        assert "forge-mvc-stats" in text, (
            "docs/release/release-policy.md doit lister forge-mvc-stats comme opt-in "
            "publiable à beta.5."
        )


class TestMfaNonPublieSerie1:
    """forge-mvc-mfa est explicitement non publié sur PyPI en série 1.0."""

    def test_mfa_not_published_in_1_0(self):
        text = RELEASE_POLICY.read_text(encoding="utf-8")
        assert (
            "forge-mvc-mfa" in text
            and (
                "non publié" in text
                or "Non publié" in text
                or "pas publié" in text
                or "n'est pas publié" in text
            )
        ), (
            "docs/release/release-policy.md doit expliciter que forge-mvc-mfa n'est "
            "pas publié sur PyPI en série 1.0."
        )

    def test_sec_mfa_encryption_referenced(self):
        text = RELEASE_POLICY.read_text(encoding="utf-8")
        assert "SEC-MFA-SECRET-ENCRYPTION-001" in text, (
            "docs/release/release-policy.md doit référencer SEC-MFA-SECRET-ENCRYPTION-001 "
            "comme prérequis à la publication de forge-mvc-mfa."
        )

    def test_mfa_excluded_from_all_extra_in_pyproject(self):
        data = tomllib.loads(ROOT_PYPROJECT.read_text(encoding="utf-8"))
        all_deps = (
            data.get("project", {})
            .get("optional-dependencies", {})
            .get("all", [])
        )
        for dep in all_deps:
            assert "forge-mvc-mfa" not in dep, (
                f"forge-mvc-mfa est dans l'extra [all] : {dep!r}. "
                f"MFA est Pre-Alpha et ne doit pas être dans forge-mvc[all]."
            )


class TestNoPyotpInCore:
    """pyotp n'est pas une dépendance runtime du core."""

    def test_pyotp_not_in_core_dependencies(self):
        data = tomllib.loads(ROOT_PYPROJECT.read_text(encoding="utf-8"))
        core_deps = data.get("project", {}).get("dependencies", [])
        for dep in core_deps:
            assert "pyotp" not in dep.lower(), (
                f"pyotp est dans les dépendances runtime du core : {dep!r}. "
                f"pyotp doit rester une dépendance de forge-mvc-mfa uniquement."
            )


class TestNoActiveMfaInstallClaim:
    """Aucune affirmation active de 'pip install forge-mvc[mfa]' dans la politique."""

    def test_no_pip_install_mfa_claim_in_policy(self):
        text = RELEASE_POLICY.read_text(encoding="utf-8")
        lines = text.splitlines()
        for i, line in enumerate(lines, start=1):
            if "pip install forge-mvc[mfa]" in line and not line.strip().startswith("#"):
                raise AssertionError(
                    f"Affirmation active 'pip install forge-mvc[mfa]' détectée "
                    f"(ligne {i}) dans docs/release/release-policy.md : {line.strip()!r}. "
                    f"forge-mvc[mfa] n'est pas disponible en série 1.0."
                )
