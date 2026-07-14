"""Garde-fou — TESTS-DOCS-MARKER-001 : partition tests de prose / tests de code.

Le marqueur `docs` isole les tests de « prose pure » : ceux qui ne peuvent
casser que par édition de la documentation du dépôt (docs/, mkdocs.yml,
CHANGELOG.md, README.md, CHARTE_DOC, landing), jamais par édition de code.
La boucle rapide code est `pytest -m "not docs"` ; la CI reste exhaustive.

Règle d'auto-classification (la même que l'application initiale) :
  - candidat prose : le source référence un artefact de prose du dépôt ;
  - signal code : exécution (tmp_path, subprocess), lecture de source d'un
    module importé (<mod>.__file__, getsource), import du framework,
    chemin de code en dur (hors doc embarquée core/docs, cli/docs — ADR-043),
    packaging (pyproject.toml, requirements, .github), fixtures d'app ;
  - prose pure = candidat SANS signal code → doit porter `pytest.mark.docs` ;
  - un fichier marqué `docs` doit être prose pure (pas de test de
    comportement exilé hors de la boucle code).

Les cas que la règle statique classe mal se déclarent dans les listes
d'exceptions explicites ci-dessous, avec justification en commentaire.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent

# Fichiers prose pure autorisés à ne PAS porter le marqueur docs.
EXCEPTIONS_SANS_MARQUEUR: frozenset[str] = frozenset()

# Fichiers marqués docs bien que la règle statique voie un signal code.
EXCEPTIONS_AVEC_MARQUEUR: frozenset[str] = frozenset()

_PROSE_RE = re.compile(
    r"mkdocs\.yml|CHANGELOG\.md|README\.md|CHARTE_DOC|official-site"
    r"|[\"'(/ ]docs/|[\"']docs[\"']"
)
_CODE_SIGNALS = (
    re.compile(r"tmp_path|subprocess"),
    re.compile(r"[A-Za-z_]\w*\.__file__|getsource"),
    re.compile(
        r"^\s*(?:from|import)\s+(?:core|cli|forge_mvc\w*|skeleton|integrations)\b",
        re.MULTILINE,
    ),
    re.compile(r"[\"'](?:core|cli|skeleton)[\"'](?!\s*/\s*[\"']docs[\"'])"),
    re.compile(r"[\"'](?:core|cli|skeleton)/(?!docs)"),
    re.compile(r"[\"']forge\.py[\"']|pyproject\.toml"),
    re.compile(r"fixtures/|requirements|\.github"),
)


def _test_files() -> list[Path]:
    files = sorted((PROJECT_ROOT / "tests").glob("**/test_*.py"))
    self_path = Path(__file__).resolve()
    return [f for f in files if f.resolve() != self_path]


def _is_pure_prose(text: str) -> bool:
    if not _PROSE_RE.search(text):
        return False
    return not any(rx.search(text) for rx in _CODE_SIGNALS)


def _has_docs_marker(text: str) -> bool:
    return "pytest.mark.docs" in text


def test_prose_pure_porte_le_marqueur_docs():
    """Tout test de prose pure doit porter pytest.mark.docs (sinon la boucle
    code `-m "not docs"` le relance inutilement)."""
    manquants: list[str] = []
    for path in _test_files():
        rel = str(path.relative_to(PROJECT_ROOT))
        if rel in EXCEPTIONS_SANS_MARQUEUR:
            continue
        text = path.read_text(encoding="utf-8")
        if _is_pure_prose(text) and not _has_docs_marker(text):
            manquants.append(rel)
    assert not manquants, (
        "Tests de prose pure sans marqueur docs (ajouter "
        "`pytestmark = [pytest.mark.meta, pytest.mark.docs]` ou justifier "
        f"dans EXCEPTIONS_SANS_MARQUEUR) : {manquants}"
    )


def test_marqueur_docs_reserve_a_la_prose_pure():
    """Un test marqué docs sort de la boucle code : il ne doit porter aucun
    signal code (sinon une régression de code passe sous le radar local)."""
    indus: list[str] = []
    for path in _test_files():
        rel = str(path.relative_to(PROJECT_ROOT))
        if rel in EXCEPTIONS_AVEC_MARQUEUR:
            continue
        text = path.read_text(encoding="utf-8")
        if _has_docs_marker(text) and not _is_pure_prose(text):
            indus.append(rel)
    assert not indus, (
        "Tests marqués docs qui portent un signal code (retirer le marqueur "
        f"ou justifier dans EXCEPTIONS_AVEC_MARQUEUR) : {indus}"
    )


def test_marqueur_declare_dans_pytest_ini():
    """--strict-markers exige la déclaration ; on verrouille sa présence."""
    ini = (PROJECT_ROOT / "pytest.ini").read_text(encoding="utf-8")
    assert re.search(r"^\s*docs:", ini, re.MULTILINE), (
        "le marqueur docs doit rester déclaré dans pytest.ini"
    )
