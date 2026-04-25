"""Tests de cohérence des métadonnées projet."""

from __future__ import annotations

import json
from pathlib import Path


def test_package_json_author_is_current():
    package_json = Path("package.json")
    data = json.loads(package_json.read_text(encoding="utf-8"))

    assert data["author"] == "Roger Cauchon"
