"""Garde-fou RELEASE-VALIDATION-GIT-001.

Vérifie :
- le fichier outils tools/release-validate.sh existe et est exécutable ;
- storage/logs/ est couvert par .gitignore ;
- aucun fichier aberrant du type '=X.Y.Z' n'existe à la racine ;
- le script référence les 3 fichiers de version canoniques ;
- docs/release/release-policy.md référence tools/release-validate.sh.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent


class TestReleaseValidateScript:

    def test_script_exists(self):
        assert (PROJECT_ROOT / "tools" / "release-validate.sh").is_file()

    def test_script_is_executable(self):
        path = PROJECT_ROOT / "tools" / "release-validate.sh"
        assert os.access(path, os.X_OK), "tools/release-validate.sh doit être exécutable"

    def test_script_checks_pyproject(self):
        text = (PROJECT_ROOT / "tools" / "release-validate.sh").read_text()
        assert "pyproject.toml" in text

    def test_script_checks_core_init(self):
        text = (PROJECT_ROOT / "tools" / "release-validate.sh").read_text()
        assert "core/__init__.py" in text

    def test_script_checks_forge_py(self):
        text = (PROJECT_ROOT / "tools" / "release-validate.sh").read_text()
        assert "forge.py" in text

    def test_script_checks_changelog(self):
        text = (PROJECT_ROOT / "tools" / "release-validate.sh").read_text()
        assert "CHANGELOG" in text

    def test_script_checks_pytest(self):
        text = (PROJECT_ROOT / "tools" / "release-validate.sh").read_text()
        assert "pytest" in text

    def test_script_checks_ruff(self):
        text = (PROJECT_ROOT / "tools" / "release-validate.sh").read_text()
        assert "ruff" in text

    def test_script_checks_mkdocs(self):
        text = (PROJECT_ROOT / "tools" / "release-validate.sh").read_text()
        assert "mkdocs" in text

    def test_script_exits_nonzero_on_fail(self):
        text = (PROJECT_ROOT / "tools" / "release-validate.sh").read_text()
        assert "exit 1" in text


class TestGitignoreCoversLogs:

    def test_storage_logs_in_gitignore(self):
        gitignore = (PROJECT_ROOT / ".gitignore").read_text()
        assert "storage/logs/" in gitignore or "storage/logs/*" in gitignore, (
            ".gitignore doit couvrir storage/logs/ (logs runtime non versionnés)"
        )


class TestNoArtifactFilesAtRoot:
    """Fichiers parasites créés par des shell redirects sans guillemets (ex: =3.12)."""

    def test_no_pip_version_constraint_artifacts(self):
        artifacts = list(PROJECT_ROOT.glob("=*."))
        artifacts += [p for p in PROJECT_ROOT.iterdir()
                      if p.name.startswith("=") and p.is_file()]
        assert not artifacts, (
            f"Fichiers parasites '=X.Y.Z' à la racine : {artifacts}. "
            "Supprimer avec rm -f '=<version>'."
        )


class TestReleasePolicyDocumentsScript:

    def test_release_policy_references_script(self):
        text = (PROJECT_ROOT / "docs" / "release" / "release-policy.md").read_text()
        assert "tools/release-validate.sh" in text, (
            "docs/release/release-policy.md doit référencer tools/release-validate.sh"
        )
