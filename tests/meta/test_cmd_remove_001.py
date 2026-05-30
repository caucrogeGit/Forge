"""Tests CMD-LEGACY-REMOVE-001 — suppression définitive du dossier cmd/.

Vérifie que :
- cmd/ n'existe plus
- Les fichiers connus de cmd/ sont absents
- Aucun fichier productif n'importe depuis cmd/
- La documentation ne promeut plus cmd/ comme interface active
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# TestCmdDirectoryRemoved
# ---------------------------------------------------------------------------


class TestCmdDirectoryRemoved:
    def test_cmd_directory_does_not_exist(self):
        assert not (ROOT / "cmd").exists(), (
            "Le dossier cmd/ aurait dû être supprimé en Forge 2.10.0"
        )

    @pytest.mark.parametrize("removed_file", [
        "cmd/__init__.py",
        "cmd/make.py",
        "cmd/_common.py",
        "cmd/README.md",
        "cmd/security/init_users.py",
        "cmd/security/hash.py",
        "cmd/mvc/controller.py",
        "cmd/mvc/entity.py",
        "cmd/sql/migration.py",
    ])
    def test_known_files_removed(self, removed_file):
        assert not (ROOT / removed_file).exists(), (
            f"{removed_file} aurait dû être supprimé"
        )


# ---------------------------------------------------------------------------
# TestNoCmdImportsRemain
# ---------------------------------------------------------------------------


class TestNoCmdImportsRemain:
    @pytest.mark.parametrize("forbidden_pattern", [
        "from cmd ",
        "from cmd.",
        "import cmd\n",
    ])
    def test_no_cmd_imports(self, forbidden_pattern):
        roots = [
            ROOT / "core",
            ROOT / "mvc",
            ROOT / "forge_cli",
            ROOT / "integrations",
        ]
        offenders = []
        for root in roots:
            if not root.exists():
                continue
            for py_file in root.rglob("*.py"):
                if forbidden_pattern in py_file.read_text(encoding="utf-8"):
                    offenders.append(str(py_file.relative_to(ROOT)))
        assert not offenders, f"Imports cmd/ résiduels : {offenders}"


# ---------------------------------------------------------------------------
# TestDeprecationDocsClean
# ---------------------------------------------------------------------------


class TestDeprecationDocsClean:
    def test_deprecation_policy_no_longer_promotes_cmd(self):
        path = ROOT / "docs" / "release" / "deprecation-policy.md"
        if not path.exists():
            pytest.skip("docs/release/deprecation-policy.md absent")
        content = path.read_text(encoding="utf-8")
        assert "cmd/ legacy" not in content.lower(), (
            "docs/release/deprecation-policy.md mentionne encore cmd/ comme legacy actif"
        )

    def test_reference_doc_does_not_promote_cmd(self):
        path = ROOT / "docs" / "reference" / "reference.md"
        if not path.exists():
            pytest.skip("docs/reference/reference.md absent")
        content = path.read_text(encoding="utf-8")
        for pattern in ("python cmd/", "cmd/make.py", "cmd/mvc/", "cmd/security/"):
            assert pattern not in content, (
                f"docs/reference/reference.md contient encore '{pattern}'"
            )
