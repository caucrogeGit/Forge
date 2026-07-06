"""Garde-fou SMOKE-INSTALL-VIERGE-001 (volet rapide, hors réseau).

Tout paquet Forge épinglé dans le requirements.txt du squelette doit
correspondre à un paquet réellement livré par le monorepo, à la MÊME version.
Empêche `forge new` de pointer vers un paquet fantôme ou une version
incohérente, cause d'échec d'installation côté nouvel utilisateur.

Le smoke complet (build des wheels + venv vierge + forge new + installation
résolue via --find-links) est dans tools/smoke-install.sh ; ce test en est le
volet rapide et déterministe.
"""
from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SKELETON_REQ = PROJECT_ROOT / "skeleton" / "data" / "requirements.txt"
ROOT_PYPROJECT = PROJECT_ROOT / "pyproject.toml"

_PIN = re.compile(r"^(forge-mvc(?:-[a-z0-9-]+)?)==([^\s#]+)", re.MULTILINE)


def _version(pyproject: Path) -> str:
    return tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["version"]


def _skeleton_pins() -> list[tuple[str, str]]:
    return _PIN.findall(SKELETON_REQ.read_text(encoding="utf-8"))


def test_skeleton_pins_at_least_core():
    pins = dict(_skeleton_pins())
    assert "forge-mvc" in pins, (
        "Le requirements.txt du squelette doit épingler forge-mvc."
    )


@pytest.mark.parametrize("name,version", _skeleton_pins())
def test_pinned_forge_package_exists_and_matches(name: str, version: str):
    canonical = _version(ROOT_PYPROJECT)
    if name == "forge-mvc":
        pyproject = ROOT_PYPROJECT
    else:
        slug = name[len("forge-mvc-"):]
        pyproject = PROJECT_ROOT / "packages" / f"forge-mvc-{slug}" / "pyproject.toml"
        assert pyproject.is_file(), (
            f"Le squelette épingle '{name}=={version}' mais "
            f"packages/forge-mvc-{slug}/pyproject.toml est absent : "
            f"forge new pointerait vers un paquet non livré par le monorepo."
        )
    pkg_version = _version(pyproject)
    assert version == pkg_version, (
        f"Le squelette épingle '{name}=={version}' mais le paquet est en "
        f"version {pkg_version}. Le pin du squelette doit suivre la version "
        f"courante ({canonical})."
    )
