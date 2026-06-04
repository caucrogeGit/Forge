"""Tests PACKAGES-OPTIN-INSTALL-001 : politique de publication des packages opt-in.

Apres MFA-PYPI-READY-001 :
- forge-mvc-mfa est requalifié Alpha, 'Private :: Do Not Upload' retiré ;
- forge-mvc-media est en statut Alpha (MEDIA-PYPI-READY-002) ;
- forge-mvc-rbac, forge-mvc-workflow, forge-mvc-stats sont prepares pour publication
  (Private :: Do Not Upload retire) mais aucun n'est encore stable.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

ROOT = Path(__file__).resolve().parents[2]

_ALPHA_PREPARED = [
    "forge-mvc-mfa",
]

_ALL_OPTIN_PACKAGES = [
    "forge-mvc-mfa",
    "forge-mvc-rbac",
    "forge-mvc-workflow",
    "forge-mvc-stats",
]


@pytest.mark.parametrize("package", _ALPHA_PREPARED)
class TestAlphaPreparedClassifier:

    def test_no_private_classifier(self, package: str):
        """forge-mvc-mfa et forge-mvc-media n'ont pas 'Private :: Do Not Upload' (requalifiés Alpha)."""
        pyproject_path = ROOT / "packages" / package / "pyproject.toml"
        assert pyproject_path.exists(), f"packages/{package}/pyproject.toml introuvable"
        data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        classifiers = data["project"]["classifiers"]
        assert not any("Private :: Do Not Upload" in c for c in classifiers), (
            f"{package} : classifier 'Private :: Do Not Upload' toujours présent — "
            f"ce package a été requalifié Alpha (MEDIA-PYPI-READY-002 / MFA-PYPI-READY-001)"
        )

    def test_alpha_or_above_status(self, package: str):
        """forge-mvc-mfa et forge-mvc-media sont en statut Alpha minimum."""
        pyproject_path = ROOT / "packages" / package / "pyproject.toml"
        data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        classifiers = data["project"]["classifiers"]
        dev_statuses = [c for c in classifiers if "Development Status" in c]
        assert dev_statuses, f"{package} n'a pas de classifier Development Status"
        status = dev_statuses[0]
        assert "Alpha" in status or "Beta" in status, (
            f"{package} : statut {status!r} — attendu Alpha minimum"
        )


@pytest.mark.parametrize("package", _ALL_OPTIN_PACKAGES)
class TestOptInPackagesDevelopmentStatus:

    def test_development_status_not_stable(self, package: str):
        """Les packages opt-in ne doivent pas être marqués Production/Stable."""
        pyproject_path = ROOT / "packages" / package / "pyproject.toml"
        data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        classifiers = data["project"]["classifiers"]
        assert not any("5 - Production/Stable" in c for c in classifiers), (
            f"{package} est marqué Production/Stable — statut réservé après 1.0.0-rc1"
        )
