"""Tests de cohérence des métadonnées projet."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

import core
import pytest

pytestmark = pytest.mark.meta

_VERSION = __import__("tomllib").loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
_VERSION_SEMVER = __import__("re").sub(r"(\d+\.\d+\.\d+)b(\d+)$", r"\1-beta.\2", _VERSION)


def test_package_json_author_is_current():
    package_json = Path("package.json")
    data = json.loads(package_json.read_text(encoding="utf-8"))

    assert data["author"] == "Roger Lequette"


def test_pyproject_version_is_current():
    data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert data["project"]["version"] == _VERSION


def test_versions_actives_sont_alignees():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    forge_py = Path("forge.py").read_text(encoding="utf-8")
    package_json = json.loads(Path("package.json").read_text(encoding="utf-8"))

    assert pyproject["project"]["version"] == _VERSION
    assert re.search(rf'_FORGE_VERSION\s*=\s*"{re.escape(_VERSION)}"', forge_py)
    assert core.__version__ == _VERSION
    assert package_json["version"] == _VERSION_SEMVER
