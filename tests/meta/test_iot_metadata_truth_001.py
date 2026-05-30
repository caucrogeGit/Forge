"""Garde-fou IOT-PYPI-TRUTH-001.

Le module ``forge-mvc-iot`` est implémenté de bout en bout (subscriber
MQTT via ``paho-mqtt``, stockage ``iot_events``, API HTTP JSON, commandes
CLI ``forge iot:*``). Avant ce ticket, plusieurs surfaces de métadonnées
le décrivaient encore comme un « squelette initial sans implémentation » :

- ``packages/forge-mvc-iot/pyproject.toml`` (champ ``description``,
  publié tel quel sur PyPI) ;
- les docstrings des sous-packages ``mqtt`` et ``diagnostics``.

Ce garde-fou empêche la réapparition de ces mentions mensongères et
vérifie que la description publique reflète le module réel (charte v2,
règle A « retirer la cause », règle D « les tests testent le code »).
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
IOT_PKG_DIR = PROJECT_ROOT / "packages" / "forge-mvc-iot"
IOT_PYPROJECT = IOT_PKG_DIR / "pyproject.toml"
IOT_PYTHON_PKG = IOT_PKG_DIR / "forge_mvc_iot"

_FORBIDDEN_FRAGMENTS = (
    "squelette initial",
    "sans implémentation",
    "squelette vide",
    "aucune logique",
    "aucune commande cli",
    "aucune dépendance",
)


def _description() -> str:
    with IOT_PYPROJECT.open("rb") as fh:
        data = tomllib.load(fh)
    return data["project"]["description"]


class TestPyprojectDescription:
    def test_description_not_skeleton(self):
        lowered = _description().lower()
        offenders = [f for f in _FORBIDDEN_FRAGMENTS if f in lowered]
        assert not offenders, (
            "pyproject.description décrit encore forge-mvc-iot comme un "
            f"squelette vide (publié sur PyPI) : {offenders}"
        )

    def test_description_lists_real_capabilities(self):
        lowered = _description().lower()
        for token in ("mqtt", "http", "cli"):
            assert token in lowered, (
                f"pyproject.description doit mentionner la capacité '{token}'"
            )


class TestSubpackageDocstrings:
    @pytest.mark.parametrize("subpkg", ["mqtt", "diagnostics"])
    def test_docstring_not_skeleton(self, subpkg):
        text = (IOT_PYTHON_PKG / subpkg / "__init__.py").read_text(
            encoding="utf-8"
        )
        lowered = text.lower()
        offenders = [f for f in _FORBIDDEN_FRAGMENTS if f in lowered]
        assert not offenders, (
            f"La docstring de forge_mvc_iot/{subpkg}/__init__.py affirme "
            f"encore un état squelette : {offenders}"
        )
