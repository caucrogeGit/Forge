"""Tests OPTIN-LICENSE-001 — chaque opt-in embarque le texte de licence.

Forge est diffusé sous licence propriétaire (« tous droits réservés »).
Publier un paquet sur PyPI public sans le texte de la licence est une
incohérence juridique : l'utilisateur ne reçoit pas les conditions d'usage.
setuptools (>=77) embarque automatiquement tout fichier `LICENSE*` présent à
la racine du paquet (glob license-files par défaut), donc la présence du
fichier suffit à l'inclure dans le wheel/sdist.
"""

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

ROOT = Path(__file__).resolve().parent.parent.parent
PACKAGES_DIR = ROOT / "packages"
ROOT_LICENSE = ROOT / "LICENSE"

_OPTIN_DIRS = sorted(
    p for p in PACKAGES_DIR.iterdir()
    if (p / "pyproject.toml").is_file()
    # forge-mvc-testing : infra de test dev-only, non distribuée (ADR-041).
    and p.name != "forge-mvc-testing"
)


def test_root_license_exists():
    assert ROOT_LICENSE.is_file(), "LICENSE racine absent"


@pytest.mark.parametrize("pkg_dir", _OPTIN_DIRS, ids=lambda p: p.name)
def test_optin_has_license(pkg_dir):
    license_file = pkg_dir / "LICENSE"
    assert license_file.is_file(), (
        f"{pkg_dir.name} : LICENSE absent — un opt-in publié sur PyPI doit "
        "embarquer le texte de licence."
    )


@pytest.mark.parametrize("pkg_dir", _OPTIN_DIRS, ids=lambda p: p.name)
def test_optin_license_matches_root(pkg_dir):
    license_file = pkg_dir / "LICENSE"
    assert license_file.read_text(encoding="utf-8") == ROOT_LICENSE.read_text(
        encoding="utf-8"
    ), f"{pkg_dir.name} : LICENSE diffère du LICENSE racine"
