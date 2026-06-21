"""Garde-fou RBAC-LIGHT-VS-FULL-DOC-001.

Vérifie que la documentation distingue explicitement :
- RBAC léger core (require_role, user_has_role, déprécié)
- RBAC complet opt-in (forge-mvc-rbac)
- frontière d'import (core ne doit pas importer forge_mvc_rbac)
- tableau de décision (quand utiliser quoi)
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
RBAC_DOC = PROJECT_ROOT / "packages" / "forge-mvc-rbac" / "docs" / "reference.md"
SECURITY_DOC = PROJECT_ROOT / "docs" / "philosophy" / "security.md"
CORE_ROOT = PROJECT_ROOT / "core"


# ---------------------------------------------------------------------------
# Documentation packages/forge-mvc-rbac/docs/reference.md — frontière RBAC léger / RBAC complet
# ---------------------------------------------------------------------------

class TestRbacDocDistinguishesCoreAndOptin:

    def test_rbac_doc_mentions_require_role(self):
        content = RBAC_DOC.read_text(encoding="utf-8")
        assert "require_role" in content, (
            "packages/forge-mvc-rbac/docs/reference.md doit mentionner require_role (primitive core légère)"
        )

    def test_rbac_doc_mentions_user_has_role(self):
        content = RBAC_DOC.read_text(encoding="utf-8")
        assert "user_has_role" in content, (
            "packages/forge-mvc-rbac/docs/reference.md doit mentionner user_has_role (primitive core légère)"
        )

    def test_rbac_doc_mentions_forge_mvc_rbac(self):
        content = RBAC_DOC.read_text(encoding="utf-8")
        assert "forge_mvc_rbac" in content or "forge-mvc-rbac" in content, (
            "packages/forge-mvc-rbac/docs/reference.md doit mentionner forge_mvc_rbac ou forge-mvc-rbac"
        )

    def test_rbac_doc_mentions_opt_in(self):
        content = RBAC_DOC.read_text(encoding="utf-8")
        assert "opt-in" in content, (
            "packages/forge-mvc-rbac/docs/reference.md doit qualifier forge-mvc-rbac comme opt-in"
        )

    def test_rbac_doc_mentions_core_light_rbac(self):
        content = RBAC_DOC.read_text(encoding="utf-8")
        assert "léger" in content or "light" in content.lower(), (
            "packages/forge-mvc-rbac/docs/reference.md doit mentionner le RBAC léger core"
        )

    def test_rbac_doc_mentions_permission_fines(self):
        content = RBAC_DOC.read_text(encoding="utf-8")
        assert "permission" in content.lower(), (
            "packages/forge-mvc-rbac/docs/reference.md doit mentionner les permissions fines (forge-mvc-rbac)"
        )

    def test_rbac_doc_mentions_import_boundary(self):
        content = RBAC_DOC.read_text(encoding="utf-8")
        assert "core/" in content and "forge_mvc_rbac" in content, (
            "packages/forge-mvc-rbac/docs/reference.md doit mentionner que core/ ne doit pas importer forge_mvc_rbac"
        )

    def test_rbac_doc_has_decision_table(self):
        content = RBAC_DOC.read_text(encoding="utf-8")
        assert "Quand utiliser" in content or "quand utiliser" in content.lower(), (
            "packages/forge-mvc-rbac/docs/reference.md doit contenir un tableau de décision core léger / opt-in"
        )


# ---------------------------------------------------------------------------
# Documentation docs/philosophy/security.md — pas de rbac.py fantôme dans core/security/
# ---------------------------------------------------------------------------

class TestSecurityDocNoCoreRbacPhantom:

    def test_security_doc_does_not_claim_rbac_py_in_core(self):
        content = SECURITY_DOC.read_text(encoding="utf-8")
        lines_with_rbac_py = [
            line for line in content.splitlines()
            if "rbac.py" in line and "|" in line
        ]
        assert not lines_with_rbac_py, (
            "docs/philosophy/security.md ne doit pas lister rbac.py comme fichier core — "
            "ce fichier n'existe pas dans core/security/ : "
            + str(lines_with_rbac_py)
        )

    def test_security_doc_points_to_forge_mvc_rbac(self):
        content = SECURITY_DOC.read_text(encoding="utf-8")
        assert "forge_mvc_rbac" in content or "forge-mvc-rbac" in content, (
            "docs/philosophy/security.md doit pointer vers forge_mvc_rbac / forge-mvc-rbac"
        )


# ---------------------------------------------------------------------------
# Frontière d'import — core/ ne contient pas import forge_mvc_rbac
# ---------------------------------------------------------------------------

class TestCoreDoesNotImportForgeRbac:

    def test_core_has_no_forge_mvc_rbac_import(self):
        violations = []
        for path in CORE_ROOT.rglob("*.py"):
            if "__pycache__" in str(path):
                continue
            src = path.read_text(encoding="utf-8")
            for i, line in enumerate(src.splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith(("import forge_mvc_rbac", "from forge_mvc_rbac")):
                    violations.append(f"{path.relative_to(PROJECT_ROOT)}:{i}: {stripped}")
        assert not violations, (
            "core/ ne doit pas importer forge_mvc_rbac (RBAC-LIGHT-VS-FULL-DOC-001, ADR-004) :\n"
            + "\n".join(violations)
        )
