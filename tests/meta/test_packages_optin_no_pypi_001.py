"""Tests PACKAGES-OPTIN-INSTALL-001 : les packages opt-in ne doivent pas être publiés sur PyPI."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

ROOT = Path(__file__).resolve().parents[2]

_OPTIN_PACKAGES = [
    "forge-mvc-mfa",
    "forge-mvc-rbac",
    "forge-mvc-workflow",
    "forge-mvc-stats",
    "forge-mvc-media",
]


@pytest.mark.parametrize("package", _OPTIN_PACKAGES)
class TestOptInPackagesPrivateClassifier:

    def test_private_classifier_present(self, package: str):
        """Chaque package opt-in déclare 'Private :: Do Not Upload' dans ses classifiers."""
        pyproject_path = ROOT / "packages" / package / "pyproject.toml"
        assert pyproject_path.exists(), f"packages/{package}/pyproject.toml introuvable"
        data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        classifiers = data["project"]["classifiers"]
        assert any("Private :: Do Not Upload" in c for c in classifiers), (
            f"{package} : classifier 'Private :: Do Not Upload' absent — "
            f"risque de publication accidentelle sur PyPI"
        )

    def test_development_status_not_stable(self, package: str):
        """Les packages opt-in ne doivent pas être marqués Production/Stable."""
        pyproject_path = ROOT / "packages" / package / "pyproject.toml"
        data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        classifiers = data["project"]["classifiers"]
        assert not any("5 - Production/Stable" in c for c in classifiers), (
            f"{package} est marqué Production/Stable — statut réservé après 1.0.0-rc1"
        )
