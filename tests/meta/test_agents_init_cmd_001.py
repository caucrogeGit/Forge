"""Garde-fou AGENTS-INIT-COMMAND-001 (ADR-047).

`forge agents:init` : crée la guidance (write-if-new), `--force` rafraîchit le
briefing sans toucher l'ADR-001, `--check` diagnostique (lecture seule).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

from cli.agents.briefing import render_app_briefing
from cli.agents.cli import main as agents_init_main


def test_init_cree_la_guidance(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    assert agents_init_main([]) == 0
    assert (tmp_path / "CLAUDE.md").is_file()
    assert (tmp_path / "AGENTS.md").is_file()
    assert (tmp_path / "docs" / "adr" / "001-adopter-forge.md").is_file()


def test_init_idempotent(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    assert agents_init_main([]) == 0
    assert agents_init_main([]) == 0  # rejouable, write-if-new


def test_check_signale_absence(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    assert agents_init_main(["--check"]) == 1  # rien encore


def test_check_ok_apres_init(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    agents_init_main([])
    assert agents_init_main(["--check"]) == 0


def test_check_detecte_divergence(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    agents_init_main([])
    (tmp_path / "CLAUDE.md").write_text("# modifié à la main\n", encoding="utf-8")
    assert agents_init_main(["--check"]) == 1


def test_force_rafraichit_briefing_sans_toucher_adr(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    agents_init_main([])
    adr = tmp_path / "docs" / "adr" / "001-adopter-forge.md"
    adr.write_text("# mon ADR-001 personnalisé\n", encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text("# divergé\n", encoding="utf-8")
    assert agents_init_main(["--force"]) == 0
    # briefing rafraîchi
    assert (tmp_path / "CLAUDE.md").read_text(encoding="utf-8") == render_app_briefing()
    # ADR-001 préservé
    assert adr.read_text(encoding="utf-8") == "# mon ADR-001 personnalisé\n"
