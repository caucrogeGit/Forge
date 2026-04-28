"""Tests de cohérence des métadonnées projet."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

import core


def test_package_json_author_is_current():
    package_json = Path("package.json")
    data = json.loads(package_json.read_text(encoding="utf-8"))

    assert data["author"] == "Roger Cauchon"


def test_pyproject_version_is_1_0_1():
    data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert data["project"]["version"] == "1.0.1"


def test_versions_actives_sont_alignees_sur_1_0_1():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    forge_py = Path("forge.py").read_text(encoding="utf-8")
    package_json = json.loads(Path("package.json").read_text(encoding="utf-8"))

    assert pyproject["project"]["version"] == "1.0.1"
    assert re.search(r'_FORGE_VERSION\s*=\s*"1\.0\.1"', forge_py)
    assert core.__version__ == "1.0.1"
    assert package_json["version"] == "1.0.1"
