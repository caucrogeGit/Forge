"""Intégration réelle de forge fixtures:load contre MariaDB (ADR-074).

Prouve que le chemin --run insère réellement les lignes des fixtures dans la base
active via core.database.db (et pas seulement via un db.execute mocké). Une table
jetable `ville` est créée, un fichier de fixtures est chargé, les lignes sont
vérifiées.

Marqués `db` : sautés en local sans base, imposés en CI (FORGE_REQUIRE_DB=1).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.db

pytest.importorskip("forge_mvc_fixtures")

from forge_mvc_fixtures.cli.load import load_fixtures


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


def test_run_inserts_rows(ville_table, tmp_path: Path) -> None:
    db = ville_table
    _write_fixture(
        tmp_path,
        "01_villes.sql",
        "-- villes de départ\n"
        "INSERT INTO ville (nom) VALUES ('Lyon');\n"
        "INSERT INTO ville (nom) VALUES ('l''Haÿ-les-Roses');\n",
    )
    rc = load_fixtures(tmp_path, run=True, force=False, env="dev")
    assert rc == 0
    rows = db.fetch_all("SELECT nom FROM ville ORDER BY id", ())
    assert [r["nom"] for r in rows] == ["Lyon", "l'Haÿ-les-Roses"]


def test_display_only_inserts_nothing(ville_table, tmp_path: Path) -> None:
    db = ville_table
    _write_fixture(tmp_path, "01_villes.sql", "INSERT INTO ville (nom) VALUES ('Lyon');")
    rc = load_fixtures(tmp_path, run=False, force=False, env="dev")
    assert rc == 0
    assert db.fetch_all("SELECT nom FROM ville", ()) == []
