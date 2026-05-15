"""Garde-fou DOCS-PHANTOM-MODULES-001.

Vérifie qu'aucun fichier de documentation (hors ADR et notes historiques
explicitement taguées) ne contient d'import actif vers les modules fantômes
du core (core.security.rbac, core.auth.mfa, core.workflow, core.stats,
core.auth.oidc, core.media).

Seuls les blocs python sont inspectés (Type 1). Les mentions descriptives
en prose (Type 2) et les notes historiques dans les ADR (Type 3) sont
exclues volontairement pour éviter les faux positifs.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent

PHANTOM_MODULES = [
    "core.security.rbac",
    "core.auth.mfa",
    "core.workflow",
    "core.stats",
    "core.auth.oidc",
    "core.media",
]

_SCANNED_DOCS = [
    PROJECT_ROOT / "docs" / "rbac.md",
    PROJECT_ROOT / "docs" / "security.md",
    PROJECT_ROOT / "docs" / "auth.md",
    PROJECT_ROOT / "docs" / "reference" / "workflow.md",
    PROJECT_ROOT / "docs" / "reference" / "stats.md",
    PROJECT_ROOT / "docs" / "reference" / "auth-mfa.md",
    PROJECT_ROOT / "SECURITY.md",
]

_SCANNED_IDS = [p.name for p in _SCANNED_DOCS]


def _python_blocks(md_text: str) -> list[str]:
    return re.findall(r"```python\s*\n(.*?)```", md_text, re.DOTALL)


def _has_phantom_import(block: str, module: str) -> bool:
    from_pat = re.compile(rf"\bfrom\s+{re.escape(module)}\b")
    import_pat = re.compile(rf"\bimport\s+{re.escape(module)}\b")
    return bool(from_pat.search(block) or import_pat.search(block))


@pytest.mark.parametrize("doc_path", _SCANNED_DOCS, ids=_SCANNED_IDS)
class TestPhantomModulesNotInCodeBlocks:
    """Aucun bloc python dans les pages scannées ne contient d'import fantôme."""

    def test_no_phantom_import_in_code_blocks(self, doc_path: Path):
        if not doc_path.exists():
            pytest.skip(f"{doc_path.name} n'existe pas encore")
        text = doc_path.read_text(encoding="utf-8")
        violations: list[str] = []
        for block in _python_blocks(text):
            for module in PHANTOM_MODULES:
                if _has_phantom_import(block, module):
                    violations.append(
                        f"{doc_path.name} — import fantôme `{module}` dans un bloc python"
                    )
        assert not violations, "\n".join(violations)
