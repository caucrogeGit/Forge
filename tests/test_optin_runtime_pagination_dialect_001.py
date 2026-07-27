"""OPTIN-RUNTIME-PAGINATION-DIALECT-001 (ADR-084) : bornes de lecture des opt-ins.

Cinq opt-ins bornaient leurs lectures en syntaxe MySQL, dans le SQL qu'ils
**exécutent** et non dans du code généré : `forge-mvc-admin`, `forge-mvc-audit`,
`forge-mvc-iot`, `forge-mvc-mail` et `forge-mvc-notifications`. T-SQL ne
connaissant pas `LIMIT`, ces lectures échouaient sur SQL Server, promu au
niveau plein par l'ADR-084.

La borne sans décalage rejoint le contrat `Dialect` sous `limit_clause()`,
distincte de `pagination_clause()` qui en prend deux.

Garde-fous :
- parité MariaDB : les requêtes restent identiques à l'existant ;
- SQL Server reçoit une forme sans `LIMIT`, précédée d'un `ORDER BY` ;
- garde-fou de cause : plus aucun littéral `LIMIT ?` dans le SQL d'exécution.
"""
from __future__ import annotations

import ast
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

BACKENDS = ("mariadb", "sqlite", "postgres", "mssql")

PROJECT_ROOT = Path(__file__).parent.parent

# Modules dont le SQL d'exécution bornait les lectures en MySQL.
RUNTIME_SQL_MODULES = (
    "packages/forge-mvc-admin/forge_mvc_admin/query.py",
    "packages/forge-mvc-audit/forge_mvc_audit/store.py",
    "packages/forge-mvc-iot/forge_mvc_iot/storage/repository.py",
    "packages/forge-mvc-mail/forge_mvc_mail/log.py",
    "packages/forge-mvc-notifications/forge_mvc_notifications/store.py",
)


@pytest.fixture()
def backend_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[Any]:
    from core.database import backend as backend_module

    def use(name: str) -> None:
        monkeypatch.setenv("DB_BACKEND", name)
        backend_module.reset_backend()

    try:
        yield use
    finally:
        backend_module.reset_backend()


# ── Contrat ──────────────────────────────────────────────────────────────────

def test_protocol_dialect_declare_limit_clause() -> None:
    from core.database.backend import Dialect

    assert hasattr(Dialect, "limit_clause")


@pytest.mark.parametrize("name", BACKENDS)
def test_limit_clause_porte_un_seul_marqueur(name: str, backend_env: Any) -> None:
    backend_env(name)
    from core.database.backend import get_backend

    clause = get_backend().dialect.limit_clause()
    assert clause.count("?") == 1, clause
    assert clause.startswith(" "), "la clause se colle après le ORDER BY"


def test_mssql_borne_sans_limit(backend_env: Any) -> None:
    backend_env("mssql")
    from core.database.backend import get_backend

    clause = get_backend().dialect.limit_clause()
    assert "LIMIT" not in clause, "T-SQL ne connaît pas LIMIT"
    assert "FETCH NEXT" in clause


# ── Les cinq consommateurs suivent le dialecte ───────────────────────────────

def _admin_resource() -> Any:
    from forge_mvc_admin.resources import AdminResource

    return AdminResource(
        entity="Article",
        slug="articles",
        label="Article",
        plural_label="Articles",
        list_fields=("title", "published_at"),
        form_fields=("title", "body"),
        table="articles",
        order_by="",
    )


def test_admin_pagination_suit_le_dialecte(backend_env: Any) -> None:
    from forge_mvc_admin.query import build_list_sql, list_params

    backend_env("mariadb")
    assert build_list_sql(_admin_resource()).endswith("LIMIT ? OFFSET ?")
    assert list_params(limit=10, offset=20) == [10, 20]

    backend_env("mssql")
    sql = build_list_sql(_admin_resource())
    assert sql.endswith("OFFSET ? ROWS FETCH NEXT ? ROWS ONLY")
    assert "LIMIT" not in sql
    # Le piège : l'ordre s'inverse en T-SQL.
    assert list_params(limit=10, offset=20) == [20, 10]


def test_iot_lectures_bornees_sont_des_fonctions(backend_env: Any) -> None:
    """Une constante figée à l'import ne peut plus être correcte."""
    from forge_mvc_iot.storage import (
        select_iot_events_by_device_sql,
        select_iot_events_recent_sql,
    )

    backend_env("mariadb")
    assert select_iot_events_recent_sql().endswith("LIMIT ?")

    backend_env("mssql")
    for sql in (select_iot_events_recent_sql(), select_iot_events_by_device_sql()):
        assert "LIMIT" not in sql
        assert sql.endswith("OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY")
        assert "ORDER BY" in sql, "OFFSET/FETCH exige un ORDER BY"


def test_mail_lecture_bornee_suit_le_dialecte(backend_env: Any) -> None:
    from forge_mvc_mail.log import _select_sql

    backend_env("mariadb")
    assert "LIMIT ?" in _select_sql()

    backend_env("mssql")
    sql = _select_sql()
    assert "LIMIT" not in sql
    assert "FETCH NEXT ? ROWS ONLY" in sql


# ── Garde-fou de cause ───────────────────────────────────────────────────────

def _sql_literals(path: Path) -> list[str]:
    """Littéraux de chaîne du module, seuls porteurs de SQL."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [
        node.value for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]


@pytest.mark.parametrize("relative", RUNTIME_SQL_MODULES)
def test_aucune_borne_mysql_codee_en_dur(relative: str) -> None:
    """La borne vient de `Dialect.limit_clause()`, jamais d'un littéral.

    Les docstrings sont exclues : elles expliquent précisément le défaut.
    """
    path = PROJECT_ROOT / relative
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = {
        ast.get_docstring(node)
        for node in ast.walk(tree)
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef))
    }

    offenders = [
        literal for literal in _sql_literals(path)
        if "LIMIT ?" in literal and literal not in docstrings
    ]
    assert offenders == [], (
        f"{relative} borne encore ses lectures en MySQL : {offenders}"
    )
