"""DB-CONNECTION-LOST-503-001 : une connexion coupée rend un 503, pas un 500.

Le cas n'est pas la panne durable mais la connexion **périmée dans le pool**.
Mesuré sur MariaDB, le pilote ne revalide qu'au delà d'une demi-seconde
d'inactivité : en deçà, il livre la connexion morte et
`InterfaceError: Server has gone away` traverse jusqu'à la page d'erreur.

    KILL, puis attente 0,1 s  ->  échec brut
    KILL, puis attente 1,0 s  ->  le pilote a revalidé, la requête passe

Le scénario réel est le redémarrage ou la bascule du serveur sous trafic : une
rafale de 500 pendant une demi-seconde, puis auto-guérison. C'était incohérent
avec la saturation du pool (`MARIADB-POOL-QUEUE-001`), déjà traduite en 503
avec `Retry-After`. Une connexion perdue est de la même famille : transitoire,
sans faute de l'appelant, et l'emprunt suivant réussit.

Forge ne rejoue **pas** la requête à la place de l'appelant. Réémettre en
silence une écriture dont on ignore si le serveur l'a reçue serait la magie
que le principe 3 refuse.

Le pendant sur serveur réel est `tests/db/test_connection_lost_real_server_001.py`.
"""
from __future__ import annotations

from typing import Any

import pytest

from core.database import db, qualify
from core.database.backend import DatabaseBackend
from core.database.errors import DatabaseUnavailableError, UniqueViolationError


# ── Le contrat ───────────────────────────────────────────────────────────────

def test_le_contrat_porte_la_question() -> None:
    assert hasattr(DatabaseBackend, "is_connection_lost")


def test_le_contrat_dit_ou_elle_vit_et_pourquoi() -> None:
    doc = DatabaseBackend.is_connection_lost.__doc__ or ""

    assert "503" in doc
    assert "Retry-After" in doc


@pytest.mark.parametrize(
    ("module", "classe"),
    [
        ("forge_mvc_mariadb.backend", "MariaDBBackend"),
        ("forge_mvc_sqlite.backend", "SQLiteBackend"),
        ("forge_mvc_postgres.backend", "PostgreSQLBackend"),
        ("forge_mvc_mssql.backend", "MSSQLBackend"),
    ],
)
def test_les_quatre_backends_implementent(module: str, classe: str) -> None:
    importe = pytest.importorskip(module)

    assert callable(getattr(getattr(importe, classe), "is_connection_lost"))


# ── Les signaux mesurés, backend par backend ─────────────────────────────────

class _ErreurPilote(Exception):
    def __init__(self, message: str = "", **attributs: Any) -> None:
        super().__init__(message)
        for cle, valeur in attributs.items():
            setattr(self, cle, valeur)


@pytest.mark.parametrize(("errno", "attendu"), [
    (2006, True),    # « Server has gone away », mesuré
    (2013, True),    # « Lost connection to server during query », mesuré
    (2002, True),    # serveur injoignable
    (2003, True),
    (2055, True),
    (1062, False),   # doublon : une requête fautive, pas une coupure
    (1048, False),   # NOT NULL
    (None, False),
])
def test_mariadb_discrimine_par_errno(errno: "int | None", attendu: bool) -> None:
    """Le SQLSTATE ne sert à rien ici : ces erreurs portent toutes `HY000`."""
    backend = pytest.importorskip("forge_mvc_mariadb.backend").MariaDBBackend()

    assert backend.is_connection_lost(_ErreurPilote(errno=errno, sqlstate="HY000")) is attendu


@pytest.mark.parametrize(("sqlstate", "attendu"), [
    ("08000", True), ("08006", True), ("08S01", True),
    ("57P01", True),   # admin_shutdown, mesuré en terminant le backend
    ("57P02", True), ("57P03", True),
    ("23505", False),  # doublon
    ("42601", False),  # erreur de syntaxe
])
def test_postgres_discrimine_par_sqlstate(sqlstate: str, attendu: bool) -> None:
    backend = pytest.importorskip("forge_mvc_postgres.backend").PostgreSQLBackend()

    assert backend.is_connection_lost(_ErreurPilote(sqlstate=sqlstate)) is attendu


def test_postgres_reconnait_l_erreur_sans_sqlstate() -> None:
    """Une `OperationalError` sans SQLSTATE vient du client, pas du serveur.

    Mesuré : la deuxième requête après coupure donne « the connection is
    lost », `sqlstate` à `None`. Les erreurs de requête, elles, en portent
    toujours un.
    """
    psycopg = pytest.importorskip("psycopg")
    backend = pytest.importorskip("forge_mvc_postgres.backend").PostgreSQLBackend()

    perdue = psycopg.OperationalError("the connection is lost")

    assert backend.is_connection_lost(perdue) is True


def test_postgres_reste_strict_sur_les_autres_exceptions() -> None:
    backend = pytest.importorskip("forge_mvc_postgres.backend").PostgreSQLBackend()

    assert backend.is_connection_lost(ValueError("rien à voir")) is False


@pytest.mark.parametrize(("sqlstate", "attendu"), [
    ("08S01", True),   # « Communication link failure », mesuré
    ("08001", True), ("08003", True),
    ("23000", False),  # doublon SQL Server
    ("42000", False),  # syntaxe
])
def test_mssql_discrimine_par_classe_sqlstate(sqlstate: str, attendu: bool) -> None:
    backend = pytest.importorskip("forge_mvc_mssql.backend").MSSQLBackend()
    erreur = _ErreurPilote()
    erreur.args = (sqlstate, f"[{sqlstate}] message du pilote")

    assert backend.is_connection_lost(erreur) is attendu


