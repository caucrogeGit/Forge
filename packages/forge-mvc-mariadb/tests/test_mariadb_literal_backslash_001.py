"""MARIADB-LITERAL-BACKSLASH-001 : l'antislash doit être échappé (injection SQL).

MariaDB est le **seul** des quatre backends où l'antislash est un caractère
d'échappement dans les littéraux : `NO_BACKSLASH_ESCAPES` y est désactivé par
défaut. PostgreSQL (`standard_conforming_strings` à `on`), SQLite et SQL Server
le traitent comme un caractère ordinaire.

`escape_string` du cœur double la seule apostrophe, ce que prescrit la norme
SQL. Sur MariaDB, cela laissait deux trous, tous deux mesurés sur serveur réel.

**Rupture d'instruction.** `"abc\\"` rendait `'abc\'` : l'antislash échappe le
guillemet fermant, la chaîne reste ouverte, l'instruction est invalide.

**Injection SQL.** `"a\\' OR 1=1 -- "` rendait `'a\'' OR 1=1 -- '` : la chaîne
se referme et la suite devient exécutable. Vérifié, le serveur évaluait la
condition et rendait `1`.

La surface est le SQL **écrit dans des artefacts** (ADR-075) : fixtures
générées, valeurs par défaut de DDL. Le chemin de requête ordinaire n'est pas
concerné, il passe par des paramètres liés.

Le correctif appartient au dialecte MariaDB, non au cœur, qui implémente
correctement la norme pour les trois autres backends.
"""
from __future__ import annotations

import pytest

pytest.importorskip("forge_mvc_mariadb")
from forge_mvc_mariadb.dialect import MariaDBDialect  # noqa: E402

D = MariaDBDialect()


# ── Les deux défauts mesurés ─────────────────────────────────────────────────

def test_une_valeur_terminee_par_un_antislash_ne_rompt_pas_la_chaine() -> None:
    rendu = D.render_literal("abc\\")

    assert rendu == "'abc\\\\'"
    assert rendu.endswith("\\\\'"), "le guillemet fermant doit rester un guillemet"


def test_la_charge_d_injection_est_neutralisee() -> None:
    """`a\\' OR 1=1 -- ` refermait la chaîne et exécutait la suite."""
    rendu = D.render_literal("a\\' OR 1=1 -- ")

    assert rendu == "'a\\\\'' OR 1=1 -- '"


def test_un_antislash_n_est_plus_interprete_comme_echappement() -> None:
    """`\\b` valait un retour arrière, la donnée était corrompue en silence."""
    assert D.render_literal("a\\b") == "'a\\\\b'"


# ── Ce qui doit continuer de marcher ─────────────────────────────────────────

@pytest.mark.parametrize(
    ("valeur", "attendu"),
    [
        ("abc", "'abc'"),
        ("l'ecole", "'l''ecole'"),
        ("", "''"),
        ("élève 日本", "'élève 日本'"),
        ("chemin\\vers\\fichier", "'chemin\\\\vers\\\\fichier'"),
    ],
)
def test_les_valeurs_ordinaires_sont_rendues_correctement(valeur: str, attendu: str) -> None:
    assert D.render_literal(valeur) == attendu


def test_l_apostrophe_reste_doublee() -> None:
    """Le correctif ne doit pas remplacer l'échappement normalisé."""
    assert D.render_literal("'") == "''''"


@pytest.mark.parametrize(
    ("valeur", "attendu"),
    [(True, "1"), (False, "0"), (None, "NULL"), (42, "42")],
)
def test_les_types_non_textuels_sont_intacts(valeur: object, attendu: str) -> None:
    assert D.render_literal(valeur) == attendu


def test_l_ordre_d_echappement_est_le_bon() -> None:
    """Échapper l'apostrophe d'abord doublerait les antislashes introduits.

    Ici il n'y en a pas, mais la valeur combine les deux caractères : c'est le
    cas qui révélerait une inversion.
    """
    assert D.render_literal("\\'") == "'\\\\'''"


def test_le_coeur_garde_l_echappement_normalise() -> None:
    """Les trois autres backends n'ont pas ce besoin, et ne doivent pas changer.

    `escape_string` implémente la norme SQL : seule l'apostrophe est doublée.
    L'antislash y reste un caractère ordinaire, ce qui est correct pour
    PostgreSQL, SQLite et SQL Server.
    """
    from core.database.literals import escape_string

    assert escape_string("a\\b") == "'a\\b'"
