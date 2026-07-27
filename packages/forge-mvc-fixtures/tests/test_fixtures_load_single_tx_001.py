"""FIXTURES-LOAD-SINGLE-TX-001 (ADR-074/078) : chargement en transaction unique.

`fixtures:load --run` exécutait chaque instruction sur sa propre connexion.
Deux conséquences, mesurées avant correctif :

- un échec à mi-parcours laissait la base **à moitié peuplée**, sans rien pour
  revenir en arrière (un fichier de deux INSERT suivi d'un fichier fautif
  laissait les deux lignes) ;
- `--no-fk-checks` était **sans effet**. La désactivation des contraintes est
  une variable de SESSION, donc propre à une connexion : émise hors
  transaction, elle s'appliquait à une connexion aussitôt rendue au pool, et
  les insertions suivantes repartaient sur des connexions où les contraintes
  étaient toujours actives. Rien ne le signalait.

Le chargement suit désormais le modèle de la purge (F52-bis) : une transaction,
une connexion, `tx` propagé jusqu'aux fixtures Python.
"""
from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from forge_mvc_fixtures.cli.load import main


@pytest.fixture(autouse=True)
def _fake_transaction() -> None:
    """Neutralise le faux `transaction()` autouse du conftest du paquet.

    Il existe parce que les tests unitaires n'ouvrent aucune base. Ce module-ci
    en ouvre une vraie, sur SQLite : c'est précisément le comportement
    transactionnel qu'il vérifie, donc il lui faut la vraie transaction.
    """
    return None


@pytest.fixture()
def projet(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Un projet minimal, sur une base SQLite jetable."""
    from core.database import backend as backend_module

    database = tmp_path / "fixtures.sqlite3"
    connection = sqlite3.connect(database)
    connection.execute("CREATE TABLE villes (id INTEGER PRIMARY KEY, nom TEXT NOT NULL)")
    connection.commit()
    connection.close()

    monkeypatch.setenv("DB_BACKEND", "sqlite")
    monkeypatch.setenv("DB_NAME", str(database))
    monkeypatch.setenv("APP_ENV", "dev")
    backend_module.reset_backend()
    monkeypatch.chdir(tmp_path)
    (tmp_path / "mvc" / "fixtures").mkdir(parents=True)

    try:
        yield tmp_path
    finally:
        backend_module.reset_backend()


def _rows(projet: Path) -> list[tuple[int, str]]:
    connection = sqlite3.connect(projet / "fixtures.sqlite3")
    try:
        return connection.execute("SELECT id, nom FROM villes ORDER BY id").fetchall()
    finally:
        connection.close()


def _write(projet: Path, name: str, content: str) -> None:
    (projet / "mvc" / "fixtures" / name).write_text(content, encoding="utf-8")


# ── Le cœur du ticket : un échec annule tout ─────────────────────────────────

def test_un_echec_annule_les_insertions_deja_faites(projet: Path) -> None:
    _write(projet, "01_villes.sql",
           "INSERT INTO villes (id, nom) VALUES (1, 'Québec');\n"
           "INSERT INTO villes (id, nom) VALUES (2, 'Montréal');\n")
    _write(projet, "02_casse.sql",
           "INSERT INTO villes (id, colonne_absente) VALUES (3, 'x');\n")

    assert main(["--run", "--force"]) == 1
    assert _rows(projet) == [], "le chargement échoué doit laisser la base intacte"


def test_un_chargement_reussi_est_bien_valide(projet: Path) -> None:
    """Contrôle inverse : la transaction est bien validée quand tout passe."""
    _write(projet, "01_villes.sql",
           "INSERT INTO villes (id, nom) VALUES (1, 'Québec');\n"
           "INSERT INTO villes (id, nom) VALUES (2, 'Montréal');\n")

    assert main(["--run", "--force"]) == 0
    assert _rows(projet) == [(1, "Québec"), (2, "Montréal")]


def test_l_echec_d_une_fixture_python_annule_le_sql_precedent(projet: Path) -> None:
    _write(projet, "01_villes.sql", "INSERT INTO villes (id, nom) VALUES (1, 'Québec');\n")
    _write(projet, "02_boom.py",
           "from forge_mvc_fixtures import Fixture\n\n\n"
           "class BoomFixture(Fixture):\n"
           "    tables = ('villes',)\n\n"
           "    def load(self, *, tx=None):\n"
           "        raise RuntimeError('échec volontaire')\n")

    assert main(["--run", "--force"]) == 1
    assert _rows(projet) == []


# ── Le contrat `tx` propagé aux fixtures Python ──────────────────────────────

def test_la_fixture_python_recoit_la_transaction(projet: Path) -> None:
    """`tx` est passé, et une écriture qui le propage est bien validée."""
    _write(projet, "01_compte.py",
           "from forge_mvc_fixtures import Fixture\n"
           "from core.database import db\n\n\n"
           "class CompteFixture(Fixture):\n"
           "    tables = ('villes',)\n\n"
           "    def load(self, *, tx=None):\n"
           "        assert tx is not None, 'fixtures:load doit fournir tx'\n"
           "        db.execute(\"INSERT INTO villes (id, nom) VALUES (7, 'Laval')\", tx=tx)\n")

    assert main(["--run", "--force"]) == 0
    assert _rows(projet) == [(7, "Laval")]


def test_une_fixture_sans_parametre_tx_est_refusee_avec_un_message_clair(
    projet: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    """Rupture d'API expliquée, jamais un TypeError brut ni un repli silencieux."""
    _write(projet, "01_ancienne.py",
           "from forge_mvc_fixtures import Fixture\n\n\n"
           "class AncienneFixture(Fixture):\n"
           "    tables = ('villes',)\n\n"
           "    def load(self):\n"
           "        pass\n")

    assert main(["--run", "--force"]) == 1
    message = capsys.readouterr().err
    assert "sans paramètre 'tx'" in message
    assert "def load(self, *, tx=None)" in message


def test_une_fixture_a_kwargs_est_acceptee(projet: Path) -> None:
    """`**kwargs` accepte `tx` : inutile de le refuser."""
    _write(projet, "01_kwargs.py",
           "from forge_mvc_fixtures import Fixture\n"
           "from core.database import db\n\n\n"
           "class KwargsFixture(Fixture):\n"
           "    tables = ('villes',)\n\n"
           "    def load(self, **kwargs):\n"
           "        db.execute(\"INSERT INTO villes (id, nom) VALUES (9, 'Gaspé')\", "
           "tx=kwargs.get('tx'))\n")

    assert main(["--run", "--force"]) == 0
    assert _rows(projet) == [(9, "Gaspé")]


# ── Le contrat de base reste symétrique de la purge ──────────────────────────

def test_le_contrat_de_base_declare_tx_comme_la_purge() -> None:
    import inspect

    from forge_mvc_fixtures import Fixture

    for method in (Fixture.load, Fixture.purge):
        parameters = inspect.signature(method).parameters
        assert "tx" in parameters, f"{method.__name__} doit accepter tx"
        assert parameters["tx"].kind is inspect.Parameter.KEYWORD_ONLY
