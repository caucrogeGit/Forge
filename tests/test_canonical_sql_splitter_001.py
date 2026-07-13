"""Découpeur SQL canonique du cœur (CANONICAL-SQL-SPLITTER-001, ADR-079).

Un seul découpeur robuste, conscient des chaînes ('...' avec ''), des
commentaires de ligne (--) et de bloc (/* */). Fiabilise les retours terrain
012 (apostrophe) et 021 (commentaire contenant un ;).
"""
from __future__ import annotations

import pytest

from core.database.sql_script import split_sql_statements

pytestmark = pytest.mark.meta


class TestBasics:
    def test_simple_split(self) -> None:
        assert split_sql_statements("SELECT 1; SELECT 2;") == ["SELECT 1", "SELECT 2"]

    def test_trailing_without_semicolon(self) -> None:
        assert split_sql_statements("SELECT 1") == ["SELECT 1"]

    def test_empty(self) -> None:
        assert split_sql_statements("") == []

    def test_only_whitespace_and_semicolons(self) -> None:
        assert split_sql_statements("  ;\n ; \t") == []


class TestStringLiterals:
    def test_semicolon_inside_string_is_not_a_separator(self) -> None:
        assert split_sql_statements("INSERT INTO t VALUES ('a;b'); INSERT INTO t VALUES ('c')") == [
            "INSERT INTO t VALUES ('a;b')",
            "INSERT INTO t VALUES ('c')",
        ]

    def test_escaped_doubled_quote(self) -> None:
        assert split_sql_statements("INSERT INTO t VALUES ('l''ecole')") == [
            "INSERT INTO t VALUES ('l''ecole')"
        ]

    def test_double_dash_inside_string_is_not_a_comment(self) -> None:
        # Retour 012 : le -- dans une chaîne ne doit pas ouvrir un commentaire.
        assert split_sql_statements("INSERT INTO t VALUES ('a -- b ; c'); SELECT 2") == [
            "INSERT INTO t VALUES ('a -- b ; c')",
            "SELECT 2",
        ]


class TestLineComments:
    def test_semicolon_in_line_comment_is_not_a_separator(self) -> None:
        # Retour 021 : le ; du commentaire ne coupe pas l'instruction.
        assert split_sql_statements(
            "-- ajoute la colonne ; attention\nALTER TABLE t ADD COLUMN x INT;"
        ) == ["ALTER TABLE t ADD COLUMN x INT"]

    def test_inline_line_comment_stripped(self) -> None:
        assert split_sql_statements("SELECT 1 -- note ; ici\n; SELECT 2") == [
            "SELECT 1",
            "SELECT 2",
        ]

    def test_comment_only_is_dropped(self) -> None:
        assert split_sql_statements("-- rien que du commentaire ;\n  ") == []


class TestBlockComments:
    def test_semicolon_in_block_comment_is_not_a_separator(self) -> None:
        assert split_sql_statements("/* bloc ; ici */ SELECT 1; SELECT 2") == [
            "SELECT 1",
            "SELECT 2",
        ]

    def test_block_comment_becomes_token_separator(self) -> None:
        # Le bloc retiré laisse une espace : les tokens ne se collent pas.
        assert split_sql_statements("SELECT/* x */1") == ["SELECT 1"]

    def test_multiline_block_comment(self) -> None:
        assert split_sql_statements("/* ligne 1\nligne 2 ; */ SELECT 1;") == ["SELECT 1"]
