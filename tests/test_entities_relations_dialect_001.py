"""ENTITIES-RELATIONS-DIALECT-001 (ADR-084) : many_to_one rendu par le dialecte.

Le chemin many_to_one de generate_relations_sql passe par
Dialect.add_foreign_key_sql, comme le chemin many_to_many voisin.
Garde-fous :
- parité MariaDB : le rendu reste STRICTEMENT identique à l'existant ;
- applicabilité SQLite : le SQL rendu s'exécute réellement sur sqlite3
  (:memory:), colonne, contrainte inline et index compris ;
- honnêteté (règle B) : les cas que SQLite ne sait pas honorer sont révélés
  par un commentaire SQL, jamais par un ALTER TABLE ADD CONSTRAINT inapplicable.
"""
from __future__ import annotations

import sqlite3
from collections.abc import Iterator

import pytest

from forge_mvc_entities.relations import ValidatedRelation, generate_relations_sql


def _relation(
    *,
    fk_owned: bool = True,
    fk_nullable: bool = True,
    fk_index: bool = True,
    sql_type: str = "BIGINT UNSIGNED",
) -> ValidatedRelation:
    return ValidatedRelation(
        name="annee_scolaire",
        relation_type="many_to_one",
        foreign_key_name="fk_classe_annee_scolaire_id",
        from_entity="Classe",
        from_table="classe",
        from_field="annee_scolaire_id",
        from_column="annee_scolaire_id",
        from_python_type="int",
        to_entity="AnneeScolaire",
        to_table="annee_scolaire",
        to_field="id",
        to_column="id",
        to_python_type="int",
        on_delete="RESTRICT",
        on_update="RESTRICT",
        from_column_sql_type=sql_type,
        fk_nullable=fk_nullable,
        fk_index=fk_index,
        fk_owned=fk_owned,
    )


@pytest.fixture()
def sqlite_backend(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    from core.database import backend as backend_module

    monkeypatch.setenv("DB_BACKEND", "sqlite")
    backend_module.reset_backend()
    try:
        yield
    finally:
        backend_module.reset_backend()


def test_protocol_dialect_declare_add_foreign_key_sql() -> None:
    # ADR-084 : la pose de FK many_to_one fait partie du contrat Dialect.
    from core.database.backend import Dialect

    assert hasattr(Dialect, "add_foreign_key_sql")


# ── Parité MariaDB : rendu strictement identique à l'existant ─────────────────

def test_parite_mariadb_fk_possedee_avec_index() -> None:
    # conftest : DB_BACKEND=mariadb par défaut.
    sql = generate_relations_sql([_relation()])
    assert sql == (
        "ALTER TABLE classe\n"
        "    ADD COLUMN annee_scolaire_id BIGINT UNSIGNED NULL;\n"
        "ALTER TABLE classe\n"
        "    ADD CONSTRAINT fk_classe_annee_scolaire_id\n"
        "    FOREIGN KEY (annee_scolaire_id)\n"
        "    REFERENCES annee_scolaire (id)\n"
        "    ON DELETE RESTRICT\n"
        "    ON UPDATE RESTRICT;\n"
        "CREATE INDEX idx_classe_annee_scolaire_id ON classe (annee_scolaire_id);\n"
    )


def test_parite_mariadb_fk_declaree_contrainte_seule() -> None:
    sql = generate_relations_sql([_relation(fk_owned=False)])
    assert sql == (
        "ALTER TABLE classe\n"
        "    ADD CONSTRAINT fk_classe_annee_scolaire_id\n"
        "    FOREIGN KEY (annee_scolaire_id)\n"
        "    REFERENCES annee_scolaire (id)\n"
        "    ON DELETE RESTRICT\n"
        "    ON UPDATE RESTRICT;\n"
    )


def test_parite_mariadb_fk_not_null_sans_index() -> None:
    sql = generate_relations_sql([_relation(fk_nullable=False, fk_index=False)])
    assert "ADD COLUMN annee_scolaire_id BIGINT UNSIGNED NOT NULL;" in sql
    assert "CREATE INDEX" not in sql


# ── SQLite : SQL réellement applicable sur :memory: ──────────────────────────

def _sqlite_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(
        "CREATE TABLE annee_scolaire (id INTEGER PRIMARY KEY AUTOINCREMENT, libelle TEXT)"
    )
    conn.execute("CREATE TABLE classe (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT)")
    return conn


def test_sqlite_fk_possedee_s_execute_et_contraint(sqlite_backend: None) -> None:
    sql = generate_relations_sql([_relation(sql_type="INTEGER")])
    assert "ADD CONSTRAINT" not in sql
    conn = _sqlite_conn()
    try:
        conn.executescript(sql)
        cols = {row[1] for row in conn.execute("PRAGMA table_info(classe)")}
        assert "annee_scolaire_id" in cols
        indexes = {row[1] for row in conn.execute("PRAGMA index_list(classe)")}
        assert "idx_classe_annee_scolaire_id" in indexes
        # La contrainte inline est réellement active.
        fks = list(conn.execute("PRAGMA foreign_key_list(classe)"))
        assert any(row[2] == "annee_scolaire" and row[3] == "annee_scolaire_id" for row in fks)
        conn.execute("INSERT INTO annee_scolaire (libelle) VALUES ('2026-2027')")
        conn.execute("INSERT INTO classe (code, annee_scolaire_id) VALUES ('6A', 1)")
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO classe (code, annee_scolaire_id) VALUES ('6B', 999)")
    finally:
        conn.close()


def test_sqlite_fk_not_null_revelee_et_executable(sqlite_backend: None) -> None:
    # Règle B : SQLite ne peut pas ajouter une colonne NOT NULL avec REFERENCES ;
    # le SQL le dit en commentaire et reste applicable (colonne nullable).
    sql = generate_relations_sql([_relation(fk_nullable=False, sql_type="INTEGER")])
    assert "-- SQLite" in sql
    assert "NOT NULL" in sql  # le commentaire nomme la limite
    conn = _sqlite_conn()
    try:
        conn.executescript(sql)
        cols = {row[1] for row in conn.execute("PRAGMA table_info(classe)")}
        assert "annee_scolaire_id" in cols
    finally:
        conn.close()


def test_sqlite_fk_declaree_commentaire_sans_enonce_inapplicable(sqlite_backend: None) -> None:
    # Règle B : pas d'ADD CONSTRAINT (inapplicable en SQLite), un commentaire
    # explicite à la place ; le script reste exécutable (no-op).
    sql = generate_relations_sql([_relation(fk_owned=False, sql_type="INTEGER")])
    # Aucun énoncé exécutable : uniquement des lignes de commentaire SQL.
    assert all(line.startswith("--") for line in sql.splitlines() if line.strip())
    assert "-- SQLite ne supporte pas ALTER TABLE ... ADD CONSTRAINT" in sql
    assert "ADR-084" in sql
    conn = _sqlite_conn()
    try:
        conn.executescript(sql)
    finally:
        conn.close()


def test_sqlite_many_to_one_et_m2m_partagent_le_dialecte(sqlite_backend: None) -> None:
    # Cohérence : sous SQLite, aucun trait MariaDB ne fuit dans relations.sql.
    sql = generate_relations_sql([_relation(sql_type="INTEGER")])
    assert "ENGINE=" not in sql
    assert "AUTO_INCREMENT" not in sql
