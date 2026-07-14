"""Tests — CORE-OPTIN-INIT-HELPER-001 : helper partagé de provisioning des opt-ins.

La logique de ``<optin>:init`` (copie idempotente des migrations SQL embarquées
vers ``mvc/migrations/``, sans exécution, non-écrasement) était dupliquée dans
huit paquets. Elle vit désormais dans ``cli._support.optin_migrations`` ; ce test
couvre le helper une fois pour toutes, contre un vrai paquet opt-in installé
(forge-mvc-audit).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_audit")

from cli._support.optin_migrations import (
    STATUS_OK,
    STATUS_WARN,
    init_optin_migrations,
    iter_migration_resources,
)

_PKG = "forge_mvc_audit"
_LABEL = "Audit"


def test_iter_migration_resources_rend_des_sql():
    resources = list(iter_migration_resources(_PKG))
    assert resources, "le paquet audit doit embarquer au moins une migration .sql"
    for name, content in resources:
        assert name.endswith(".sql")
        assert isinstance(content, bytes) and content


def test_refuse_hors_projet_forge(tmp_path: Path):
    # Pas de dossier mvc/ : ce n'est pas un projet Forge.
    assert init_optin_migrations(_PKG, _LABEL, tmp_path) == 1


def test_copie_puis_idempotence(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    (tmp_path / "mvc").mkdir()
    assert init_optin_migrations(_PKG, _LABEL, tmp_path) == 0
    out = capsys.readouterr().out
    assert f"{STATUS_OK} Migration {_LABEL} copiée" in out
    migrations = tmp_path / "mvc" / "migrations"
    copied = sorted(p.name for p in migrations.glob("*.sql"))
    assert copied, "au moins un .sql doit être copié"

    # Deuxième passage : identique, signalé OK, pas de nouvelle copie.
    assert init_optin_migrations(_PKG, _LABEL, tmp_path) == 0
    out2 = capsys.readouterr().out
    assert "déjà présente (identique)" in out2


def test_fichier_different_non_ecrase(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    (tmp_path / "mvc" / "migrations").mkdir(parents=True)
    name = next(iter(iter_migration_resources(_PKG)))[0]
    cible = tmp_path / "mvc" / "migrations" / name
    cible.write_text("-- contenu utilisateur", encoding="utf-8")

    assert init_optin_migrations(_PKG, _LABEL, tmp_path) == 0
    out = capsys.readouterr().out
    assert f"{STATUS_WARN} mvc/migrations/{name} existe et diffère" in out
    assert cible.read_text(encoding="utf-8") == "-- contenu utilisateur", (
        "un fichier existant au contenu différent ne doit jamais être écrasé"
    )
