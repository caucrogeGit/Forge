"""Garde-fou DOCS-REFERENCE-MODULES-FIX-001.

Vérifie que les pages de référence des modules opt-in (workflow, stats, mfa)
n'enseignent pas d'imports vers des modules qui n'existent plus dans le core
(`core.workflow`, `core.stats`, `core.auth.mfa`).

Ces pages sont listées dans la nav mkdocs sous « Référence → Modules officiels ».
Un utilisateur qui copie un exemple doit pouvoir l'exécuter sans
ModuleNotFoundError.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent

REFERENCE_PAGES = {
    PROJECT_ROOT / "docs" / "reference" / "workflow.md": "forge_mvc_workflow",
    PROJECT_ROOT / "docs" / "reference" / "stats.md": "forge_mvc_stats",
    PROJECT_ROOT / "docs" / "reference" / "auth-mfa.md": "forge_mvc_mfa",
}

DEPRECATED_PREFIXES = {
    "core.workflow",
    "core.stats",
    "core.auth.mfa",
}

_FROM_PAT = {d: re.compile(rf"\bfrom\s+{re.escape(d)}\b") for d in DEPRECATED_PREFIXES}
_IMPORT_PAT = {d: re.compile(rf"\bimport\s+{re.escape(d)}\b") for d in DEPRECATED_PREFIXES}
_BACKTICK_PAT = {d: re.compile(rf"`{re.escape(d)}[`.\s]") for d in DEPRECATED_PREFIXES}


def _python_blocks(md_text: str) -> list[str]:
    return re.findall(r"```python\s*\n(.*?)```", md_text, re.DOTALL)


def _text_no_code(md_text: str) -> str:
    return re.sub(r"```.*?```", "", md_text, flags=re.DOTALL)


_PAGES = list(REFERENCE_PAGES.items())
_IDS = [p.name for p in REFERENCE_PAGES]


class TestReferencePagesNoPhantomImports:
    """Aucun import vers core.workflow, core.stats ou core.auth.mfa dans les blocs python."""

    @pytest.mark.parametrize("page,_module", _PAGES, ids=_IDS)
    def test_no_deprecated_import_in_code_blocks(self, page: Path, _module: str):
        assert page.exists(), f"{page.relative_to(PROJECT_ROOT)} doit exister"
        text = page.read_text(encoding="utf-8")
        for block in _python_blocks(text):
            for dep in DEPRECATED_PREFIXES:
                assert not _FROM_PAT[dep].search(block), (
                    f"{page.name} contient `from {dep}` dans un bloc python — "
                    f"remplacer par l'import du module extrait"
                )
                assert not _IMPORT_PAT[dep].search(block), (
                    f"{page.name} contient `import {dep}` dans un bloc python — "
                    f"remplacer par l'import du module extrait"
                )

    @pytest.mark.parametrize("page,_module", _PAGES, ids=_IDS)
    def test_no_deprecated_path_in_descriptive_text(self, page: Path, _module: str):
        text = _text_no_code(page.read_text(encoding="utf-8"))
        for dep in DEPRECATED_PREFIXES:
            matches = _BACKTICK_PAT[dep].findall(text)
            assert len(matches) <= 1, (
                f"{page.name} mentionne `{dep}` {len(matches)} fois dans le texte "
                f"descriptif (max 1 mention historique tolérée)"
            )


class TestReferencePagesUseExtractedModule:
    """Les pages référencent le module extrait par son vrai nom."""

    @pytest.mark.parametrize("page,expected_module", _PAGES, ids=_IDS)
    def test_extracted_module_mentioned(self, page: Path, expected_module: str):
        text = page.read_text(encoding="utf-8")
        assert expected_module in text, (
            f"{page.name} doit mentionner `{expected_module}` "
            f"(import ou encart d'installation)"
        )

    @pytest.mark.parametrize("page,expected_module", _PAGES, ids=_IDS)
    def test_extracted_module_actually_importable(self, page: Path, expected_module: str):
        pytest.importorskip(
            expected_module,
            reason=f"`{expected_module}` non installé — pip install -e packages/forge-mvc-{expected_module[10:]}",
        )


class TestReferencePagesHaveExtractionNotice:
    """Chaque page signale clairement que le module a été extrait du core."""

    @pytest.mark.parametrize("page,_module", _PAGES, ids=_IDS)
    def test_page_mentions_extraction(self, page: Path, _module: str):
        text = page.read_text(encoding="utf-8")
        markers = ["Module extrait", "module extrait", "distribué séparément"]
        assert any(m in text for m in markers), (
            f"{page.name} doit signaler que le module a été extrait du core "
            f"(encart « Module extrait » au début)"
        )
