"""Garde-fou TEST-LAYERS-DOC-001 : la carte des couches de test reste exacte.

Point 5 de l'audit d'industrialisation (« savoir rapidement quelle couche est
cassée »). La carte des couches vit dans docs/contributing/conventions.md
(pattern B.7). Ce garde-fou la relie à la source unique (`pytest.ini`) pour
qu'elle ne dérive pas :

- chaque marqueur déclaré dans `pytest.ini` est documenté dans la carte ;
- les commandes de sélection par couche y figurent.
"""
from __future__ import annotations

import configparser
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYTEST_INI = PROJECT_ROOT / "pytest.ini"
CONVENTIONS = PROJECT_ROOT / "docs" / "contributing" / "conventions.md"


def _declared_markers() -> list[str]:
    parser = configparser.ConfigParser()
    parser.read(PYTEST_INI, encoding="utf-8")
    raw = parser.get("pytest", "markers")
    names: list[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r"([a-z_]+)\s*:", line)
        if m:
            names.append(m.group(1))
    return names


def test_carte_des_couches_presente():
    content = CONVENTIONS.read_text(encoding="utf-8")
    assert "Couches de test" in content, (
        "conventions.md doit documenter la carte des couches de test (pattern B.7)."
    )


@pytest.mark.parametrize("marker", _declared_markers())
def test_marqueur_documente(marker: str):
    content = CONVENTIONS.read_text(encoding="utf-8")
    assert f"`{marker}`" in content, (
        f"Le marqueur pytest « {marker} » (déclaré dans pytest.ini) doit être "
        "documenté dans la carte des couches de conventions.md."
    )


@pytest.mark.parametrize("command", [
    "pytest tests/meta",
    "pytest -m db",
    "pytest tests/release",
    "pytest packages",
])
def test_commande_de_selection_documentee(command: str):
    content = CONVENTIONS.read_text(encoding="utf-8")
    assert command in content, (
        f"La commande de sélection de couche « {command} » doit figurer dans "
        "la carte des couches de conventions.md."
    )