def test_mssql_reste_strict_sans_sqlstate() -> None:
    backend = pytest.importorskip("forge_mvc_mssql.backend").MSSQLBackend()

    assert backend.is_connection_lost(_ErreurPilote("message nu")) is False


def test_sqlite_n_a_pas_de_connexion_a_perdre() -> None:
    """Sans serveur, un échec d'accès est durable : il appelle un 500."""
    import sqlite3

    backend = pytest.importorskip("forge_mvc_sqlite.backend").SQLiteBackend()

    assert backend.is_connection_lost(sqlite3.OperationalError("disk I/O error")) is False


# ── La traduction par le cœur ────────────────────────────────────────────────

class _BackendFactice:
    """Backend minimal dont on pilote les deux réponses."""

    def __init__(self, *, perdue: bool = False, doublon: bool = False) -> None:
        self._perdue = perdue
        self._doublon = doublon
        self.rollbacks = 0

    def is_connection_lost(self, error: Exception) -> bool:
        return self._perdue

    def is_unique_violation(self, error: Exception) -> bool:
        return self._doublon


class _ConnexionQuiEchoue:
    def __init__(self, backend: _BackendFactice, *, rollback_leve: bool = False) -> None:
        self._backend = backend
        self._rollback_leve = rollback_leve

    def cursor(self, **_: Any) -> Any:
        class _Curseur:
            def execute(self, *_a: Any, **_k: Any) -> None:
                raise RuntimeError("erreur du pilote")

            def close(self) -> None:
                pass

        return _Curseur()

    def rollback(self) -> None:
        self._backend.rollbacks += 1
        if self._rollback_leve:
            raise RuntimeError("rollback impossible : connexion morte")

    def commit(self) -> None:
        pass


def _brancher(monkeypatch: pytest.MonkeyPatch, backend: _BackendFactice,
              connexion: Any) -> None:
    # Depuis CORE-TX-LOST-CONNECTION-001, la traduction vit dans
    # `core.database.qualify`, partagée par `db` et `transaction` : c'est là
    # que le backend actif est interrogé.
    monkeypatch.setattr(qualify, "get_backend", lambda: backend)
    monkeypatch.setattr(db, "get_connection", lambda: connexion)
    monkeypatch.setattr(db, "close_connection", lambda _c: None)


def test_une_coupure_devient_une_indisponibilite(monkeypatch: pytest.MonkeyPatch) -> None:
    backend = _BackendFactice(perdue=True)
    _brancher(monkeypatch, backend, _ConnexionQuiEchoue(backend))

    with pytest.raises(DatabaseUnavailableError):
        db.fetch_one("SELECT 1")


def test_le_doublon_garde_la_priorite(monkeypatch: pytest.MonkeyPatch) -> None:
    """Un backend qui répondrait vrai aux deux ne doit pas perdre le doublon.

    Le doublon est la condition la plus spécifique et la plus actionnable : il
    s'affiche dans un formulaire, là où l'indisponibilité fait une page.
    """
    backend = _BackendFactice(perdue=True, doublon=True)
    _brancher(monkeypatch, backend, _ConnexionQuiEchoue(backend))

    with pytest.raises(UniqueViolationError):
        db.execute("INSERT INTO t VALUES (1)")


def test_le_reste_remonte_inchange(monkeypatch: pytest.MonkeyPatch) -> None:
    """Le cœur n'enveloppe que ce qu'il sait qualifier (ADR-054)."""
    backend = _BackendFactice()
    _brancher(monkeypatch, backend, _ConnexionQuiEchoue(backend))

    with pytest.raises(RuntimeError, match="erreur du pilote"):
        db.fetch_one("SELECT 1")


def test_un_rollback_impossible_ne_masque_pas_la_cause(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sur connexion coupée, le rollback échoue lui aussi.

    Le laisser lever remplacerait l'erreur d'origine par la sienne : on
    diagnostiquerait « rollback impossible » au lieu de « connexion perdue ».
    """
    backend = _BackendFactice(perdue=True)
    _brancher(monkeypatch, backend,
              _ConnexionQuiEchoue(backend, rollback_leve=True))

    with pytest.raises(DatabaseUnavailableError):
        db.fetch_one("SELECT 1")

    assert backend.rollbacks == 1, "l'annulation doit rester tentée"


def test_un_backend_sans_la_methode_ne_masque_rien(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Un backend tiers antérieur au contrat laisse remonter l'erreur d'origine."""

    class _Ancien:
        def is_unique_violation(self, error: Exception) -> bool:
            return False

    ancien = _Ancien()
    monkeypatch.setattr(qualify, "get_backend", lambda: ancien)
    monkeypatch.setattr(db, "get_connection",
                        lambda: _ConnexionQuiEchoue(_BackendFactice()))
    monkeypatch.setattr(db, "close_connection", lambda _c: None)

    with pytest.raises(RuntimeError, match="erreur du pilote"):
        db.fetch_one("SELECT 1")


def test_l_erreur_traduite_conserve_sa_cause(monkeypatch: pytest.MonkeyPatch) -> None:
    backend = _BackendFactice(perdue=True)
    _brancher(monkeypatch, backend, _ConnexionQuiEchoue(backend))

    with pytest.raises(DatabaseUnavailableError) as capture:
        db.fetch_one("SELECT 1")

    assert isinstance(capture.value.__cause__, RuntimeError)
