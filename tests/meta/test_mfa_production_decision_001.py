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
    """forge-mvc-mfa reste hors des extras du pyproject racine.

    Les extras publiables [rbac]/[workflow]/[stats]/[all] sont présents et
    pointent vers les opt-ins publiés sur PyPI (politique unifiée
    OPTIN-DEPS-PIN-B13-001). forge-mvc-mfa en est volontairement exclu (Alpha)
    — cf. ``test_mfa_excluded_from_root_all``.
    """

    def test_mfa_extra_intentionally_absent(self):
        """L'extra [mfa] doit rester absent — forge-mvc-mfa est exclu des extras (Alpha)."""
        extras = _read_extras(ROOT_PYPROJECT)
        assert "mfa" not in extras, (
            "L'extra [mfa] est présent dans pyproject.toml — il doit être absent "
            "(forge-mvc-mfa est Alpha, exclu des extras et de [all])."
        )

    def test_publishable_extras_present(self):
        """Les extras publiables (rbac/workflow/stats/all) sont déclarés —
        réintroduction effectuée, les opt-ins sont publiés sur PyPI."""
        extras = _read_extras(ROOT_PYPROJECT)
        for name in ("rbac", "workflow", "stats", "all"):
            assert name in extras, (
                f"L'extra [{name}] doit être déclaré dans pyproject.toml racine."
            )


class TestMfaStatusDocumented:
    """Le statut Beta de MFA est documenté visiblement."""

    def test_mfa_pyproject_is_beta(self):
        text = MFA_PYPROJECT.read_text(encoding="utf-8")
        assert "Development Status :: 4 - Beta" in text, (
            "Le classifier MFA doit être 'Development Status :: 4 - Beta'."
        )

    def test_mfa_pyproject_no_private_do_not_upload(self):
        text = MFA_PYPROJECT.read_text(encoding="utf-8")
        assert "Private :: Do Not Upload" not in text, (
            "forge-mvc-mfa n'a plus 'Private :: Do Not Upload' depuis MFA-PYPI-READY-001."
        )

    def test_mfa_readme_documents_status(self):
        """Le README dit d'où vient sa version.

        Ce contrôle exigeait le mot « Beta »
        (`OPTINS-MATURITY-FOLLOWS-CORE-001`). Un opt-in n'a plus de maturité
        propre : l'exiger obligerait à réafficher un stade périmé pour
        satisfaire un test, ce que la règle D interdit.
        """
        text = MFA_README.read_text(encoding="utf-8")
        assert "suit la version du cœur" in text, (
            "Le README MFA doit dire que le paquet suit la version du cœur."
        )

    def test_mfa_readme_documents_pypi_roadmap(self):
        text = MFA_README.read_text(encoding="utf-8")
        assert "MFA-PYPI-READY-001" in text, (
            "Le README MFA doit mentionner MFA-PYPI-READY-001 "
            "(ticket de requalification Beta et publication PyPI de forge-mvc-mfa)."
        )
