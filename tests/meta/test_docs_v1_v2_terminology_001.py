"""Garde-fou DOCS-V1-V2-TERMINOLOGY-001.

Vérifie qu'aucune référence isolée « V1 » ou « V2 » ne subsiste dans la
documentation active. Les formes acceptables sont :
  - « format_version » (clé JSON)
  - « version 1 du format » / « version 2 du format » (formulation explicite)
  - « version future » (désignation non versionnée)
  - codes de tickets contenant « -V1- » ou « -V2- » (ex. CHARTER-V2-ADOPTION-001)
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

_EXCLUDED_DIRS = {"history", "audits"}

_ACCEPTABLE_CONTEXT = [
    "format_version",
    "version 1 du format",
    "version 2 du format",
    "version future",
]

_TICKET_CODE_RE = re.compile(r"-V[12]-")


def _active_md_files() -> list[Path]:
    files: list[Path] = []
    for md in Path("docs").rglob("*.md"):
        if any(part in _EXCLUDED_DIRS for part in md.parts):
            continue
        files.append(md)
    for name in ("README.md", "SECURITY.md", "CONTRIBUTING.md"):
        p = Path(name)
        if p.exists():
            files.append(p)
    return sorted(files)


class TestNoAmbiguousV1V2InActiveDocs:
    """Aucune référence isolée V1/V2 ne doit subsister dans la doc active."""

    def test_no_isolated_v1_v2_references(self):
        pattern = re.compile(r"\bV[12]\b")
        offenders: list[tuple[str, int, str]] = []

        for md_path in _active_md_files():
            text = md_path.read_text(encoding="utf-8")
            lines = text.splitlines()
            for line_no, line in enumerate(lines, start=1):
                if not pattern.search(line):
                    continue
                # Tolérance : codes de tickets (ex. CHARTER-V2-ADOPTION-001)
                if _TICKET_CODE_RE.search(line):
                    continue
                # Tolérance : contexte de 3 lignes avant
                ctx_start = max(0, line_no - 4)
                context = "\n".join(lines[ctx_start:line_no])
                if any(m in context for m in _ACCEPTABLE_CONTEXT):
                    continue
                offenders.append((str(md_path), line_no, line.strip()))

        assert not offenders, (
            "Références V1/V2 ambiguës trouvées dans la documentation active :\n"
            + "\n".join(f"  {f}:{n}  {l}" for f, n, l in offenders)
        )
