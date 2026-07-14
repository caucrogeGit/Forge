"""Garde-fou DOCS-STRICT-VALIDATION-001 (partie 1/2).

Sweep global : aucun fichier .md actif de la doc utilisateur ne contient
de bloc ```python``` important depuis un module fantôme (core.workflow,
core.stats, core.security.rbac, core.auth.mfa, core.auth.oidc, core.media).

Différence avec les garde-fous C1/C2 :
- C1 scanne 3 fichiers spécifiques (workflow.md, stats.md, auth-mfa.md)
- C2 scanne 7 fichiers spécifiques (rbac.md, security.md, etc.)
- F1 (ce test) scanne TOUS les .md actifs : si quelqu'un crée demain une
  page qui importe core.workflow, F1 le détecte automatiquement.

Whitelist : voir EXCLUDED_DIRS et EXCLUDED_FILES.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
pytestmark = [pytest.mark.meta, pytest.mark.docs]

PROJECT_ROOT = Path(__file__).parent.parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
# Doc des opt-ins embarquée par paquet (ADR-038) : balayée aussi.
PACKAGES_DIR = PROJECT_ROOT / "packages"

PHANTOM_MODULES = {
    "core.security.rbac": "forge_mvc_rbac",
    "core.auth.oidc":     None,
    "core.auth.mfa":      "forge_mvc_mfa",
    "core.workflow":      "forge_mvc_workflow",
    "core.stats":         "forge_mvc_stats",
    "core.media":         "core.uploads",
}

EXCLUDED_DIRS: set[str] = {"history", "audits"}

EXCLUDED_FILES: set[Path] = set()


def _active_md_files() -> list[Path]:
    files: list[Path] = []
    roots = [DOCS_DIR, *sorted(PACKAGES_DIR.glob("*/docs"))]
    for root in roots:
        for md in root.rglob("*.md"):
            if any(part in EXCLUDED_DIRS for part in md.parts):
                continue
            if md in EXCLUDED_FILES:
                continue
            files.append(md)
    return sorted(files)


def _python_blocks(text: str) -> list[str]:
    pattern = re.compile(r"```python\s*\n(.*?)```", re.DOTALL)
    return pattern.findall(text)


class TestNoPhantomModulesInAnyActiveDoc:
    """Sweep global : aucun .md actif n'importe depuis un module fantôme."""

    def test_phantom_modules_set_is_non_empty(self):
        assert PHANTOM_MODULES

    def test_at_least_one_active_doc_found(self):
        files = _active_md_files()
        assert len(files) >= 20, (
            f"Trop peu de .md actifs trouvés ({len(files)}). "
            "Vérifier EXCLUDED_DIRS et EXCLUDED_FILES."
        )

    def test_no_phantom_imports_in_any_active_doc(self):
        offenders: list[tuple[str, str, str]] = []
        for md_path in _active_md_files():
            text = md_path.read_text(encoding="utf-8")
            for block in _python_blocks(text):
                for phantom in PHANTOM_MODULES:
                    pat_from = re.compile(
                        rf"^\s*from\s+{re.escape(phantom)}\b", re.MULTILINE
                    )
                    pat_import = re.compile(
                        rf"^\s*import\s+{re.escape(phantom)}\b", re.MULTILINE
                    )
                    if pat_from.search(block) or pat_import.search(block):
                        offenders.append((str(md_path), phantom, block[:80]))

        if offenders:
            lines = [
                f"  {path} → import `{phantom}`\n    bloc : {block!r}..."
                for path, phantom, block in offenders
            ]
            replacements = "\n".join(
                f"  {p} → {r}" for p, r in PHANTOM_MODULES.items() if r
            )
            raise AssertionError(
                "Modules fantômes importés dans des blocs python actifs :\n"
                + "\n".join(lines)
                + f"\n\nRemplacements :\n{replacements}"
            )
