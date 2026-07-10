"""Garde-fou IOT-DOCTOR-DB-CONFIG-BOOTSTRAP-001.

`forge iot:doctor --db` charge la config du projet (env/dev) si elle est présente,
pour connecter avec les identifiants applicatifs, mais ne l'exige pas (le doctor
tourne aussi hors projet). Distinct des commandes fonctionnelles adossées à la base
(config: True) qui, elles, exigent la config (ADR-072).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_iot")

from forge_mvc_iot.cli import doctor


def test_helper_does_not_raise_outside_project(tmp_path: Path, monkeypatch):
    """Hors projet (pas de config.py) : le helper avale l'erreur, ne lève pas."""
    monkeypatch.chdir(tmp_path)
    doctor._load_project_config_if_present()  # ne doit pas lever


def test_default_path_loads_config_before_connecting(monkeypatch):
    """Chemin par défaut (fetch injecté None) : la config est chargée d'abord."""
    called: list[str] = []
    monkeypatch.setattr(
        doctor, "_load_project_config_if_present",
        lambda: called.append("config"),
    )
    import core.database.db as dbmod

    monkeypatch.setattr(dbmod, "fetch_one", lambda _sql, _params: {"n": 0})
    result = doctor.check_database_table()
    assert called == ["config"], "la config projet doit être chargée avant la connexion"
    assert result.status == "ok"


def test_injected_fetch_skips_config(monkeypatch):
    """Fetch injecté (test/mock) : aucune config chargée, aucun accès réel."""
    called: list[str] = []
    monkeypatch.setattr(
        doctor, "_load_project_config_if_present",
        lambda: called.append("config"),
    )
    result = doctor.check_database_table(lambda _sql, _params: {"n": 3})
    assert called == [], "un fetch injecté ne doit pas déclencher le chargement config"
    assert result.status == "ok"
