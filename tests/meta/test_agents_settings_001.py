"""Garde-fou AGENTS-SETTINGS-001 (ADR-047).

`.claude/settings.json` applicatif : JSON valide, pré-autorise les commandes
usuelles, refuse les destructrices. Opt-in : écrit seulement via
`forge agents:init --settings`, jamais par défaut.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

from cli.agents import emit_app_agent_files, render_app_settings
from cli.agents.cli import main as agents_init_main


def test_settings_json_valide():
    data = json.loads(render_app_settings())
    allow = data["permissions"]["allow"]
    deny = data["permissions"]["deny"]
    assert "Bash(forge:*)" in allow
    assert any("pytest" in a for a in allow)
    assert "Bash(rm -rf:*)" in deny
    assert "Bash(git push -f:*)" in deny
    # minimal : pas de defaultMode ni de hooks imposés
    assert "defaultMode" not in data.get("permissions", {})
    assert "hooks" not in data


def test_emit_sans_settings_par_defaut(tmp_path: Path):
    created = emit_app_agent_files(tmp_path)
    assert ".claude/settings.json" not in created
    assert not (tmp_path / ".claude" / "settings.json").exists()


def test_emit_avec_settings(tmp_path: Path):
    created = emit_app_agent_files(tmp_path, with_settings=True)
    assert ".claude/settings.json" in created
    assert (tmp_path / ".claude" / "settings.json").is_file()


def test_commande_settings_opt_in(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    # sans --settings : pas de .claude/settings.json
    agents_init_main([])
    assert not (tmp_path / ".claude" / "settings.json").exists()
    # avec --settings : créé
    assert agents_init_main(["--settings"]) == 0
    assert (tmp_path / ".claude" / "settings.json").is_file()
