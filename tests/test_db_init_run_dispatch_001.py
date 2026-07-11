"""Garde-fou DB-INIT-RUN-DISPATCH-001 (audit correctness).

`forge db:init --run` doit transmettre `--run` au handler : le dispatch de
forge.py passait `[command]` au lieu de l'argv complet, perdant silencieusement
`--run` (le provisioning ne s'exécutait jamais via la CLI). Ce test traverse le
vrai `forge.main()`, chemin qui n'était pas couvert.
"""
from __future__ import annotations

import sys

import pytest

pytest.importorskip("forge_mvc_entities")

import forge as forge_cli
import forge_mvc_entities.db_init as db_init_mod
import forge_mvc_entities.db_apply as db_apply_mod


def _run_forge(monkeypatch, argv: list[str], target_mod) -> list[str]:
    """Lance forge.main() avec argv et capture l'argv reçu par le handler cible."""
    captured: list[str] = []
    monkeypatch.setattr(target_mod, "main", lambda a=None: captured.extend(a or []))
    monkeypatch.setattr(sys, "argv", ["forge", *argv])
    forge_cli.main()
    return captured


def test_db_init_run_flag_reaches_handler(monkeypatch):
    captured = _run_forge(monkeypatch, ["db:init", "--run"], db_init_mod)
    assert "--run" in captured, "forge db:init --run doit transmettre --run au handler"
    assert captured[0] == "db:init"


def test_db_init_without_run(monkeypatch):
    captured = _run_forge(monkeypatch, ["db:init"], db_init_mod)
    assert captured == ["db:init"]
    assert "--run" not in captured


def test_db_apply_receives_full_argv(monkeypatch):
    captured = _run_forge(monkeypatch, ["db:apply"], db_apply_mod)
    assert captured == ["db:apply"]
