"""Garde-fou MFA-PRODUCTION-DECISION-001.

Vérifie que :
1. forge-mvc-mfa n'est PAS dans l'extra [all] (décision option A — 3.0.2)
2. forge-mvc-mfa reste disponible via [mfa] (opt-in conscient)
3. Le README MFA documente clairement le statut Pre-Alpha

Origine : trois audits convergents — MFA est marqué Pre-Alpha mais inclus
dans forge-mvc[all]. Contradiction avec la charte principe 7 (sécuriser par
défaut) et principe 10 (API publique = contrat de complétude). Décision :
retirer MFA de [all] pour 3.0.2, réintégrer après SEC-MFA-SECRET-ENCRYPTION-001.

Note T2b : le véhicule packages/forge-mvc/pyproject.toml a été supprimé.
Un seul pyproject.toml (racine) publie forge-mvc.
"""
from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
ROOT_PYPROJECT = PROJECT_ROOT / "pyproject.toml"
MFA_README = PROJECT_ROOT / "packages" / "forge-mvc-mfa" / "README.md"
MFA_PYPROJECT = PROJECT_ROOT / "packages" / "forge-mvc-mfa" / "pyproject.toml"


def _read_extras(pyproject_path: Path) -> dict[str, list[str]]:
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    return data.get("project", {}).get("optional-dependencies", {})


class TestMfaNotInAll:
    """forge-mvc-mfa n'est PAS dans l'extra [all]."""

    def test_mfa_excluded_from_root_all(self):
        extras = _read_extras(ROOT_PYPROJECT)
        all_deps = extras.get("all", [])
        for dep in all_deps:
            assert "forge-mvc-mfa" not in dep, (
                f"forge-mvc-mfa est dans [all] : '{dep}'. "
                f"Décision T3 (option A) : MFA est Pre-Alpha et ne doit pas "
                f"être dans le metapackage all."
            )


class TestMfaAvailableViaExplicitExtra:
    """forge-mvc-mfa est en mode source-only (extras PyPI temporairement désactivés).

    Les extras [mfa], [rbac], [workflow], [stats], [all] ont été retirés du
    pyproject.toml racine en 1.0.0b1 car les modules opt-in ne sont pas encore
    sur PyPI. Réintroduction prévue dans une version ultérieure (OPTIN-PYPI-PUBLISH-001).
    """

    def test_mfa_extra_intentionally_absent(self):
        """L'extra [mfa] doit rester absent — forge-mvc-mfa n'est pas publiable (Pre-Alpha)."""
        extras = _read_extras(ROOT_PYPROJECT)
        assert "mfa" not in extras, (
            "L'extra [mfa] est présent dans pyproject.toml — il doit être absent "
            "(forge-mvc-mfa est Pre-Alpha, SEC-MFA-SECRET-ENCRYPTION-001 requis). "
            "Voir OPTIN-PYPI-PUBLISH-001."
        )

    def test_optin_publish_ticket_documented_in_pyproject(self):
        """La suppression des extras est tracée dans pyproject.toml."""
        text = ROOT_PYPROJECT.read_text(encoding="utf-8")
        assert "OPTIN-PYPI-PUBLISH-001" in text, (
            "pyproject.toml doit mentionner OPTIN-PYPI-PUBLISH-001 pour tracer "
            "la réintroduction prévue des extras en 3.1."
        )


class TestMfaStatusDocumented:
    """Le statut Pre-Alpha de MFA est documenté visiblement."""

    def test_mfa_pyproject_is_alpha(self):
        text = MFA_PYPROJECT.read_text(encoding="utf-8")
        assert "Development Status :: 3 - Alpha" in text, (
            "Le classifier MFA doit être 'Development Status :: 3 - Alpha' "
            "depuis MFA-PYPI-READY-001."
        )

    def test_mfa_pyproject_no_private_do_not_upload(self):
        text = MFA_PYPROJECT.read_text(encoding="utf-8")
        assert "Private :: Do Not Upload" not in text, (
            "forge-mvc-mfa n'a plus 'Private :: Do Not Upload' depuis MFA-PYPI-READY-001."
        )

    def test_mfa_readme_documents_status(self):
        text = MFA_README.read_text(encoding="utf-8")
        assert "Alpha" in text, (
            "Le README MFA doit afficher le statut 'Alpha' clairement."
        )

    def test_mfa_readme_documents_pypi_roadmap(self):
        text = MFA_README.read_text(encoding="utf-8")
        assert "MFA-PYPI-READY-001" in text, (
            "Le README MFA doit mentionner MFA-PYPI-READY-001 "
            "(ticket de requalification Beta et publication PyPI de forge-mvc-mfa)."
        )
