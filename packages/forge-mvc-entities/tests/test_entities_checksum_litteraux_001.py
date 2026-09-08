"""`ENTITIES-CHECKSUM-LITTERAUX-001` — deux valeurs différentes, deux empreintes.

L'empreinte d'étape normalisait les blancs de toute l'instruction, littéraux
compris. Mesuré :

    INSERT INTO demo (value) VALUES ('a  b')
    INSERT INTO demo (value) VALUES ('a b')

avaient la **même** empreinte, alors qu'elles n'écrivent pas la même valeur.

Une reprise de migration pouvait donc tenir pour déjà exécutée une étape dont un
littéral avait changé, et laisser la base dans un état que le fichier ne décrit
plus. Un outil de migration doit être particulièrement conservateur quand il
décide qu'une étape a eu lieu.

L'intention d'origine reste : reformater ou recommenter une instruction déjà
appliquée ne doit pas faire refuser la reprise. Elle s'arrête simplement où
commence le texte.
"""
from __future__ import annotations

import pytest

pytest.importorskip("forge_mvc_entities")

from forge_mvc_entities.migrations import _statement_checksum  # noqa: E402


class TestUnLitteralQuiChangeChangeLEmpreinte:
    """Le défaut mesuré."""

    @pytest.mark.parametrize(
        ("un", "deux"),
        [
            (
                "INSERT INTO demo (value) VALUES ('a  b')",
                "INSERT INTO demo (value) VALUES ('a b')",
            ),
            ("UPDATE t SET v = 'x  y'", "UPDATE t SET v = 'x y'"),
            ("INSERT INTO t VALUES ('a\nb')", "INSERT INTO t VALUES ('a b')"),
            ("INSERT INTO t VALUES ('  a')", "INSERT INTO t VALUES ('a')"),
        ],
        ids=["deux-espaces", "update", "retour-ligne", "espace-en-tete"],
    )
    def test_deux_valeurs_distinctes_ont_deux_empreintes(self, un: str, deux: str) -> None:
        assert _statement_checksum(un) != _statement_checksum(deux)


class TestUnReformatageDuCodeNeChangeRien:
    """L'intention d'origine, qu'il ne fallait pas perdre en corrigeant."""

    @pytest.mark.parametrize(
        ("un", "deux"),
        [
            ("SELECT   1   FROM   t", "SELECT 1 FROM t"),
            ("CREATE TABLE t (\n  a INT\n)", "CREATE TABLE t ( a INT )"),
            ("SELECT 'x' -- note", "SELECT   'x'"),
            ("SELECT /* bloc */ 1", "SELECT 1"),
        ],
        ids=["espaces", "indentation", "commentaire-ligne", "commentaire-bloc"],
    )
    def test_le_reformatage_garde_la_meme_empreinte(self, un: str, deux: str) -> None:
        assert _statement_checksum(un) == _statement_checksum(deux)

    def test_une_apostrophe_echappee_reste_du_contenu(self) -> None:
        """`''` est un caractère de la valeur, pas une fin de chaîne."""
        un = "INSERT INTO t VALUES ('c''est  ici')"
        deux = "INSERT INTO t VALUES ('c''est ici')"

        assert _statement_checksum(un) != _statement_checksum(deux)


class TestLEmpreinteResteUtilisable:
    """Une empreinte doit rester stable et de forme constante."""

    def test_elle_est_stable_d_un_appel_a_l_autre(self) -> None:
        sql = "INSERT INTO t VALUES ('a')"

        assert _statement_checksum(sql) == _statement_checksum(sql)

    def test_elle_fait_soixante_quatre_caracteres(self) -> None:
        """La colonne du journal de reprise est un `char(64)`."""
        assert len(_statement_checksum("SELECT 1")) == 64
