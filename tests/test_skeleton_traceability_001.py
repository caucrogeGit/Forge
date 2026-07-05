"""SKELETON-STANDARDS-CONFORMANCE-001 / T5 (ADR-063) — traçabilité et hygiène.

`forge new` livre par défaut de quoi tenir un journal de décisions et une base
de dépôt saine : un scaffold ADR (`docs/adr/index.md` + `docs/adr/000-template.md`,
en plus de `001-adopter-forge.md` posé par agents:init), un `.editorconfig` et
un `CHANGELOG.md` amorcé. Les pointeurs vers les ADR fondateurs de Forge (F7)
sont vérifiés côté briefing (test_agents_briefing_001).
"""
from __future__ import annotations

from pathlib import Path

SKELETON = Path(__file__).parent.parent / "cli" / "skeleton" / "data"


# ── Scaffold ADR ─────────────────────────────────────────────────────────────

def test_scaffold_adr_livre():
    adr = SKELETON / "docs" / "adr"
    assert (adr / "index.md").is_file(), "docs/adr/index.md attendu (ADR-063)"
    assert (adr / "000-template.md").is_file(), "docs/adr/000-template.md attendu (ADR-063)"


def test_template_adr_porte_les_sections_du_format_forge():
    template = (SKELETON / "docs" / "adr" / "000-template.md").read_text(encoding="utf-8")
    for section in ("## Statut", "## Contexte", "## Décision", "## Conséquences",
                    "### Alternatives écartées"):
        assert section in template, f"section {section!r} attendue dans le gabarit ADR"


def test_index_adr_pointe_le_gabarit():
    index = (SKELETON / "docs" / "adr" / "index.md").read_text(encoding="utf-8")
    assert "000-template.md" in index


# ── Hygiène de dépôt ─────────────────────────────────────────────────────────

def test_editorconfig_livre():
    editorconfig = SKELETON / ".editorconfig"
    assert editorconfig.is_file(), ".editorconfig attendu (ADR-063)"
    content = editorconfig.read_text(encoding="utf-8")
    assert "root = true" in content
    # Le Makefile doit rester en tabulations malgré l'indentation espaces par défaut.
    assert "[Makefile]" in content and "indent_style = tab" in content


def test_changelog_amorce():
    changelog = SKELETON / "CHANGELOG.md"
    assert changelog.is_file(), "CHANGELOG.md attendu (ADR-063)"
    content = changelog.read_text(encoding="utf-8")
    assert "Keep a Changelog" in content
    assert "[Non publié]" in content
