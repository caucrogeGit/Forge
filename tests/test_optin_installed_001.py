"""Commande forge opt-in:installed (OPTIN-INSTALLED-001).

Vérifie la détection des distributions installées et la sortie, sans contexte
projet ni base.
"""
from __future__ import annotations

import pytest

from cli.optins.installed import installed_version, list_installed, main


def test_installed_version_absent_returns_none() -> None:
    assert installed_version("forge-mvc-paquet-inexistant-xyz") is None


def test_installed_version_present_for_core() -> None:
    # forge-mvc (le cœur) est installé dans l'environnement de test.
    assert installed_version("forge-mvc") is not None


def test_main_returns_zero(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    out = capsys.readouterr().out
    assert "Opt-ins installés (pip)" in out


def test_lists_installed_optin_with_version(capsys: pytest.CaptureFixture[str]) -> None:
    # forge-mvc-fixtures est installé en éditable dans l'environnement de test :
    # il doit apparaître avec une version, pas « (non installé) ».
    pytest.importorskip("forge_mvc_fixtures")
    list_installed()
    lines = [l for l in capsys.readouterr().out.splitlines() if l.strip().startswith("fixtures")]
    assert lines, "la ligne fixtures doit être présente"
    assert "(non installé)" not in lines[0], "fixtures est installé, doit montrer sa version"


def test_absent_optin_marked_not_installed(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    # Force une distribution absente pour prouver le marquage « (non installé) ».
    import cli.optins.installed as mod

    monkeypatch.setattr(mod, "installed_version", lambda dist: None)
    list_installed()
    out = capsys.readouterr().out
    assert "(non installé)" in out
    assert "Aucun opt-in installé" in out
