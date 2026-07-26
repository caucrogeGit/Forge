"""FK-IDENTITY-STORAGE-TYPE-001 : type de stockage d'une clé étrangère.

Le type d'une colonne **auto-incrémentée** (`identity_type()`) et le type de
**stockage** de la valeur qu'elle contient sont deux choses différentes. Ils
coïncident sur MariaDB (`BIGINT UNSIGNED`) et SQLite (`INTEGER`), mais pas sur
PostgreSQL (`BIGSERIAL` contre `BIGINT`) ni SQL Server
(`BIGINT IDENTITY(1,1)` contre `BIGINT`).

L'ADR-069 posait qu'une clé étrangère adopte `identity_type()` « quelle que
soit l'entité cible, et reste backend-agnostique ». C'est faux hors MariaDB et
SQLite : sur PostgreSQL la colonne FK reçoit sa propre séquence et un
`DEFAULT nextval()`, ce qui fait accepter un INSERT sans la clé et fabrique
silencieusement une valeur ; sur SQL Server le `CREATE TABLE` est refusé, une
table ne pouvant porter qu'une seule colonne IDENTITY.

Ces garde-fous verrouillent la distinction dans les deux sens : la clé
primaire garde sa forme auto-incrémentée, la clé étrangère prend le type de
stockage.
"""
from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest

# Type de stockage attendu par backend pour une colonne de clé étrangère.
STORAGE_TYPE_BY_BACKEND = {
    "mariadb": "BIGINT UNSIGNED",
    "sqlite": "INTEGER",
    "postgres": "BIGINT",
    "mssql": "BIGINT",
}

# Forme auto-incrémentée attendue pour la clé primaire : inchangée par ce ticket.
IDENTITY_TYPE_BY_BACKEND = {
    "mariadb": "BIGINT UNSIGNED",
    "sqlite": "INTEGER",
    "postgres": "BIGSERIAL",
    "mssql": "BIGINT IDENTITY(1,1)",
}

# Marqueurs d'auto-incrément : aucun ne doit apparaître dans un type de colonne FK.
AUTO_INCREMENT_MARKERS = ("SERIAL", "IDENTITY", "AUTO_INCREMENT", "AUTOINCREMENT")

BACKENDS = sorted(STORAGE_TYPE_BY_BACKEND)


@pytest.fixture()
def backend(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    """Active le backend nommé pour la durée du test."""
    from core.database import backend as backend_module

    name = request.param
    monkeypatch.setenv("DB_BACKEND", name)
    backend_module.reset_backend()
    try:
        yield name
    finally:
        backend_module.reset_backend()


def _fk_entity() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "name": "Classe",
        "table": "classe",
        "fields": [
            {
                "name": "annee_scolaire_id",
                "type": "foreign_key",
                "references": "AnneeScolaire",
                "required": True,
            }
        ],
    }


# ── Contrat Dialect ──────────────────────────────────────────────────────────


def test_protocol_dialect_declare_identity_storage_type() -> None:
    """La méthode fait partie du contrat, pas d'un backend en particulier."""
    from core.database.backend import Dialect

    assert hasattr(Dialect, "identity_storage_type")


@pytest.mark.parametrize("backend", BACKENDS, indirect=True)
def test_dialect_expose_les_deux_types(backend: str) -> None:
    from core.database.backend import get_backend

    dialect = get_backend().dialect
    assert dialect.identity_storage_type() == STORAGE_TYPE_BY_BACKEND[backend]
    assert dialect.identity_type() == IDENTITY_TYPE_BY_BACKEND[backend]


@pytest.mark.parametrize("backend", BACKENDS, indirect=True)
def test_type_de_stockage_sans_marqueur_auto_increment(backend: str) -> None:
    """Un type de stockage ne doit jamais générer de valeur tout seul."""
    from core.database.backend import get_backend

    storage = get_backend().dialect.identity_storage_type().upper()
    present = [m for m in AUTO_INCREMENT_MARKERS if m in storage]
    assert not present, (
        f"{backend} : identity_storage_type() vaut {storage!r} et porte "
        f"{present} — une colonne de clé étrangère se verrait attribuer une "
        "valeur automatiquement."
    )


# ── Résolution d'un champ foreign_key ────────────────────────────────────────


@pytest.mark.parametrize("backend", BACKENDS, indirect=True)
def test_resolveur_foreign_key_prend_le_type_de_stockage(backend: str) -> None:
    from forge_mvc_entities.field_resolver import resolve_sql_and_python_type

    sql_type, python_type = resolve_sql_and_python_type(
        {"name": "annee_scolaire_id", "type": "foreign_key", "references": "AnneeScolaire"}
    )
    assert sql_type == STORAGE_TYPE_BY_BACKEND[backend]
    assert python_type == "int"


@pytest.mark.parametrize("backend", BACKENDS, indirect=True)
def test_normaliseur_canonique_fk_et_pk_ont_des_types_distincts(backend: str) -> None:
    """Bout en bout : la PK reste auto-incrémentée, la FK ne l'est pas."""
    from forge_mvc_entities.canonical_model_normalizer import (
        normalize_canonical_entity_for_model_build,
    )

    fields = normalize_canonical_entity_for_model_build(_fk_entity())["fields"]
    pk = next(f for f in fields if f["name"] == "id")
    fk = next(f for f in fields if f["name"] == "annee_scolaire_id")

    assert pk["sql_type"] == IDENTITY_TYPE_BY_BACKEND[backend]
    assert fk["sql_type"] == STORAGE_TYPE_BY_BACKEND[backend]
    assert fk["python_type"] == "int"
    assert fk["nullable"] is False

    storage = fk["sql_type"].upper()
    assert not [m for m in AUTO_INCREMENT_MARKERS if m in storage], (
        f"{backend} : la colonne FK {fk['column']} est déclarée {fk['sql_type']!r}, "
        "donc auto-générée — un INSERT sans la clé fabriquerait une valeur."
    )
