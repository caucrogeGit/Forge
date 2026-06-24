"""Garde-fou AGENTS-SKELETON-EMIT-001 (ADR-047).

`emit_app_agent_files` écrit CLAUDE.md, AGENTS.md et docs/adr/001-adopter-forge.md
en write-if-new (jamais d'écrasement), avec la date tamponnée dans l'ADR-001.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

from cli.agents import emit_app_agent_files


def test_emet_les_trois_fichiers(tmp_path: Path):
    created = emit_app_agent_files(tmp_path, date="2026-06-24")
    assert set(created) == {
        "CLAUDE.md",
        "AGENTS.md",
        "docs/adr/001-adopter-forge.md",
    }
    assert (tmp_path / "CLAUDE.md").is_file()
    assert (tmp_path / "AGENTS.md").is_file()
    adr = tmp_path / "docs" / "adr" / "001-adopter-forge.md"
    assert adr.is_file()
    assert "2026-06-24" in adr.read_text(encoding="utf-8")


def test_claude_et_agents_meme_contenu(tmp_path: Path):
    emit_app_agent_files(tmp_path)
    claude = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    agents = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert claude == agents
    assert "application" in claude.lower()


def test_write_if_new_ne_remplace_pas(tmp_path: Path):
    (tmp_path / "CLAUDE.md").write_text("# mon briefing à moi\n", encoding="utf-8")
    created = emit_app_agent_files(tmp_path)
    # CLAUDE.md existait : non listé, non écrasé.
    assert "CLAUDE.md" not in created
    assert (tmp_path / "CLAUDE.md").read_text(encoding="utf-8") == "# mon briefing à moi\n"
    # les autres sont bien créés
    assert "AGENTS.md" in created
    assert "docs/adr/001-adopter-forge.md" in created


def test_date_par_defaut_du_jour(tmp_path: Path):
    from datetime import date
    emit_app_agent_files(tmp_path)
    adr = (tmp_path / "docs" / "adr" / "001-adopter-forge.md").read_text(encoding="utf-8")
    assert date.today().isoformat() in adr
