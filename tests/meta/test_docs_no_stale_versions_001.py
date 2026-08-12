"""Garde-fou DOCS-3.0.1-VERSION-SWEEP-001.

Vérifie que la documentation active ne référence pas des versions
obsolètes (Forge 2.x.y, tag v3.0.0) là où seule la version courante
devrait apparaître.

Frictions corrigées par T7 :
- F6 : app.py docstring 'Forge 2.0.1'
- F5 : docs/release/release-local.md 'Forge 2.0.0' (lignes 50 et 351)
- F4 : guide.md, install/github.md, profiles.md 'v3.0.0'

Les fichiers HISTORIQUES sont explicitement exclus du check large :
- docs/history/, docs/audits/, docs/adr/ — archives
- docs/roadmap/ — planification historique
- docs/reference/ — notes d'extraction depuis Forge 2.x
- docs/release/deprecation-policy.md, docs/features/auth.md, docs/features/migration-guide.md,
  docs/release/lts-policy.md, docs/release/release-policy.md — documentent intentionnellement
  les versions 2.x ou montrent des exemples de tags historiques
- CHANGELOG.md, tests/ — historique ou tests de conformité historique
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent

STALE_FORGE_VERSION_PATTERN = re.compile(r"\bForge 2\.\d+\.\d+\b")
STALE_TAG_V3_0_0_PATTERN = re.compile(r"\bv3\.0\.0\b")

# Chemins exclus du scan large (mentions historiques légitimes)
EXCLUDED_PATHS = [
    "docs/history",
    "docs/audits",
    "docs/adr",
    "docs/roadmap",
    "docs/reference",
    "docs/release/deprecation-policy.md",
    "docs/features/auth.md",
    "docs/features/migration-guide.md",
    "docs/release/lts-policy.md",
    "docs/release/release-policy.md",
    "CHANGELOG.md",
    "CLAUDE.md",        # note de mise à jour historique "Forge 2.10.0"
    "tests",
    "__pycache__",
    # Artefact d'outillage, au même titre que `.venv`, `site` et `build`.
    # Son absence de cette liste rendait le relevé intermittent : `pytest`
    # écrit `.pytest_cache/README.md`, et sous `-n` quatre workers le
    # réécrivent pendant que le balayage le lit. En série, le cache est posé
    # une fois puis stable, si bien que le défaut ne se voyait pas.
    ".pytest_cache",
    ".git",
    ".claude",          # worktrees et cache d'agents
    ".venv",
    "TestForge101",     # application de test gitignorée
    "official-site",    # outillage de publication + archives forge-web (ADR-045)
    "packages",
    "site",
    "build",
    "dist",
    "cmd",
]


def _is_excluded(path: Path) -> bool:
    rel_str = str(path.relative_to(PROJECT_ROOT))
    return any(rel_str.startswith(exc) for exc in EXCLUDED_PATHS)


def _find_active_md_docs() -> list[Path]:
    """Retourne les fichiers .md actifs (hors exclus).

    Le scan large se limite aux .md : les fichiers .py contiennent
    légitimement des commentaires historiques ('extrait depuis Forge 2.4.0',
    'deprecated en Forge 2.10.0', etc.). Les cibles .py sont testées
    séparément via des tests ciblés (app.py dans TestNoStaleForgeVersionInActiveDocs).
    """
    files = []
    for path in PROJECT_ROOT.rglob("*.md"):
        if not _is_excluded(path):
            files.append(path)
    return files


# ---------------------------------------------------------------------------
# Classe 1 — Cibles spécifiques confirmées par audit F4/F5/F6
# ---------------------------------------------------------------------------

class TestNoStaleForgeVersionInActiveDocs:

    def test_no_forge_2_x_in_app_py(self):
        text = (PROJECT_ROOT / "tests" / "fixtures" / "app" / "app.py").read_text(encoding="utf-8")
        match = STALE_FORGE_VERSION_PATTERN.search(text)
        assert not match, (
            f"app.py contient une mention obsolète : '{match.group()}'. "
            f"À remplacer par la version courante (voir pyproject.toml)."
        )

    def test_no_forge_2_x_in_release_local(self):
        text = (PROJECT_ROOT / "docs" / "release" / "release-local.md").read_text(encoding="utf-8")
        match = STALE_FORGE_VERSION_PATTERN.search(text)
        assert not match, (
            f"docs/release/release-local.md contient une mention obsolète : "
            f"'{match.group()}'. À remplacer par la version courante (voir pyproject.toml)."
        )

    def test_no_forge_2_x_in_installation_github(self):
        text = (PROJECT_ROOT / "docs" / "install" / "github.md").read_text(encoding="utf-8")
        match = STALE_FORGE_VERSION_PATTERN.search(text)
        assert not match, (
            f"docs/install/github.md contient une mention obsolète : "
            f"'{match.group()}'. (version périmée, voir pyproject.toml)."
        )


class TestNoStaleTagV300InActiveDocs:

    def test_no_v3_0_0_in_guide(self):
        text = (PROJECT_ROOT / "docs" / "guide" / "guide.md").read_text(encoding="utf-8")
        match = STALE_TAG_V3_0_0_PATTERN.search(text)
        assert not match, (
            "docs/guide/guide.md référence encore v3.0.0. "
            "À remplacer par la version courante (voir pyproject.toml)."
        )

    def test_no_v3_0_0_in_installation_github(self):
        text = (PROJECT_ROOT / "docs" / "install" / "github.md").read_text(encoding="utf-8")
        match = STALE_TAG_V3_0_0_PATTERN.search(text)
        assert not match, (
            "docs/install/github.md référence encore v3.0.0. "
            "À remplacer par la version courante (voir pyproject.toml)."
        )

    def test_no_v3_0_0_in_profiles(self):
        text = (PROJECT_ROOT / "docs" / "features" / "profiles.md").read_text(encoding="utf-8")
        match = STALE_TAG_V3_0_0_PATTERN.search(text)
        assert not match, (
            "docs/features/profiles.md référence encore v3.0.0. "
            "À remplacer par la version courante (voir pyproject.toml)."
        )


# ---------------------------------------------------------------------------
# Classe 2 — Scan large sur les docs actives (hors exclus)
# ---------------------------------------------------------------------------

class TestNoStaleVersionInActiveDocs:

    def test_no_active_forge_2_x_across_docs(self):
        """Aucun doc actif (hors exclus) ne mentionne 'Forge 2.x.y'."""
        violations = []
        for doc in _find_active_md_docs():
            try:
                text = doc.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                continue
            for match in STALE_FORGE_VERSION_PATTERN.finditer(text):
                line_num = text[: match.start()].count("\n") + 1
                violations.append(
                    f"{doc.relative_to(PROJECT_ROOT)}:{line_num} : '{match.group()}'"
                )
        assert not violations, (
            "Mentions 'Forge 2.x.y' actives détectées :\n  "
            + "\n  ".join(violations[:20])
            + ("\n  ..." if len(violations) > 20 else "")
            + "\n\nCes mentions doivent être bumpées à la version courante (voir pyproject.toml)."
        )

    def test_no_active_v3_0_0_across_docs(self):
        """Aucun doc actif (hors exclus) ne référence v3.0.0."""
        violations = []
        for doc in _find_active_md_docs():
            try:
                text = doc.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                continue
            for match in STALE_TAG_V3_0_0_PATTERN.finditer(text):
                line_num = text[: match.start()].count("\n") + 1
                violations.append(
                    f"{doc.relative_to(PROJECT_ROOT)}:{line_num} : '{match.group()}'"
                )
        assert not violations, (
            "Références 'v3.0.0' actives détectées :\n  "
            + "\n  ".join(violations[:20])
            + ("\n  ..." if len(violations) > 20 else "")
            + "\n\nÀ remplacer par la version courante (voir pyproject.toml)."
        )


# ---------------------------------------------------------------------------
# Classe 3 — Cohérence forge.py
# ---------------------------------------------------------------------------

class TestForgePyVersionConsistency:

    def _current_version(self) -> str:
        import tomllib
        return tomllib.loads(
            (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )["project"]["version"]

    def _current_ref(self) -> str:
        import re as _re
        v = self._current_version()
        semver = _re.sub(r"(\d+\.\d+\.\d+)a(\d+)$", r"\1-alpha.\2", v)
        semver = _re.sub(r"(\d+\.\d+\.\d+)b(\d+)$", r"\1-beta.\2", semver)
        semver = _re.sub(r"(\d+\.\d+\.\d+)rc(\d+)$", r"\1-rc.\2", semver)
        return f"v{semver}"

    def test_forge_version_current(self):
        expected = self._current_version()
        text = (PROJECT_ROOT / "forge.py").read_text(encoding="utf-8")
        match = re.search(r'_FORGE_VERSION\s*=\s*"([^"]+)"', text)
        assert match, "forge.py doit déclarer _FORGE_VERSION"
        assert match.group(1) == expected, (
            f"forge.py _FORGE_VERSION = '{match.group(1)}', attendu '{expected}'."
        )

    def test_forge_default_ref_current(self):
        expected_ref = self._current_ref()
        text = (PROJECT_ROOT / "forge.py").read_text(encoding="utf-8")
        match = re.search(r'_FORGE_DEFAULT_REF\s*=\s*"([^"]+)"', text)
        assert match, "forge.py doit déclarer _FORGE_DEFAULT_REF"
        assert match.group(1) == expected_ref, (
            f"forge.py _FORGE_DEFAULT_REF = '{match.group(1)}', attendu '{expected_ref}'."
        )
