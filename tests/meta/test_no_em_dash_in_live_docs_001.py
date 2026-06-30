"""Garde-fou DOC-EMDASH-SWEEP-001 : pas de tiret cadratin U+2014 dans la doc vivante.

La directive de style FR (CLAUDE.md §2.1) interdit le tiret cadratin (—, U+2014)
dans la documentation. On vérifie ici toute la doc « vivante » : docs/ (hors
mémoire brute docs/history/), et la doc embarquée des paquets, du cœur et du CLI.

Exclusions assumées :
- docs/history/ : mémoire brute, conservée telle qu'écrite (convention §9 D).
- core/http/docs/request.md : fichier sous gestion manuelle de l'auteur.

Remplacement attendu : virgule, deux-points, point-virgule ou trait d'union court
« - » selon le contexte (jamais U+2014).
"""

from __future__ import annotations

import glob
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EM_DASH = "—"

EXCLUDED_DIRS = ("docs/history/",)
EXCLUDED_FILES = {"core/http/docs/request.md"}


def _doc_roots() -> list[str]:
    roots = [str(PROJECT_ROOT / "docs")]
    for pattern in ("packages/*/docs", "core/*/docs", "cli/*/docs"):
        roots.extend(glob.glob(str(PROJECT_ROOT / pattern)))
    return roots


def _live_markdown_files() -> list[Path]:
    files: list[Path] = []
    for root in _doc_roots():
        for path in Path(root).rglob("*.md"):
            rel = path.relative_to(PROJECT_ROOT).as_posix()
            if any(rel.startswith(d) for d in EXCLUDED_DIRS):
                continue
            if rel in EXCLUDED_FILES:
                continue
            files.append(path)
    return files


@pytest.mark.parametrize(
    "md_file",
    _live_markdown_files(),
    ids=lambda p: p.relative_to(PROJECT_ROOT).as_posix(),
)
def test_no_em_dash_in_live_doc(md_file: Path) -> None:
    text = md_file.read_text(encoding="utf-8")
    assert EM_DASH not in text, (
        f"{md_file.relative_to(PROJECT_ROOT)} contient un tiret cadratin U+2014 "
        f"(interdit par CLAUDE.md §2.1). Remplacer par une virgule, deux-points, "
        f"point-virgule ou trait d'union court « - »."
    )
