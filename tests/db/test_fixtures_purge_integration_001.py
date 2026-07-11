"""Intégration réelle de forge fixtures:purge contre MariaDB (ADR-074).

Prouve que le chemin --run vide réellement les tables ciblées : on charge des
lignes, on purge, on vérifie que la table est vide et que le schéma survit.

Marqués `db` : sautés en local sans base, imposés en CI (FORGE_REQUIRE_DB=1).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.db

pytest.importorskip("forge_mvc_fixtures")

from forge_mvc_fixtures.cli.load import load_fixtures
from forge_mvc_fixtures.cli.purge import purge_fixtures


@pytest.fixture()
def ville_table(real_db):
    from core.database import db

    db.execute("DROP TABLE IF EXISTS ville", ())
    db.execute(
        "CREATE TABLE ville (id INT AUTO_INCREMENT PRIMARY KEY, nom VARCHAR(100) NOT NULL)",
        (),
    )
    yield db
    db.execute("DROP TABLE IF EXISTS ville", ())


def _write_fixture(root: Path, name: str, sql: str) -> None:
    fixtures = root / "mvc" / "fixtures"
    fixtures.mkdir(parents=True, exist_ok=True)
    (fixtures / name).write_text(sql, encoding="utf-8")


def test_purge_empties_targeted_table(ville_table, tmp_path: Path) -> None:
    db = ville_table
    _write_fixture(
        tmp_path, "01_villes.sql",
        "INSERT INTO ville (nom) VALUES ('Lyon');\nINSERT INTO ville (nom) VALUES ('Nice');",
    )
    assert load_fixtures(tmp_path, run=True, force=False, env="dev") == 0
    assert len(db.fetch_all("SELECT id FROM ville", ())) == 2

    assert purge_fixtures(tmp_path, run=True, force=False, env="dev") == 0
    assert db.fetch_all("SELECT id FROM ville", ()) == []
    # Le schéma survit : la table existe toujours (purge de données, pas DROP).
    db.execute("INSERT INTO ville (nom) VALUES ('Paris')", ())
    assert len(db.fetch_all("SELECT id FROM ville", ())) == 1


def test_display_only_purges_nothing(ville_table, tmp_path: Path) -> None:
    db = ville_table
    _write_fixture(tmp_path, "01_villes.sql", "INSERT INTO ville (nom) VALUES ('Lyon');")
    load_fixtures(tmp_path, run=True, force=False, env="dev")
    assert purge_fixtures(tmp_path, run=False, force=False, env="dev") == 0
    assert len(db.fetch_all("SELECT id FROM ville", ())) == 1
