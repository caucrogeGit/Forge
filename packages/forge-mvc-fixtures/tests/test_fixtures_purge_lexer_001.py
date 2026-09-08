"""`FIXTURES-PURGE-LEXER-001` — le plan de purge ne vise que ce que les fixtures écrivent.

`collect_target_tables()` cherchait `INSERT INTO` dans le texte brut, en se
contentant de retirer les lignes commençant par `--`. Une table citée **dans une
chaîne** entrait donc dans le plan :

    INSERT INTO logs (message) VALUES ('INSERT INTO users');

rendait `['logs', 'users']`. La purge bâtit ses `DELETE FROM` sur cette liste :
elle visait une table étrangère aux écritures réelles des fixtures.

Les garde-fous d'autorisation n'y changent rien. Ils autorisent très
correctement la mauvaise suppression : un plan faux reste faux quand il est
confirmé.

Le même relevé sert à l'ordre de chargement, dans `load.py`, et y produisait la
même erreur sur les tables lues comme sur les tables écrites.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_fixtures")

from forge_mvc_fixtures.cli.load import (  # noqa: E402
    _referenced_tables_of_file,
    _tables_of_file,
)
from forge_mvc_fixtures.cli.purge import collect_target_tables  # noqa: E402


def _fixture(tmp_path: Path, sql: str) -> Path:
    chemin = tmp_path / "demo.sql"
    chemin.write_text(sql, encoding="utf-8")
    return chemin


class TestUneTableCiteeNEstPasUneTableEcrite:
    """Le cas mesuré, et ses variantes."""

    @pytest.mark.parametrize(
        "sql",
        [
            "INSERT INTO logs (m) VALUES ('INSERT INTO users');",
            "INSERT INTO logs (m) VALUES ('rapport : INSERT INTO users hier');",
            "INSERT INTO logs (m) VALUES ('c''est INSERT INTO users');",
        ],
        ids=["simple", "au-milieu", "apostrophe-echappee"],
    )
    def test_la_table_citee_reste_hors_du_plan(self, sql: str, tmp_path: Path) -> None:
        assert collect_target_tables([_fixture(tmp_path, sql)]) == ["logs"]

    def test_une_table_en_commentaire_reste_hors_du_plan(self, tmp_path: Path) -> None:
        """Le retrait des lignes `--` ne couvrait pas les commentaires de bloc."""
        sql = "/* INSERT INTO users */\nINSERT INTO logs (m) VALUES ('x');"

        assert collect_target_tables([_fixture(tmp_path, sql)]) == ["logs"]

    def test_un_commentaire_en_fin_de_ligne_non_plus(self, tmp_path: Path) -> None:
        sql = "INSERT INTO logs (m) VALUES ('x'); -- INSERT INTO users"

        assert collect_target_tables([_fixture(tmp_path, sql)]) == ["logs"]


class TestLesVraiesEcrituresSontToujoursVues:
    """Un relevé qui ne verrait plus rien ne protégerait rien non plus."""

    def test_plusieurs_tables_dans_l_ordre_d_apparition(self, tmp_path: Path) -> None:
        sql = (
            "INSERT INTO users (n) VALUES ('a');\n"
            "INSERT INTO logs (m) VALUES ('b');\n"
            "INSERT INTO users (n) VALUES ('c');\n"
        )

        assert collect_target_tables([_fixture(tmp_path, sql)]) == ["users", "logs"]

    def test_les_backticks_sont_toujours_acceptes(self, tmp_path: Path) -> None:
        sql = "INSERT INTO `logs` (m) VALUES ('x');"

        assert collect_target_tables([_fixture(tmp_path, sql)]) == ["logs"]


class TestLOrdreDeChargementLitLeMemeCode:
    """`load.py` faisait le même relevé, et se trompait pareil."""

    def test_les_tables_ecrites_ignorent_les_chaines(self, tmp_path: Path) -> None:
        chemin = _fixture(tmp_path, "INSERT INTO logs (m) VALUES ('INSERT INTO users');")

        assert _tables_of_file(chemin) == {"logs"}

    def test_les_tables_lues_ignorent_les_chaines(self, tmp_path: Path) -> None:
        """Une dépendance d'ordonnancement tirée d'une chaîne fausserait le tri."""
        chemin = _fixture(
            tmp_path, "INSERT INTO logs (m) VALUES ('vu dans FROM users hier');"
        )

        assert "users" not in _referenced_tables_of_file(chemin)

    def test_une_vraie_sous_requete_reste_une_dependance(self, tmp_path: Path) -> None:
        chemin = _fixture(
            tmp_path,
            "INSERT INTO posts (uid) VALUES ((SELECT id FROM users WHERE n='a'));",
        )

        assert "users" in _referenced_tables_of_file(chemin)
