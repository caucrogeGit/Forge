"""Intégration réelle de forge fixtures:load sur les trois serveurs (ADR-074).

Prouve que le chemin --run insère réellement les lignes des fixtures dans la base
active via core.database.db (et pas seulement via un db.execute mocké). Une table
jetable `ville` est créée, un fichier de fixtures est chargé, les lignes sont
vérifiées.

`fixtures:load` n'était exercé que contre MariaDB, sa table de test étant créée
par une DDL écrite en dur dans ce dialecte. C'est la commande principale de
l'opt-in, et la question « ce chargement se comporte-t-il pareil sur PostgreSQL »
n'avait jamais été posée à un serveur (`FIXTURES-LOAD-PURGE-TROIS-SERVEURS-001`).

Le relevé est rassurant, et il faut le dire : les trois moteurs se comportent
identiquement, apostrophe comprise. Le fichier existe pour que cela le reste.

`real_backend_db` exécute chaque test une fois par serveur, chaque cas portant
les marqueurs du sien : les trois jobs de CI sélectionnent chacun le sien sans
qu'aucun test soit écrit en triple.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.db

pytest.importorskip("forge_mvc_fixtures")

from core.database.table_ddl import Column, TableDefinition
from forge_mvc_testing.real_db import tables_temporaires

from forge_mvc_fixtures.cli.load import load_fixtures


#: FIXTURES-LOAD-PURGE-TROIS-SERVEURS-001 : la table était créée par une DDL
#: MariaDB écrite en dur (`INT AUTO_INCREMENT PRIMARY KEY`), et c'est cela seul
#: qui clouait ce fichier à un moteur. Décrite en vocabulaire Forge, sa DDL est
#: rendue par le dialecte actif, donc le même test vaut sur les trois serveurs.
VILLE = TableDefinition(
    name="ville",
    columns=[
        Column("id", "identity"),
        Column("nom", "string", length=100),
    ],
    primary_key=["id"],
)


@pytest.fixture()
def ville_table(real_backend_db: str):
    with tables_temporaires(VILLE) as db:
        yield db


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
