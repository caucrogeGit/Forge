"""ENTITIES-CRUD-PAGINATION-DIALECT-001 (ADR-084) : pagination du CRUD généré.

Le modèle généré construisait sa pagination en `LIMIT ? OFFSET ?` codé en dur,
syntaxe MySQL que T-SQL ne connaît pas : tout CRUD généré sur SQL Server
échouait dès qu'il listait des enregistrements, alors que l'ADR-084 promeut ce
backend au niveau plein.

La clause et l'ordre de ses deux paramètres appartiennent désormais au contrat
`Dialect`. Garde-fous :
- parité MariaDB : le rendu reste STRICTEMENT identique à l'existant ;
- SQL Server reçoit la forme T-SQL, avec le décalage annoncé en premier ;
- le couple clause/ordre est cohérent sur les quatre dialectes ;
- comportement : la requête générée s'exécute réellement sur sqlite3 et rend
  la bonne fenêtre de lignes, ce qu'un contrôle de texte ne prouverait pas.
"""
from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from typing import Any

import pytest

from forge_mvc_entities.crud.model_builder import _render_model_query

BACKENDS = ("mariadb", "sqlite", "postgres", "mssql")


@pytest.fixture()
def backend_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[Any]:
    """Bascule le backend actif le temps d'un test."""
    from core.database import backend as backend_module

    def use(name: str) -> None:
        monkeypatch.setenv("DB_BACKEND", name)
        backend_module.reset_backend()

    try:
        yield use
    finally:
        backend_module.reset_backend()


def _definition() -> dict[str, Any]:
    return {
        "entity": "Article",
        "table": "articles",
        "fields": [
            {
                "name": "id", "column": "Id", "sql_type": "BIGINT UNSIGNED",
                "python_type": "int", "primary_key": True,
            },
            {
                "name": "titre", "column": "Titre", "sql_type": "VARCHAR(255)",
                "python_type": "str", "forge_type": "string",
            },
        ],
    }


def _paginated_lines() -> list[str]:
    definition = _definition()
    return _render_model_query(
        definition, None, [definition["fields"][1]],
        "id", "Id", "articles", "articles",
    )


def _pagination_sql_line(lines: list[str]) -> str:
    """La ligne qui assemble le SQL paginé sans clause WHERE."""
    matches = [
        line for line in lines
        if "ORDER BY" in line and "AND" not in line and line.strip().startswith("sql =")
    ]
    assert len(matches) == 1, matches
    return matches[0]


def _params_line(lines: list[str]) -> str:
    matches = [line for line in lines if "params.extend([" in line]
    assert len(matches) == 1, matches
    return matches[0].strip()


# ── Contrat ──────────────────────────────────────────────────────────────────

def test_protocol_dialect_declare_la_pagination() -> None:
    from core.database.backend import Dialect

    assert hasattr(Dialect, "pagination_clause")
    assert hasattr(Dialect, "pagination_param_order")


@pytest.mark.parametrize("name", BACKENDS)
def test_clause_et_ordre_sont_coherents(name: str, backend_env: Any) -> None:
    """Deux marqueurs, et un ordre qui nomme exactement limit et offset."""
    backend_env(name)
    from core.database.backend import get_backend

    dialect = get_backend().dialect
    clause = dialect.pagination_clause()
    order = dialect.pagination_param_order()

    assert clause.count("?") == 2, clause
    assert clause.startswith(" "), "la clause se colle après le ORDER BY"
    assert set(order) == {"limit", "offset"}, order
    assert len(order) == 2


# ── Parité MariaDB : rendu strictement identique à l'existant ────────────────

def test_parite_mariadb_rendu_inchange() -> None:
    # conftest : DB_BACKEND=mariadb par défaut.
    lines = _paginated_lines()
    assert _pagination_sql_line(lines) == (
        '        sql = base + " ORDER BY " + sort_col + " " + sort_dir'
        ' + " LIMIT ? OFFSET ?"'
    )
    assert _params_line(lines) == "params.extend([limit, offset])"


@pytest.mark.parametrize("name", ("sqlite", "postgres"))
def test_sqlite_et_postgres_partagent_la_forme_limit(name: str, backend_env: Any) -> None:
    backend_env(name)
    lines = _paginated_lines()
    assert " LIMIT ? OFFSET ?" in _pagination_sql_line(lines)
    assert _params_line(lines) == "params.extend([limit, offset])"


# ── SQL Server : forme T-SQL et ordre inversé ────────────────────────────────

def test_mssql_recoit_la_forme_tsql(backend_env: Any) -> None:
    backend_env("mssql")
    lines = _paginated_lines()
    sql_line = _pagination_sql_line(lines)

    assert " OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in sql_line
    assert "LIMIT" not in sql_line, "T-SQL ne connaît pas LIMIT"


def test_mssql_annonce_le_decalage_avant_le_nombre_de_lignes(backend_env: Any) -> None:
    """Le piège du ticket : la clause seule ne suffit pas, l'ordre s'inverse."""
    backend_env("mssql")
    assert _params_line(_paginated_lines()) == "params.extend([offset, limit])"


def test_mssql_pagination_precede_de_order_by(backend_env: Any) -> None:
    """OFFSET/FETCH exige un ORDER BY : le générateur en pose toujours un."""
    backend_env("mssql")
    for line in _paginated_lines():
        if "OFFSET ? ROWS" in line:
            assert "ORDER BY" in line, line


# ── Comportement : la requête générée s'exécute et rend la bonne fenêtre ─────

def test_la_requete_generee_rend_la_bonne_fenetre_sur_sqlite(backend_env: Any) -> None:
    """Contrôle de comportement, pas de texte : les lignes 4 à 6 sont rendues."""
    backend_env("sqlite")
    from core.database.backend import get_backend

    dialect = get_backend().dialect
    clause = dialect.pagination_clause()
    order = dialect.pagination_param_order()

    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE articles (Id INTEGER PRIMARY KEY, Titre TEXT NOT NULL)")
    connection.executemany(
        "INSERT INTO articles (Id, Titre) VALUES (?, ?)",
        [(i, f"ligne-{i:02d}") for i in range(1, 11)],
    )

    values = {"limit": 3, "offset": 3}
    params = [values[name] for name in order]
    rows = connection.execute(
        "SELECT Titre FROM articles ORDER BY Id ASC" + clause, params
    ).fetchall()
    connection.close()

    assert [row[0] for row in rows] == ["ligne-04", "ligne-05", "ligne-06"]


def test_aucun_generateur_ne_code_la_pagination_en_dur() -> None:
    """Garde-fou de cause : plus aucun LIMIT/OFFSET littéral dans les générateurs."""
    from pathlib import Path

    import forge_mvc_entities

    root = Path(forge_mvc_entities.__file__).parent
    offenders: list[str] = []
    for path in root.rglob("*.py"):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "LIMIT ? OFFSET ?" in line:
                offenders.append(f"{path.relative_to(root)}:{number}")

    assert offenders == [], (
        "La pagination doit venir de Dialect.pagination_clause(), jamais d'un "
        f"littéral : {offenders}"
    )
