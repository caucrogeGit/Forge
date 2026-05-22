"""Tests PACKAGES-OPTIN-INSTALL-001 : politique de publication des packages opt-in.

Apres MEDIA-PYPI-READY-002 :
- forge-mvc-mfa reste non publiable (Private :: Do Not Upload maintenu — SEC-MFA-SECRET-ENCRYPTION-001) ;
- forge-mvc-media a été requalifié Alpha et préparé pour publication future (Private :: Do Not Upload retiré) ;
- forge-mvc-rbac, forge-mvc-workflow, forge-mvc-stats sont prepares pour publication
  (Private :: Do Not Upload retire) mais aucun n'est encore stable.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

ROOT = Path(__file__).resolve().parents[2]

_NON_PUBLISHABLE = [
    "forge-mvc-mfa",
]

_ALL_OPTIN_PACKAGES = [
    "forge-mvc-mfa",
    "forge-mvc-rbac",
    "forge-mvc-workflow",
    "forge-mvc-stats",
    "forge-mvc-media",
]


@pytest.mark.parametrize("package", _NON_PUBLISHABLE)
class TestNonPublishablePrivateClassifier:

    def test_private_classifier_present(self, package: str):
        """forge-mvc-mfa conserve 'Private :: Do Not Upload' (SEC-MFA-SECRET-ENCRYPTION-001)."""
        pyproject_path = ROOT / "packages" / package / "pyproject.toml"
        assert pyproject_path.exists(), f"packages/{package}/pyproject.toml introuvable"
        data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        classifiers = data["project"]["classifiers"]
        assert any("Private :: Do Not Upload" in c for c in classifiers), (
            f"{package} : classifier 'Private :: Do Not Upload' absent — "
            f"ce package ne doit pas etre publie (OPTIN-PYPI-PUBLISH-PREPARE-001)"
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
