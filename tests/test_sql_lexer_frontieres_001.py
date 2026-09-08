"""`SQL-MASK-LITERALS-001`, `SQL-NORMALIZE-WHITESPACE-001` — le code n'est pas le texte.

Deux opt-ins lisaient du SQL avec des motifs appliqués au texte brut, et
prenaient le contenu d'une chaîne pour du code :

- la purge de fixtures collectait `users` depuis
  `INSERT INTO logs (message) VALUES ('INSERT INTO users')`, et bâtissait ses
  `DELETE FROM` sur cette liste ;
- l'empreinte d'étape des migrations normalisait les blancs de toute
  l'instruction, si bien que `'a  b'` et `'a b'` avaient le même checksum.

Le cœur portait déjà la machine à états qui distingue code, chaînes et
commentaires (ADR-079), mais elle ne servait qu'à découper les instructions.
Elle sert maintenant aussi à masquer et à normaliser, ce qui évite qu'une
seconde réponse à la même question soit écrite ailleurs et finisse en retard.
"""
from __future__ import annotations

import pytest

from core.database.sql_script import (
    mask_sql_literals,
    normalize_sql_whitespace,
    split_sql_statements,
)


class TestMasquageDesLitteraux:
    """Ce qui est dans une chaîne ou un commentaire cesse d'être du code."""

    @pytest.mark.parametrize(
        ("sql", "absent"),
        [
            ("INSERT INTO logs (m) VALUES ('INSERT INTO users')", "users"),
            ("SELECT 1 -- INSERT INTO secret", "secret"),
            ("SELECT 1 /* INSERT INTO secret */ FROM t", "secret"),
            ("INSERT INTO a VALUES ('c''est INSERT INTO b')", "b'"),
        ],
        ids=["chaine", "commentaire-ligne", "commentaire-bloc", "apostrophe-echappee"],
    )
    def test_le_contenu_cite_disparait(self, sql: str, absent: str) -> None:
        assert absent not in mask_sql_literals(sql)

    def test_le_code_survit(self, sql: str = "INSERT INTO logs (m) VALUES ('x')") -> None:
        """Un masquage qui effacerait tout ne servirait à rien non plus."""
        assert "INSERT INTO logs" in mask_sql_literals(sql)

    @pytest.mark.parametrize(
        "sql",
        [
            "INSERT INTO logs (m) VALUES ('INSERT INTO users')",
            "SELECT 1 -- note\nSELECT 2",
            "SELECT /* x */ 1",
            "SELECT 'a''b'",
            "",
        ],
    )
    def test_les_positions_sont_preservees(self, sql: str) -> None:
        """Un motif appliqué au masque doit pointer le même endroit que la source."""
        assert len(mask_sql_literals(sql)) == len(sql)


class TestNormalisationDesBlancs:
    """Le reformatage du code est ignoré, celui du texte ne l'est pas."""

    @pytest.mark.parametrize(
        ("un", "deux"),
        [
            ("SELECT   1   FROM   t", "SELECT 1 FROM t"),
            ("SELECT 'x' -- note", "SELECT   'x'"),
            ("SELECT\n  'a''b  c'", "SELECT 'a''b  c'"),
            ("SELECT /* bloc */ 1", "SELECT 1"),
        ],
        ids=["espaces", "commentaire-ligne", "retour-ligne", "commentaire-bloc"],
    )
    def test_un_reformatage_du_code_ne_change_rien(self, un: str, deux: str) -> None:
        assert normalize_sql_whitespace(un) == normalize_sql_whitespace(deux)

    @pytest.mark.parametrize(
        ("un", "deux"),
        [
            ("INSERT INTO d (v) VALUES ('a  b')", "INSERT INTO d (v) VALUES ('a b')"),
            ("SELECT 'x  y'", "SELECT 'x y'"),
            ("SELECT 'a\nb'", "SELECT 'a b'"),
        ],
        ids=["deux-espaces", "chaine-simple", "retour-dans-chaine"],
    )
    def test_un_changement_de_litteral_change_tout(self, un: str, deux: str) -> None:
        """Le défaut mesuré : ces paires avaient la même empreinte."""
        assert normalize_sql_whitespace(un) != normalize_sql_whitespace(deux)


class TestLaMachineEstPartagee:
    """Les trois fonctions doivent lire le SQL de la même façon."""

    SQL = "INSERT INTO a VALUES ('x; -- y'); SELECT 1 -- vrai commentaire\n"

    def test_le_decoupeur_ignore_le_point_virgule_cite(self) -> None:
        assert len(split_sql_statements(self.SQL)) == 2

    def test_le_masque_ignore_le_commentaire_cite(self) -> None:
        """`-- y` est dans une chaîne : ce n'est pas un commentaire."""
        masque = mask_sql_literals(self.SQL)

        assert "INSERT INTO a" in masque
        assert "SELECT 1" in masque

    def test_la_normalisation_garde_la_chaine_intacte(self) -> None:
        assert "'x; -- y'" in normalize_sql_whitespace(self.SQL)
