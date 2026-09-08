"""`POSTGRES-TRANSLATE-CONTEXTES-001` — un « ? » hors du code n'est pas un paramètre.

La traduction ne connaissait que les littéraux entre apostrophes. Elle
introduisait donc des marqueurs là où le « ? » n'en était pas un :

    SELECT ? /* pourquoi ? */   ->  SELECT %s /* pourquoi %s */
    SELECT $$?$$                ->  SELECT $$%s$$
    SELECT ? -- et ?            ->  SELECT %s -- et %s
    SELECT "col?" FROM t        ->  SELECT "col%s" FROM t

Selon le pilote, cela donne un mauvais comptage des paramètres ou un SQL altéré.
Les requêtes engendrées par Forge, simples, passaient ; du SQL applicatif
parfaitement valide échouait. C'est un défaut de compatibilité pour un framework
qui laisse écrire du SQL (principe 5).
"""
from __future__ import annotations

import pytest

pytest.importorskip("forge_mvc_postgres")

from forge_mvc_postgres.translate import translate_placeholders  # noqa: E402


class TestLesContextesQuiNeSontPasDuCode:
    """Quatre contextes, tous préservés."""

    @pytest.mark.parametrize(
        ("sql", "attendu"),
        [
            ("SELECT ? /* pourquoi ? */", "SELECT %s /* pourquoi ? */"),
            ("SELECT ? -- et ?", "SELECT %s -- et ?"),
            ('SELECT "col?" FROM t', 'SELECT "col?" FROM t'),
            ("SELECT $$?$$", "SELECT $$?$$"),
            ("SELECT $tag$ ? $tag$", "SELECT $tag$ ? $tag$"),
            ("SELECT 'a?b'", "SELECT 'a?b'"),
            ("SELECT 'c''est ?'", "SELECT 'c''est ?'"),
            ('SELECT "col""x?" FROM t', 'SELECT "col""x?" FROM t'),
        ],
        ids=["bloc", "ligne", "identifiant", "dollar", "dollar-etiquette",
             "chaine", "apostrophe-echappee", "guillemet-echappe"],
    )
    def test_le_point_d_interrogation_y_reste_intact(self, sql: str, attendu: str) -> None:
        assert translate_placeholders(sql) == attendu

    def test_un_commentaire_de_bloc_imbrique(self) -> None:
        """PostgreSQL admet l'imbrication, contrairement à la plupart des moteurs."""
        sql = "SELECT ? /* a /* b ? */ c ? */ FROM t"

        assert translate_placeholders(sql) == "SELECT %s /* a /* b ? */ c ? */ FROM t"


class TestLesVraisParametres:
    """Une traduction qui ne traduirait plus rien ne servirait à rien non plus."""

    @pytest.mark.parametrize(
        ("sql", "attendu"),
        [
            ("SELECT ?", "SELECT %s"),
            ("INSERT INTO t VALUES (?, ?)", "INSERT INTO t VALUES (%s, %s)"),
            ("SELECT * FROM t WHERE a=? AND b=?", "SELECT * FROM t WHERE a=%s AND b=%s"),
            ("UPDATE t SET a=? WHERE id=?", "UPDATE t SET a=%s WHERE id=%s"),
        ],
    )
    def test_ils_sont_traduits(self, sql: str, attendu: str) -> None:
        assert translate_placeholders(sql) == attendu

    def test_un_point_d_interrogation_final_est_un_parametre(self) -> None:
        """`"" in "|&-#"` vaut True : sans garde, un « ? » final passait pour un opérateur."""
        assert translate_placeholders("SELECT ?") == "SELECT %s"


class TestLOperateurQuiCommenceParUnPointDInterrogation:
    """La règle écrite, plutôt qu'une devinette sur la grammaire."""

    @pytest.mark.parametrize(
        "sql",
        ["SELECT d ?| a", "SELECT d ?& a", "SELECT a ?- b", "SELECT a ?# b"],
        ids=["jsonb-ou", "jsonb-et", "geometrique", "diese"],
    )
    def test_un_operateur_colle_reste_intact(self, sql: str) -> None:
        assert translate_placeholders(sql) == sql

    def test_le_double_vaut_un_point_d_interrogation_litteral(self) -> None:
        """L'échappement que psycopg emploie déjà dans le même but."""
        assert translate_placeholders("SELECT d ?? 'k'") == "SELECT d ? 'k'"


class TestLeDoublementDesPourcents:
    """psycopg formate la requête entière : tout « % » littéral se double."""

    @pytest.mark.parametrize(
        ("sql", "attendu"),
        [
            ("SELECT 100%", "SELECT 100%%"),
            ("SELECT 'a%b'", "SELECT 'a%%b'"),
            ("SELECT ? -- 50%", "SELECT %s -- 50%%"),
            ("SELECT $$a%b$$", "SELECT $$a%%b$$"),
            ('SELECT "c%l"', 'SELECT "c%%l"'),
        ],
        ids=["code", "chaine", "commentaire", "dollar", "identifiant"],
    )
    def test_partout(self, sql: str, attendu: str) -> None:
        assert translate_placeholders(sql) == attendu


class TestCeQuiNeDoitPasLever:
    """Ce module traduit, il ne valide pas."""

    @pytest.mark.parametrize(
        "sql",
        ["SELECT 'jamais referme", 'SELECT "jamais referme', "SELECT $$jamais", "SELECT /* jamais"],
    )
    def test_un_delimiteur_non_referme_ne_leve_pas(self, sql: str) -> None:
        """Un SQL invalide doit être refusé par le serveur, avec son message à lui."""
        assert isinstance(translate_placeholders(sql), str)

    def test_un_parametre_numerote_n_ouvre_pas_un_litteral(self) -> None:
        """`$1$` doit rester du code : une étiquette ne commence pas par un chiffre."""
        assert translate_placeholders("SELECT $1$ ? $1$") == "SELECT $1$ %s $1$"
