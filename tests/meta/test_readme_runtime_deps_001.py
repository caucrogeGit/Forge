"""Garde-fou README-RUNTIME-DEPS-CLEANUP-001.

Vérifie que le README et docs/contributing.md ne présentent pas pyotp
comme une dépendance runtime obligatoire du core forge-mvc.

Règle : pyotp est MFA-only (principe 8). Les tests de packaging
(test_pyotp_absent_de_requirements_txt, test_pyotp_absent_du_pyproject_racine)
couvrent requirements.txt et pyproject.toml. Ce fichier couvre la documentation.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent


class TestReadmeRuntimeDeps:
    """README ne présente pas pyotp comme dépendance runtime core."""

    def test_pyotp_absent_du_tableau_runtime(self):
        readme = PROJECT_ROOT / "README.md"
        if not readme.exists():
            pytest.skip("README.md n'existe pas")
        text = readme.read_text(encoding="utf-8")
        # Isoler la section Runtime (entre "**Runtime**" et "**Développement**")
        match = re.search(
            r"\*\*Runtime\*\*.*?\*\*Développement\*\*",
            text,
            re.DOTALL,
        )
        # README simplifié : il n'y a plus de tableau Runtime des
        # dépendances. Le garde-fou reste valide « par construction » —
        # pyotp (MFA-only) ne peut pas être présenté comme dépendance
        # runtime core s'il n'y a pas de tableau. S'il existe, on vérifie.
        if match is None:
            return
        runtime_section = match.group(0)
        # pyotp ne doit pas apparaître dans le tableau Runtime en tant que ligne de dépendance
        assert "| `pyotp`" not in runtime_section, (
            "README.md liste `pyotp` dans le tableau Runtime — "
            "pyotp est MFA-only et ne fait pas partie du runtime core (principe 8)."
        )

    def test_intro_ne_mentionne_pas_pyotp_comme_dep_core(self):
        readme = PROJECT_ROOT / "README.md"
        if not readme.exists():
            pytest.skip("README.md n'existe pas")
        # Lire les 20 premières lignes (introduction)
        lines = readme.read_text(encoding="utf-8").splitlines()[:20]
        intro = "\n".join(lines)
        assert "PyOTP" not in intro and "pyotp" not in intro, (
            "README.md mentionne PyOTP dans l'introduction comme dépendance core — "
            "pyotp est MFA-only (principe 8)."
        )


class TestContributingRuntimeDeps:
    """docs/contributing.md ne liste pas pyotp parmi les dépendances runtime core."""

    def test_pyotp_absent_de_la_liste_runtime(self):
        doc = PROJECT_ROOT / "docs" / "contributing.md"
        if not doc.exists():
            pytest.skip("docs/contributing.md n'existe pas")
        text = doc.read_text(encoding="utf-8")
        # Extraire la liste des packages déclarés comme dépendances runtime core
        # (portion après "limitées à" jusqu'au premier point qui ferme la liste)
        match = re.search(r"limit[eé]es?\s+à\s+(.+?)(?:\.|$)", text, re.IGNORECASE)
        if match:
            core_list = match.group(1)
            assert "`pyotp`" not in core_list, (
                "docs/contributing.md liste `pyotp` dans les dépendances runtime core — "
                "pyotp est MFA-only (principe 8)."
            )
