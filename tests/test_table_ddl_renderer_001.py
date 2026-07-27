"""DB-TABLE-DDL-RENDERER-001 — rendu dialectal d'une table d'infrastructure.

Un paquet qui livre sa propre table doit la décrire une fois et obtenir le DDL
correct pour le backend actif. L'audit `OPTIN-DDL-DIALECT-AUDIT-001` a mesuré
le coût de l'absence de ce rendu : 12 fichiers SQL livrés par 10 opt-ins, aucun
exécutable ailleurs que sur MariaDB.

Ces garde-fous vérifient le rendu **par dialecte**, sans serveur. L'exécution
réelle du DDL produit est couverte par
`tests/db/test_table_ddl_real_server_*_001.py`.
"""
from __future__ import annotations

import pytest

from core.database.table_ddl import (
    NO_DEFAULT,
    Column,
    ForeignKey,
    Index,
    TableDefinition,
    render_create_table,
)

DIALECTS = ("mariadb", "sqlite", "postgres", "mssql")

# Constructions propres à MariaDB : aucune ne doit apparaître pour un autre
# dialecte. Ce sont exactement celles qui ont rendu les 12 fichiers audités
# inexécutables hors MariaDB.
MARIADB_ONLY = ("AUTO_INCREMENT", "UNSIGNED", "ENGINE=", "ON UPDATE CURRENT_TIMESTAMP")


def _dialect(name: str):
    pytest.importorskip(f"forge_mvc_{name}")
    module = __import__(f"forge_mvc_{name}.dialect", fromlist=["dialect"])
    cls = next(
        value for key, value in vars(module).items()
        if key.endswith("Dialect") and isinstance(value, type)
    )
    return cls()


def _sessions_table() -> TableDefinition:
    return TableDefinition(
        name="forge_sessions",
        columns=[
            Column("session_id", "char", length=64),
            Column("data", "text"),
            Column("expire_at", "datetime"),
            Column("version", "integer", default=0),
            Column("created_at", "datetime"),
        ],
        primary_key=["session_id"],
        indexes=[Index("idx_forge_sessions_expire_at", "expire_at")],
    )


def _identity_table() -> TableDefinition:
    return TableDefinition(
        name="forge_jobs",
        columns=[
            Column("id", "identity"),
            Column("queue", "string", length=191, default="default"),
            Column("payload", "text"),
            Column("done", "boolean", default=False),
            Column("created_at", "datetime", default_now=True),
            Column("updated_at", "datetime", default_now=True, on_update_now=True),
        ],
        primary_key=["id"],
    )


# ── Portabilité ──────────────────────────────────────────────────────────────


@pytest.mark.parametrize("name", DIALECTS)
@pytest.mark.parametrize("builder", [_sessions_table, _identity_table], ids=["sessions", "jobs"])
def test_aucune_construction_mariadb_hors_mariadb(name: str, builder) -> None:
    sql = "\n".join(render_create_table(builder(), _dialect(name)))
    if name == "mariadb":
        return
    present = [marker for marker in MARIADB_ONLY if marker in sql.upper()]
    assert not present, f"{name} : DDL contenant {present}\n{sql}"


@pytest.mark.parametrize("name", DIALECTS)
def test_index_rendu_en_ligne_ou_separement_selon_le_dialecte(name: str) -> None:
    dialect = _dialect(name)
    statements = render_create_table(_sessions_table(), dialect)
    if dialect.inline_indexes():
        assert len(statements) == 1, "MariaDB porte ses index dans le CREATE TABLE."
        assert "idx_forge_sessions_expire_at" in statements[0]
    else:
        assert len(statements) == 2, f"{name} exige un CREATE INDEX separe."
        assert "CREATE INDEX" in statements[1].upper()


@pytest.mark.parametrize("name", DIALECTS)
def test_la_cle_primaire_est_toujours_declaree(name: str) -> None:
    sql = "\n".join(render_create_table(_sessions_table(), _dialect(name)))
    assert "PRIMARY KEY" in sql.upper()


@pytest.mark.parametrize("name", DIALECTS)
def test_identite_auto_incrementee_passe_par_le_dialecte(name: str) -> None:
    """Chaque dialecte a sa forme : AUTO_INCREMENT, BIGSERIAL, IDENTITY(1,1)."""
    dialect = _dialect(name)
    sql = "\n".join(render_create_table(_identity_table(), dialect))
    assert dialect.identity_type().split()[0] in sql or "AUTOINCREMENT" in sql.upper()


@pytest.mark.parametrize("name", DIALECTS)
def test_restrict_est_normalise_en_no_action(name: str) -> None:
    """SQL Server ne connaît pas RESTRICT ; NO ACTION vaut pour les quatre."""
    table = TableDefinition(
        name="forge_child",
        columns=[Column("id", "identity"), Column("user_id", "identity_ref")],
        primary_key=["id"],
        foreign_keys=[ForeignKey("user_id", "users", "id", on_delete="RESTRICT")],
    )
    sql = "\n".join(render_create_table(table, _dialect(name)))
    assert "ON DELETE NO ACTION" in sql
    assert "RESTRICT" not in sql


# ── Contrat du rendu ─────────────────────────────────────────────────────────


def test_longueur_requise_pour_string_et_char() -> None:
    dialect = _dialect("sqlite")
    for kind in ("string", "char"):
        table = TableDefinition(
            name="t", columns=[Column("c", kind)], primary_key=["c"],
        )
        with pytest.raises(ValueError, match="length"):
            render_create_table(table, dialect)


def test_type_inconnu_est_refuse() -> None:
    table = TableDefinition(
        name="t", columns=[Column("c", "monnaie_martienne")], primary_key=["c"],
    )
    with pytest.raises(ValueError, match="type Forge inconnu"):
        render_create_table(table, _dialect("sqlite"))


def test_absence_de_default_se_distingue_de_default_null() -> None:
    """`NO_DEFAULT` n'est pas `None` : une colonne peut valoir DEFAULT NULL."""
    dialect = _dialect("sqlite")
    sans = render_create_table(
        TableDefinition("t", [Column("c", "text", nullable=True)], ["c"]), dialect
    )[0]
    avec = render_create_table(
        TableDefinition("t", [Column("c", "text", nullable=True, default=None)], ["c"]), dialect
    )[0]
    assert "DEFAULT" not in sans
    assert "DEFAULT NULL" in avec
    assert Column("c", "text").default is NO_DEFAULT
