"""Garde-fous PYTHON-312-CONSISTENCY-001 : cohérence Python 3.12 dans tous les fichiers actifs."""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent


class TestPython312Consistency:
    """Aucune référence active à Python 3.11 en dehors des mentions historiques légitimes.

    Le projet exige Python 3.12+ (ADR-006, pyproject.toml). Toute mention de 3.11
    comme exigence ou version supportée dans la CI/doc/CLI active est une incohérence.
    Mentions tolérées : docs/history/, CHANGELOG.md, docs/history/audits/ (rapports historiques).
    """

    ACTIVE_FILES = [
        Path("README.md"),
        Path("docs/release/compatibility.md"),
        Path("docs/release/release-and-compatibility.md"),
        Path("cli/project/doctor.py"),
        Path("packages/forge-mvc-deploy/forge_mvc_deploy/cli/deploy.py"),
        Path(".github/workflows/tests.yml"),
    ]

    @pytest.mark.parametrize("path", ACTIVE_FILES, ids=lambda p: str(p))
    def test_no_active_311_mention(self, path: Path):
        """Aucune mention de Python 3.11 dans les fichiers actifs."""
        text = (PROJECT_ROOT / path).read_text(encoding="utf-8")
        assert "3.11" not in text, (
            f"{path} mentionne encore Python 3.11. "
            f"Contradiction avec requires-python = '>=3.12' (ADR-006)."
        )

    def test_pyproject_requires_python_312(self):
        """pyproject.toml exige bien >= 3.12."""
        import tomllib
        data = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        assert data["project"]["requires-python"] == ">=3.12", (
            f"requires-python doit être '>=3.12', "
            f"trouvé : {data['project']['requires-python']!r}"
        )

    def test_pyproject_classifiers_no_311(self):
        """pyproject.toml classifiers ne contient pas Python :: 3.11."""
        import tomllib
        data = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        classifiers = data["project"].get("classifiers", [])
        assert "Programming Language :: Python :: 3.11" not in classifiers, (
            "Classifier 'Python :: 3.11' présent dans pyproject.toml — à retirer."
        )

    def test_ci_matrix_no_311(self):
        """La matrice CI ne teste plus 3.11."""
        text = (PROJECT_ROOT / ".github/workflows/tests.yml").read_text(encoding="utf-8")
        for line in text.splitlines():
            if "python-version:" in line.lower():
                assert "3.11" not in line, (
                    f"La matrice CI inclut encore Python 3.11 : {line.strip()!r}"
                )
