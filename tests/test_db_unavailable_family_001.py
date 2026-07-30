"""DB-UNAVAILABLE-FAMILY-001 : le contrat pose la question de la famille, pas d'une cause.

`is_connection_lost` nommait une cause, alors que le cœur ne se sert que de la
famille : quelle que soit la réponse, il lève `DatabaseUnavailableError`, donc
un 503 avec `Retry-After`. La preuve est dans la docstring de cette erreur, qui
décrit depuis toujours « deux situations, de même nature du point de vue de
l'appelant ».

La question trop étroite avait un coût concret. Le verrou de fichier SQLite est
le jumeau exact de la saturation du pool sur un backend serveur, mais il ne
pouvait pas entrer dans une méthode nommée « la connexion est-elle coupée » sans
mentir sur son propre nom. On aurait lu `"database is locked"` sous ce nom, et
on aurait cessé de croire les noms.

D'où `is_unavailable`, qui rétablit la symétrie : une question du contrat pour
une erreur du cœur.

    is_unique_violation  ->  UniqueViolationError
    is_unavailable       ->  DatabaseUnavailableError

Les signaux mesurés ne changent pas, seule leur porte d'entrée. Le verdict
SQLite, lui, change : voir `packages/forge-mvc-sqlite/tests/test_sqlite_busy_503_001.py`.
"""
from __future__ import annotations

import pytest

from core.database import qualify
from core.database.backend import DatabaseBackend
from core.database.errors import DatabaseUnavailableError, UniqueViolationError

_BACKENDS = [
    ("forge_mvc_mariadb.backend", "MariaDBBackend"),
    ("forge_mvc_sqlite.backend", "SQLiteBackend"),
    ("forge_mvc_postgres.backend", "PostgreSQLBackend"),
    ("forge_mvc_mssql.backend", "MSSQLBackend"),
]


# ── L'ancien nom a disparu ───────────────────────────────────────────────────

def test_le_contrat_ne_nomme_plus_une_cause() -> None:
    assert not hasattr(DatabaseBackend, "is_connection_lost")


@pytest.mark.parametrize(("module", "classe"), _BACKENDS)
def test_aucun_backend_ne_garde_l_ancien_nom(module: str, classe: str) -> None:
    """Pas d'alias de compatibilité : en pré-1.0, la rupture est franche."""
    importe = pytest.importorskip(module)

    assert not hasattr(getattr(importe, classe), "is_connection_lost")


def test_la_qualification_du_coeur_ne_le_garde_pas_non_plus() -> None:
    assert not hasattr(qualify, "is_connection_lost")


# ── La question de la famille ────────────────────────────────────────────────

@pytest.mark.parametrize(("module", "classe"), _BACKENDS)
def test_les_quatre_backends_repondent(module: str, classe: str) -> None:
    importe = pytest.importorskip(module)

    assert callable(getattr(getattr(importe, classe), "is_unavailable"))


def test_le_contrat_enonce_les_deux_causes() -> None:
    """Un backend n'est pas tenu des deux, mais doit savoir lesquelles il traite."""
    doc = DatabaseBackend.is_unavailable.__doc__ or ""

    assert "connexion était morte" in doc
    assert "ressource était prise" in doc
    assert "503" in doc and "Retry-After" in doc


def test_la_symetrie_des_deux_questions_est_ecrite() -> None:
    doc = DatabaseBackend.is_unavailable.__doc__ or ""

    assert "is_unique_violation" in doc


# ── La traduction reste celle du cœur ────────────────────────────────────────

class _Backend:
    def __init__(self, *, indisponible: bool = False, doublon: bool = False) -> None:
        self._indisponible = indisponible
        self._doublon = doublon

    def is_unavailable(self, error: Exception) -> bool:
        return self._indisponible

    def is_unique_violation(self, error: Exception) -> bool:
        return self._doublon


def test_la_famille_devient_une_indisponibilite(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(qualify, "get_backend", lambda: _Backend(indisponible=True))

    traduite = qualify.qualify(RuntimeError("ressource prise"))

    assert isinstance(traduite, DatabaseUnavailableError)


def test_le_doublon_garde_la_priorite(monkeypatch: pytest.MonkeyPatch) -> None:
    """La condition la plus spécifique gagne : elle s'affiche dans un formulaire."""
    monkeypatch.setattr(qualify, "get_backend",
                        lambda: _Backend(indisponible=True, doublon=True))

    traduite = qualify.qualify(RuntimeError("doublon"))

    assert isinstance(traduite, UniqueViolationError)


def test_le_reste_traverse_inchange(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(qualify, "get_backend", lambda: _Backend())
    origine = RuntimeError("faute applicative")

    assert qualify.qualify(origine) is origine


def test_un_backend_muet_ne_masque_rien(monkeypatch: pytest.MonkeyPatch) -> None:
    """Un backend tiers antérieur au contrat laisse remonter l'erreur d'origine."""

    class _Ancien:
        def is_unique_violation(self, error: Exception) -> bool:
            return False

    monkeypatch.setattr(qualify, "get_backend", _Ancien)
    origine = RuntimeError("erreur du pilote")

    assert qualify.qualify(origine) is origine
