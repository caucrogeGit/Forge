"""MARIADB-BOOLEAN-FAMILIES-001 : `BOOLEAN` et `TINYINT(1)` sont le même type.

MariaDB accepte `BOOLEAN` à la déclaration et **stocke** `TINYINT(1)`, que
l'introspection rapporte. Le dialecte rangeait `TINYINT` dans les entiers avant
de tester les booléens : les deux faces d'un même type rendaient donc des
familles différentes.

Conséquence mesurée sur un serveur réel, avant correctif :

    test d'or : COLUMN_CHANGED  actif  type attendu BOOLEAN, trouvé TINYINT(1)

`forge migration:diff` signalait une différence sur **chaque colonne
booléenne**, et `migration:make --from-diff` refusait alors de produire quoi que
ce soit en criant au « diff risqué ».

Le défaut n'avait pas été vu à la livraison du diff par familles parce que le
serveur MariaDB n'était pas joignable : la validation avait porté sur SQLite,
PostgreSQL et SQL Server seulement.

Deux familles plutôt qu'une, sur le modèle de `forge-mvc-sqlite` dont
l'`INTEGER` rend déjà `("int", "bool")`.
"""
from __future__ import annotations

import pytest

pytest.importorskip("forge_mvc_mariadb")
from forge_mvc_mariadb.dialect import MariaDBDialect  # noqa: E402

D = MariaDBDialect()


@pytest.mark.parametrize("sql_type", ["BOOLEAN", "BOOL", "TINYINT(1)", "tinyint(1)"])
def test_les_deux_faces_du_booleen_rendent_les_memes_familles(sql_type: str) -> None:
    assert D.sql_families(sql_type) == ("int", "bool")


def test_le_type_genere_et_le_type_stocke_se_reconnaissent() -> None:
    """Le cas exact du diff : ce que Forge écrit contre ce que MariaDB rapporte."""
    genere = D.simple_type("boolean")

    assert D.sql_families(genere) == D.sql_families("tinyint(1)")


@pytest.mark.parametrize("sql_type", ["TINYINT", "TINYINT(4)", "SMALLINT", "INT", "BIGINT"])
def test_un_petit_entier_reste_un_entier(sql_type: str) -> None:
    """Seul `TINYINT(1)` est la convention booléenne ; les autres largeurs non."""
    assert D.sql_families(sql_type) == ("int",)


def test_un_booleen_ne_se_confond_pas_avec_un_entier_ordinaire() -> None:
    """Le correctif ne doit pas rendre le diff aveugle."""
    assert D.sql_families("BOOLEAN") != D.sql_families("INT")


@pytest.mark.parametrize(
    ("sql_type", "famille"),
    [
        ("VARCHAR(255)", ("str",)),
        ("LONGTEXT", ("str",)),
        ("DATE", ("date",)),
        ("DATETIME", ("datetime",)),
        ("DOUBLE", ("float",)),
        ("BIGINT UNSIGNED", ("int",)),
    ],
)
def test_les_autres_familles_sont_intactes(sql_type: str, famille: tuple[str, ...]) -> None:
    assert D.sql_families(sql_type) == famille


def test_la_validation_python_accepte_les_deux_usages() -> None:
    """`python_type` d'un champ booléen comme d'un petit entier reste valide.

    `validation.py` teste `python_type in sql_families(...)` : rendre deux
    familles élargit sans rien casser.
    """
    familles = D.sql_families("TINYINT(1)")

    assert "bool" in familles
    assert "int" in familles
