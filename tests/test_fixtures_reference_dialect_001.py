"""FIXTURES-REFERENCE-DIALECT-001 : la borne d'une référence passe par le dialecte.

`fixtures:generate` traduit `self.reference(table, colonne, valeur)` en
sous-requête SQL, écrite telle quelle dans un fichier `.sql`. Le littéral
passait bien par `dialect.render_literal()`, mais la borne était écrite en dur :

    (SELECT Id FROM users WHERE Email = 'a@b.c' LIMIT 1)

Mesuré contre un serveur réel, SQL Server refuse ce fichier :

    [42000] Incorrect syntax near '1'

Toute fixture employant `reference()` était donc inchargeable sur SQL Server,
alors qu'il est au niveau plein depuis l'ADR-084.

**Pourquoi le chantier de portabilité de la DML l'avait manqué.** Celui-ci a
rendu dialectales les requêtes des opt-ins, en balayant la couche de requêtes.
Ici le SQL n'est pas exécuté, il est **écrit comme texte dans un fichier** : il
n'a jamais traversé cette couche. Un audit qui suit les chemins d'exécution ne
voit pas le SQL qu'on imprime.

**Pourquoi `limit_clause()` ne pouvait pas servir.** Elle est paramétrée
(`LIMIT ?`), alors qu'on écrit ici du SQL sans paramètre à lier. Et sa forme
T-SQL, `OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY`, exige un `ORDER BY` et se place
en suffixe, là où l'équivalent littéral de SQL Server est `SELECT TOP 1`, en
tête. Aucun suffixe commun n'existe.

Le dialecte rend donc la **sous-requête entière**, plutôt que deux morceaux à
recoller : deux primitives à lire en paire auraient reproduit le piège de
`pagination_clause()` et `pagination_param_order()`, dont l'ordre des marqueurs
s'inverse en T-SQL.
"""
from __future__ import annotations

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _dialectes() -> "list[tuple[str, object]]":
    from forge_mvc_mariadb.dialect import MariaDBDialect
    from forge_mvc_mssql.dialect import MSSQLDialect
    from forge_mvc_postgres.dialect import PostgreSQLDialect
    from forge_mvc_sqlite.dialect import SQLiteDialect

    return [("mariadb", MariaDBDialect()), ("sqlite", SQLiteDialect()),
            ("postgres", PostgreSQLDialect()), ("mssql", MSSQLDialect())]


# ── Le contrat ───────────────────────────────────────────────────────────────

def test_le_protocole_declare_la_sous_requete() -> None:
    source = (PROJECT_ROOT / "core" / "database" / "backend.py").read_text(
        encoding="utf-8")

    assert "def single_row_subquery(self, column: str, table: str, where: str)" in source


@pytest.mark.parametrize(("nom", "dialecte"), _dialectes(),
                         ids=[n for n, _ in _dialectes()])
def test_chaque_backend_l_implemente(nom: str, dialecte: object) -> None:
    """Un backend qui ne l'implémenterait pas ferait tomber `fixtures:generate`."""
    rendu = dialecte.single_row_subquery("Id", "users", "Email = 'a@b.c'")  # type: ignore[attr-defined]

    assert rendu.startswith("(SELECT ")
    assert rendu.endswith(")")
    assert "users" in rendu and "Email = 'a@b.c'" in rendu


@pytest.mark.parametrize(("nom", "attendu"), [
    ("mariadb", "(SELECT Id FROM users WHERE Email = 'a@b.c' LIMIT 1)"),
    ("sqlite", "(SELECT Id FROM users WHERE Email = 'a@b.c' LIMIT 1)"),
    ("postgres", "(SELECT Id FROM users WHERE Email = 'a@b.c' LIMIT 1)"),
    ("mssql", "(SELECT TOP 1 Id FROM users WHERE Email = 'a@b.c')"),
])
def test_la_forme_est_celle_du_sgbd(nom: str, attendu: str) -> None:
    """T-SQL borne en tête du `SELECT`, les trois autres en suffixe."""
    dialecte = dict(_dialectes())[nom]

    assert dialecte.single_row_subquery("Id", "users", "Email = 'a@b.c'") == attendu  # type: ignore[attr-defined]


def test_sql_server_n_ecrit_jamais_limit() -> None:
    """Le cas mesuré : `Incorrect syntax near '1'` sur le fichier produit."""
    from forge_mvc_mssql.dialect import MSSQLDialect

    rendu = MSSQLDialect().single_row_subquery("Id", "t", "c = 1")

    assert "LIMIT" not in rendu.upper()


# ── L'appelant ───────────────────────────────────────────────────────────────

def test_la_generation_ne_borne_plus_en_dur() -> None:
    """Test d'absence : c'est ce littéral qui rendait le fichier inchargeable."""
    source = (PROJECT_ROOT / "packages" / "forge-mvc-fixtures" / "forge_mvc_fixtures"
              / "cli" / "generate.py").read_text(encoding="utf-8")

    assert "LIMIT 1)" not in source
    assert "dialect.single_row_subquery(" in source


@pytest.mark.parametrize(("nom", "dialecte"), _dialectes(),
                         ids=[n for n, _ in _dialectes()])
def test_une_reference_est_rendue_par_le_dialecte(nom: str, dialecte: object) -> None:
    """De bout en bout : la référence d'une factory jusqu'au SQL du fichier."""
    from forge_mvc_fixtures.cli.generate import render_value
    from forge_mvc_fixtures.factory import FixtureReference

    rendu = render_value(FixtureReference("users", "Email", "a@b.c"), dialecte)  # type: ignore[arg-type]

    assert rendu.startswith("(SELECT ")
    if nom == "mssql":
        assert "TOP 1" in rendu
    else:
        assert "LIMIT 1" in rendu
