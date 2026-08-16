"""Intégration réelle de forge fixtures:purge sur les trois serveurs (ADR-074).

Prouve que le chemin --run vide réellement les tables ciblées : on charge des
lignes, on purge, on vérifie que la table est vide et que le schéma survit.

Comme `fixtures:load`, la purge n'était exercée que contre MariaDB, sa table de
test étant créée par une DDL écrite en dur dans ce dialecte
(`FIXTURES-LOAD-PURGE-TROIS-SERVEURS-001`). Les deux commandes sont converties
ensemble : n'en traiter qu'une aurait laissé la moitié du chemin non exercée,
alors qu'elles partagent le levier de contraintes du dialecte.

Le relevé est rassurant, et il faut le dire : aucun défaut trouvé sur les trois
moteurs.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.db

pytest.importorskip("forge_mvc_fixtures")

from core.database.table_ddl import Column, TableDefinition
from forge_mvc_testing.real_db import tables_temporaires

from forge_mvc_fixtures.cli.load import load_fixtures
from forge_mvc_fixtures.cli.purge import purge_fixtures


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


@pytest.fixture()
def related_tables(real_db):
    """Deux tables liées par une FK (parent référencé par enfant)."""
    from core.database import db

    db.execute("DROP TABLE IF EXISTS child", ())
    db.execute("DROP TABLE IF EXISTS parent", ())
    db.execute(
        "CREATE TABLE parent (Id INT AUTO_INCREMENT PRIMARY KEY, nom VARCHAR(50) NOT NULL)",
        (),
    )
    db.execute(
        "CREATE TABLE child (Id INT AUTO_INCREMENT PRIMARY KEY, parent_id INT NOT NULL, "
        "CONSTRAINT fk_child_parent FOREIGN KEY (parent_id) REFERENCES parent (Id))",
        (),
    )
    yield db
    db.execute("DROP TABLE IF EXISTS child", ())
    db.execute("DROP TABLE IF EXISTS parent", ())


def test_purge_load_idempotent_multi_table_callable(related_tables, tmp_path: Path) -> None:
    """F52-bis : un callable multi-tables liées est rejouable sur pool (DB_POOL_SIZE=2).

    ``tables`` est déclaré dans l'ordre « défavorable » (enfant avant parent) :
    ``reversed()`` supprimerait le parent d'abord, ce qui violerait la FK. Seule
    la désactivation FK dans une transaction unique (F52-bis) rend le cycle
    rejouable ; l'encadrement émis sur le pool (avant 1373b228) échouait ici.
    """
    db = related_tables
    fixtures = tmp_path / "mvc" / "fixtures"
    fixtures.mkdir(parents=True, exist_ok=True)
    (fixtures / "referentiel.py").write_text(
        "from forge_mvc_fixtures import Fixture\n"
        "from core.database import db\n"
        "class ReferentielFixture(Fixture):\n"
        "    tables = ('child', 'parent')\n"  # ordre défavorable exprès
        # FIXTURES-LOAD-SINGLE-TX-001 : le chargement tient dans une
        # transaction unique et fournit `tx`, comme la purge. Une fixture qui
        # ne le propage pas écrirait hors de cette transaction.
        "    def load(self, *, tx=None):\n"
        "        db.execute(\"INSERT INTO parent (nom) VALUES ('P')\", tx=tx)\n"
        "        pid = db.fetch_all('SELECT Id FROM parent', tx=tx)[0]['Id']\n"
        "        db.execute('INSERT INTO child (parent_id) VALUES (?)', (pid,), tx=tx)\n",
        encoding="utf-8",
    )

    # Deux cycles complets : aucune erreur FK, aucun doublon, état vidé à chaque purge.
    for _ in range(2):
        assert load_fixtures(tmp_path, run=True, force=False, env="dev") == 0
        assert len(db.fetch_all("SELECT Id FROM child", ())) == 1
        assert len(db.fetch_all("SELECT Id FROM parent", ())) == 1
        assert purge_fixtures(tmp_path, run=True, force=False, env="dev") == 0
        assert db.fetch_all("SELECT Id FROM child", ()) == []
        assert db.fetch_all("SELECT Id FROM parent", ()) == []
