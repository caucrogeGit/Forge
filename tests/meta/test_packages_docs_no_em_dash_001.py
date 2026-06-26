"""Garde-fou DOC-STYLE-U2014-PACKAGES-001.

Étend le sweep du tiret cadratin U+2014 (interdit en prose, style francophone
CLAUDE.md §2.1) aux **docs embarquées des paquets** (`packages/*/docs/`), angle
mort des garde-fous existants qui ne couvraient que la doc racine et les
parcours welcome du cœur.

La règle ne porte que sur la prose : un cadratin à l'intérieur d'un bloc de code
(fence ``` ou ~~~) ou d'un span de code inline (`...`) est conservé, car il
cite une sortie CLI réelle, du HTML d'exemple ou un gabarit Jinja, qui doit
rester fidèle au programme. Le séparateur de titre canonique reste les
deux-points (voir `# Bilan : niveau ...`).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
PACKAGES_DIR = PROJECT_ROOT / "packages"

EM_DASH = "—"

_FENCE = re.compile(r"^\s*(```|~~~)")
_INLINE_CODE = re.compile(r"`[^`]*`", re.S)


def _strip_code(text: str) -> str:
    """Retire les blocs de code (fences) et les spans de code inline.

    Le reste est la prose, seule soumise à l'interdiction du cadratin.
    """
    kept: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if _FENCE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            kept.append(line)
    # Les spans inline peuvent s'étendre sur plusieurs lignes (CommonMark).
    return _INLINE_CODE.sub("", "\n".join(kept))


def _package_doc_files() -> list[Path]:
    return sorted(PACKAGES_DIR.glob("*/docs/**/*.md"))


def test_packages_have_docs() -> None:
    """Le garde-fou doit avoir un périmètre non vide (sinon il ne protège rien)."""
    assert _package_doc_files(), "Aucune doc de paquet trouvée sous packages/*/docs/"


@pytest.mark.parametrize(
    "doc",
    _package_doc_files(),
    ids=lambda p: str(p.relative_to(PACKAGES_DIR)),
)
def test_no_em_dash_in_prose(doc: Path) -> None:
    prose = _strip_code(doc.read_text(encoding="utf-8"))
    offending = [
        line.strip()
        for line in prose.splitlines()
        if EM_DASH in line
    ]
    assert not offending, (
        f"{doc.relative_to(PROJECT_ROOT)} contient un tiret cadratin U+2014 en "
        "prose (interdit, style francophone CLAUDE.md §2.1 ; utiliser virgule, "
        "point-virgule, deux-points ou parenthèses). Lignes : "
        f"{offending}"
    )
