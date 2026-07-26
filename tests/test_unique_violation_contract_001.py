"""DB-UNIQUE-VIOLATION-CONTRACT-001 — détection portable des doublons.

Une application a besoin de distinguer « ce courriel existe déjà » d'une
panne, pour afficher une erreur de formulaire plutôt qu'une 500. Aucun
signal n'est portable entre pilotes, mesuré sur les quatre backends :

    MariaDB      mariadb.IntegrityError            errno 1062
    SQLite       sqlite3.IntegrityError            message « UNIQUE constraint failed »
    PostgreSQL   psycopg.errors.UniqueViolation    sqlstate 23505
    SQL Server   pyodbc.IntegrityError             numéro natif 2627

Le SQLSTATE ne suffit pas : MariaDB **et** SQL Server renvoient `23000`
aussi bien pour une violation d'unicité que pour un NOT NULL ou une clé
étrangère. Une détection par SQLSTATE serait donc fausse sur la moitié du
parc. C'est pourquoi la reconnaissance appartient au **backend** (qui
connaît son pilote) et non au `Dialect` (qui ne décrit que du SQL).

Le cœur expose `UniqueViolationError` ; `core.database.db` traduit, et
laisse remonter inchangée toute exception que le backend ne confirme pas.
"""
from __future__ import annotations

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent


# ── Contrat ──────────────────────────────────────────────────────────────────


def test_protocol_backend_declare_is_unique_violation() -> None:
    """La détection fait partie du contrat de backend, pas d'un opt-in isolé."""
    from core.database.backend import DatabaseBackend

    assert hasattr(DatabaseBackend, "is_unique_violation")


def test_la_detection_nest_pas_sur_le_dialecte() -> None:
    """Frontière du contrat : `Dialect` décrit du SQL, pas des exceptions de pilote."""
    from core.database.backend import Dialect

    assert not hasattr(Dialect, "is_unique_violation"), (
        "Reconnaitre une exception releve du pilote, donc de DatabaseBackend."
    )


def test_exception_publique_disponible() -> None:
    from core.database.errors import UniqueViolationError

    assert issubclass(UniqueViolationError, Exception)


def test_doublon_error_supprime() -> None:
    """`DoublonError` était mort, francophone (contraire ADR-003) et documenté
    avec une exception propre à MariaDB. Remplacé par `UniqueViolationError`."""
    exceptions = PROJECT_ROOT / "core" / "mvc" / "model" / "exceptions.py"
    if exceptions.exists():
        content = exceptions.read_text(encoding="utf-8")
        assert "DoublonError" not in content, (
            "DoublonError doit avoir disparu du coeur (DB-UNIQUE-VIOLATION-CONTRACT-001)."
        )
    hits = [
        p for p in (PROJECT_ROOT / "core").rglob("*.py")
        if "DoublonError" in p.read_text(encoding="utf-8")
    ]
    assert not hits, f"DoublonError subsiste dans {[str(p) for p in hits]}"


def test_le_coeur_ne_montre_aucun_except_de_pilote() -> None:
    """Aucun module du cœur ne doit *montrer* comment attraper une exception de pilote.

    C'était le défaut de `DoublonError`, dont la docstring donnait en exemple
    `except mariadb.IntegrityError:` dans un cœur agnostique (ADR-054). Citer
    un pilote pour expliquer *pourquoi* l'abstraction existe reste légitime :
    seule la forme `except <pilote>` est proscrite.
    """
    forbidden = ("except mariadb", "except psycopg", "except pyodbc", "except sqlite3")
    hits: list[str] = []
    for path in (PROJECT_ROOT / "core").rglob("*.py"):
        content = path.read_text(encoding="utf-8")
        for pattern in forbidden:
            if pattern in content:
                hits.append(f"{path.relative_to(PROJECT_ROOT).as_posix()} : « {pattern} »")
    assert not hits, (
        f"Le coeur agnostique montre comment attraper une exception de pilote : {hits}"
    )


# ── Comportement, sur SQLite (in-process, aucun serveur requis) ───────────────


@pytest.fixture()
def sqlite_backend(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    pytest.importorskip("forge_mvc_sqlite")
    import core.forge as forge
    from core.database import backend as backend_module

    forge.configure(app_name="forge_unique_test")
    monkeypatch.setenv("DB_NAME", str(tmp_path / "app.db"))
    monkeypatch.setenv("DB_BACKEND", "sqlite")
    backend_module.reset_backend()
    try:
        yield backend_module.get_backend()
    finally:
        backend_module.reset_backend()


def test_backend_reconnait_son_doublon(sqlite_backend) -> None:
    import sqlite3

    assert sqlite_backend.is_unique_violation(
        sqlite3.IntegrityError("UNIQUE constraint failed: t.email")
    )


def test_backend_ne_confond_pas_avec_une_autre_violation(sqlite_backend) -> None:
    """Le point critique : NOT NULL et clé étrangère ne sont PAS des doublons."""
    import sqlite3

    assert not sqlite_backend.is_unique_violation(
        sqlite3.IntegrityError("NOT NULL constraint failed: t.nn")
    )
    assert not sqlite_backend.is_unique_violation(
        sqlite3.IntegrityError("FOREIGN KEY constraint failed")
    )
    assert not sqlite_backend.is_unique_violation(ValueError("sans rapport"))


def test_db_traduit_le_doublon(sqlite_backend) -> None:
    """Bout en bout : la couche d'exécution lève l'exception portable."""
    from core.database import db
    from core.database.errors import UniqueViolationError

    db.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, email TEXT UNIQUE)")
    db.insert("INSERT INTO t (email) VALUES (?)", ("a@b.c",))
    with pytest.raises(UniqueViolationError):
        db.insert("INSERT INTO t (email) VALUES (?)", ("a@b.c",))


def test_db_laisse_remonter_les_autres_erreurs(sqlite_backend) -> None:
    """Aucune autre exception ne doit être enveloppée ni masquée."""
    from core.database import db
    from core.database.errors import UniqueViolationError

    db.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, nn INTEGER NOT NULL)")
    with pytest.raises(Exception) as info:
        db.insert("INSERT INTO t (nn) VALUES (?)", (None,))
    assert not isinstance(info.value, UniqueViolationError), (
        "Une violation NOT NULL a ete prise pour un doublon."
    )

    with pytest.raises(Exception) as info:
        db.fetch_all("SELECT * FROM table_inexistante")
    assert not isinstance(info.value, UniqueViolationError)


def test_erreur_dorigine_conservee_en_cause(sqlite_backend) -> None:
    """L'exception du pilote reste accessible pour le diagnostic."""
    from core.database import db
    from core.database.errors import UniqueViolationError

    db.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, email TEXT UNIQUE)")
    db.insert("INSERT INTO t (email) VALUES (?)", ("a@b.c",))
    with pytest.raises(UniqueViolationError) as info:
        db.insert("INSERT INTO t (email) VALUES (?)", ("a@b.c",))
    assert info.value.__cause__ is not None, (
        "L'exception d'origine du pilote doit rester chainee (raise ... from)."
    )
