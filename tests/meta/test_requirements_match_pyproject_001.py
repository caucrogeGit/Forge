"""Garde-fou DEPS-REQUIREMENTS-JSONSCHEMA-001.

``pyproject.toml`` (``[project.dependencies]``) est la source de vérité du
runtime ``forge-mvc``. ``requirements.txt`` doit rester aligné : toute
dépendance runtime déclarée dans le pyproject doit y figurer, sinon une
installation via ``pip install -r requirements.txt`` produit un
environnement incomplet (ici ``jsonschema``, requis par les commandes
``schema:*`` / ``entity:validate``).

Ce test compare les deux par **nom de paquet normalisé** (PEP 503), sans
contraindre l'identité des specifiers de version.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
PYPROJECT = PROJECT_ROOT / "pyproject.toml"
REQUIREMENTS = PROJECT_ROOT / "requirements.txt"

_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*")


def _normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _requirement_name(line: str) -> str | None:
    line = line.split("#", 1)[0].strip()
    if not line or line.startswith("-"):
        return None
    match = _NAME_RE.match(line)
    return _normalize(match.group(0)) if match else None


def _pyproject_runtime_deps() -> set[str]:
    with PYPROJECT.open("rb") as fh:
        data = tomllib.load(fh)
    deps = data["project"]["dependencies"]
    return {_requirement_name(d) for d in deps} - {None}


def _requirements_names() -> set[str]:
    names = set()
    for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        name = _requirement_name(line)
        if name:
            names.add(name)
    return names


class TestRequirementsAlignment:
    def test_jsonschema_present(self):
        assert "jsonschema" in _requirements_names(), (
            "requirements.txt doit lister jsonschema (dépendance runtime "
            "déclarée dans pyproject.toml et requise par schema:*)."
        )

    def test_every_runtime_dep_in_requirements(self):
        missing = _pyproject_runtime_deps() - _requirements_names()
        assert not missing, (
            "Dépendances runtime présentes dans pyproject.toml mais "
            f"absentes de requirements.txt : {sorted(missing)}"
        )
