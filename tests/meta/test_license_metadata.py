"""Tests LEGAL-LICENSE-001 — coherence de la licence Forge."""

from __future__ import annotations

import tomllib
from pathlib import Path
import pytest

pytestmark = pytest.mark.meta


_LICENSE = Path("LICENSE")
_PYPROJECT = Path("pyproject.toml")
_README = Path("README.md")
_DOCS_LICENCE = Path("docs/philosophy/licence.md")


def _pyproject() -> dict:
    return tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# pyproject.toml
# ---------------------------------------------------------------------------


def test_pyproject_license_is_not_mit():
    data = _pyproject()
    assert data["project"]["license"] != "MIT"


def test_pyproject_license_is_proprietary():
    data = _pyproject()
    assert data["project"]["license"] == "LicenseRef-Forge-Proprietary"


def test_pyproject_license_files_declared():
    data = _pyproject()
    assert "LICENSE" in data["project"]["license-files"]


def test_pyproject_classifiers_do_not_contain_legacy_license_classifier():
    data = _pyproject()
    classifiers = data["project"]["classifiers"]
    assert "License :: Other/Proprietary License" not in classifiers


def test_pyproject_classifiers_do_not_contain_mit():
    data = _pyproject()
    classifiers = data["project"]["classifiers"]
    assert not any("MIT" in c for c in classifiers)


# ---------------------------------------------------------------------------
# LICENSE
# ---------------------------------------------------------------------------


def test_license_exists():
    assert _LICENSE.exists()


def test_license_mentions_professional_usage():
    text = _LICENSE.read_text(encoding="utf-8")
    assert "professionnel" in text.lower()


def test_license_mentions_written_authorization():
    text = _LICENSE.read_text(encoding="utf-8")
    assert "autorisation écrite" in text


def test_license_mentions_copyright():
    text = _LICENSE.read_text(encoding="utf-8")
    assert "Roger Lequette" in text


def test_license_does_not_say_mit():
    text = _LICENSE.read_text(encoding="utf-8")
    assert "MIT License" not in text
    assert "MIT licence" not in text


def test_license_mentions_commercial_restriction():
    text = _LICENSE.read_text(encoding="utf-8")
    assert "commercial" in text.lower()


# ---------------------------------------------------------------------------
# README.md
# ---------------------------------------------------------------------------


def test_readme_mentions_proprietary_license():
    text = _README.read_text(encoding="utf-8")
    assert "propriétaire" in text.lower()


def test_readme_does_not_claim_open_source():
    text = _README.read_text(encoding="utf-8")
    assert "open source" not in text.lower() or "n'est pas open source" in text.lower()


def test_readme_licence_section_forbids_professional_use():
    text = _README.read_text(encoding="utf-8")
    assert "professionnel" in text.lower()


# ---------------------------------------------------------------------------
# docs/philosophy/licence.md
# ---------------------------------------------------------------------------


def test_docs_licence_exists():
    assert _DOCS_LICENCE.exists()


def test_docs_licence_mentions_professional_restriction():
    text = _DOCS_LICENCE.read_text(encoding="utf-8")
    assert "professionnel" in text.lower()


def test_docs_licence_mentions_written_authorization():
    text = _DOCS_LICENCE.read_text(encoding="utf-8")
    assert "autorisation écrite" in text


def test_docs_licence_mentions_not_open_source():
    text = _DOCS_LICENCE.read_text(encoding="utf-8")
    assert "pas un logiciel open source" in text or "n'est pas open source" in text.lower()
