"""Tests DOCS-REFERENCE-SPLIT-001 : reference.md decoupe en sous-fichiers.

Verifie que :
- docs/reference/reference.md est devenu un index leger (<200 lignes) ;
- les 11 sous-fichiers existent dans docs/reference/ ;
- les titres "Phase 5" et "Phase 6" ont disparu des sous-fichiers ;
- les modules extraits sont mentionnes avec pointeurs ;
- le contenu critique est present dans les sous-fichiers attendus.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_DIR = PROJECT_ROOT / "docs" / "reference"
REFERENCE_INDEX = PROJECT_ROOT / "docs" / "reference" / "reference.md"


# ── reference.md est un index leger ──────────────────────────────────────────

class TestReferenceIndexIsLight:

    def test_reference_md_exists(self):
        assert REFERENCE_INDEX.exists()

    def test_reference_md_is_short(self):
        content = REFERENCE_INDEX.read_text(encoding="utf-8")
        line_count = len(content.splitlines())
        assert line_count < 200, (
            f"docs/reference/reference.md fait {line_count} lignes — devrait etre un "
            f"index leger (<200 lignes)."
        )

    # DOCS-REORG-REFERENCE-001 : reference.md vit désormais DANS docs/reference/,
    # ses liens vers les sous-fichiers sont donc relatifs au même dossier (frères).
    def test_reference_md_links_to_api(self):
        assert "](api.md)" in REFERENCE_INDEX.read_text(encoding="utf-8")

    def test_reference_md_links_to_workflow(self):
        assert "](workflow.md)" in REFERENCE_INDEX.read_text(encoding="utf-8")

    def test_reference_md_links_to_stats(self):
        assert "](stats.md)" in REFERENCE_INDEX.read_text(encoding="utf-8")

    def test_reference_md_links_to_modules(self):
        assert "](modules.md)" in REFERENCE_INDEX.read_text(encoding="utf-8")

    def test_reference_md_mentions_extracted_modules(self):
        content = REFERENCE_INDEX.read_text(encoding="utf-8")
        assert "forge-mvc-mfa" in content
        assert "forge-mvc-rbac" in content
        assert "forge-mvc-workflow" in content
        assert "forge-mvc-stats" in content


# ── Les 11 sous-fichiers existent ─────────────────────────────────────────────

_EXPECTED_SUBFILES = [
    "api.md",
    "cli-commands.md",
    "http.md",
    "workflow.md",
    "stats.md",
    "auth-mfa.md",
    "crud.md",
    "pages-publiques.md",
    "modules.md",
    "profils.md",
    "tests-e2e.md",
    "sessions.md",
    "audit-auth.md",
]


@pytest.mark.parametrize("subfile", _EXPECTED_SUBFILES)
class TestReferenceSubfilesExist:

    def test_subfile_exists(self, subfile):
        assert (REFERENCE_DIR / subfile).exists(), (
            f"docs/reference/{subfile} doit exister apres le decoupage"
        )

    def test_subfile_not_empty(self, subfile):
        path = REFERENCE_DIR / subfile
        if path.exists():
            assert path.stat().st_size > 0, f"{subfile} est vide"

    def test_subfile_has_h1_title(self, subfile):
        path = REFERENCE_DIR / subfile
        if not path.exists():
            pytest.skip(f"{subfile} n'existe pas")
        content = path.read_text(encoding="utf-8")
        assert any(line.startswith("# ") for line in content.splitlines()), (
            f"{subfile} n'a pas de titre de niveau 1 (#)"
        )


# ── Titres "Phase X" supprimes des sous-fichiers ─────────────────────────────

@pytest.mark.parametrize("subfile,forbidden_pattern", [
    ("crud.md", "Phase 5"),
    ("pages-publiques.md", "Phase 6"),
])
class TestPhaseTitlesRemoved:

    def test_no_phase_title_in_subfile(self, subfile, forbidden_pattern):
        path = REFERENCE_DIR / subfile
        if not path.exists():
            pytest.skip(f"{subfile} n'existe pas")
        content = path.read_text(encoding="utf-8")
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("#") and forbidden_pattern in stripped:
                pytest.fail(
                    f"{subfile} contient encore un titre avec "
                    f"'{forbidden_pattern}' : {stripped}"
                )


# ── Modules extraits mentionnes ───────────────────────────────────────────────

@pytest.mark.parametrize("subfile,module_pkg", [
    ("workflow.md", "forge-mvc-workflow"),
    ("stats.md", "forge-mvc-stats"),
    ("auth-mfa.md", "forge-mvc-mfa"),
])
class TestExtractedModulesNoted:

    def test_mentions_module_extraction(self, subfile, module_pkg):
        path = REFERENCE_DIR / subfile
        if not path.exists():
            pytest.skip(f"{subfile} n'existe pas")
        content = path.read_text(encoding="utf-8")
        assert module_pkg in content or "Module extrait" in content, (
            f"{subfile} devrait mentionner l'extraction vers {module_pkg}"
        )


# ── Contenu critique present dans les bons fichiers ──────────────────────────

@pytest.mark.parametrize("keyword,expected_subfile", [
    ("CSRF", "tests-e2e.md"),
    ("Endpoint de sant", "profils.md"),
    ("WorkflowStatus", "workflow.md"),
    ("track_event", "stats.md"),
    ("log_auth_event", "audit-auth.md"),
])
class TestNoCriticalContentLost:

    def test_keyword_in_expected_subfile(self, keyword, expected_subfile):
        path = REFERENCE_DIR / expected_subfile
        if not path.exists():
            pytest.skip(f"{expected_subfile} n'existe pas")
        content = path.read_text(encoding="utf-8")
        assert keyword in content, (
            f"Mot-cle critique '{keyword}' attendu dans "
            f"docs/reference/{expected_subfile}"
        )


# ── Pas de fichiers inattendus dans docs/reference/ ──────────────────────────

class TestNoUnexpectedSubfiles:

    def test_only_expected_subfiles(self):
        if not REFERENCE_DIR.exists():
            pytest.skip("docs/reference/ n'existe pas")
        # _EXPECTED_SUBFILES = les 13 sous-fichiers du découpage ; on autorise
        # en plus l'index reference.md et les 3 docs de référence regroupées
        # ici par DOCS-REORG-REFERENCE-001.
        expected = set(_EXPECTED_SUBFILES) | {
            "reference.md",
            "reference-schema.md",
            "api-json.md",
            "runtime-errors-schema.md",
            "vocabulaire-opt-in.md",  # glossaire canonique (OPTIN-VOCAB-001, ADR-016)
            "public-contract-1.0.md",  # gel surface publique (CLI-PUBLIC-CONTRACT-FREEZE-001)
            "markdown.md",  # aide-mémoire Markdown (DOCS-MARKDOWN-FLATTEN-001)
        }
        actual = {f.name for f in REFERENCE_DIR.glob("*.md")}
        unexpected = actual - expected
        assert not unexpected, (
            f"Fichiers inattendus dans docs/reference/ : {unexpected}"
        )
