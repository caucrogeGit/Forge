"""SQLITE-BUSY-503-001 — un fichier verrouillé est une indisponibilité passagère.

SQLite n'admet qu'un écrivain à la fois. Une sauvegarde, un `fixtures:load` ou
un second processus qui tient une transaction fait attendre l'écriture, puis
échouer au delà du délai. Mesuré avant correctif :

    5,0 s d'attente, puis sqlite3.OperationalError « database is locked »
    non qualifiée, donc une page 500

C'est pourtant le jumeau exact de la saturation du pool sur un backend serveur,
déjà traduite en 503 avec `Retry-After` : la requête n'a rien de fautif,
l'écrivain d'à côté finira, et réessayer suffit.

Deux autres choses se jouaient là. Le délai était celui du pilote, cinq
secondes en dur, que rien ne permettait d'ajuster ; il suit désormais
`DB_POOL_TIMEOUT`, la variable qui nomme déjà la même chose côté MariaDB. Et la
discrimination se fait sur le code SQLite (`SQLITE_BUSY`, `SQLITE_LOCKED`),
exposé par `sqlite3` depuis Python 3.11, non sur le message.

Éprouvé sur un vrai fichier, verrou tenu par une seconde connexion : aucun
serveur, donc aucune raison du marqueur `db`.
"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_sqlite")

import core.forge as forge  # noqa: E402
from core.database.errors import DatabaseUnavailableError  # noqa: E402
from forge_mvc_sqlite.backend import SQLiteBackend  # noqa: E402

_ATTENTE = "0.3"  # secondes : de quoi mesurer sans allonger la suite


@pytest.fixture()
def base_verrouillee(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Une base dont une seconde connexion tient le verrou d'écriture."""
    fichier = tmp_path / "app.db"
    forge.configure(app_name="forge_sqlite_busy_test")
    monkeypatch.setenv("DB_BACKEND", "sqlite")
    monkeypatch.setenv("DB_NAME", str(fichier))
    monkeypatch.setenv("DB_POOL_TIMEOUT", _ATTENTE)
    from core.database import backend as backend_module
    from core.database import db

    backend_module.reset_backend()
    # SQLITE-RUNTIME-NO-CREATE-001 : la base se crée par la porte de
    # provisionnement, comme le ferait `forge db:init`.
    SQLiteBackend().get_admin_connection().close()
    db.execute("CREATE TABLE compteur (id INTEGER PRIMARY KEY, v INTEGER)")

    bloqueur = sqlite3.connect(str(fichier), isolation_level=None)
    bloqueur.execute("BEGIN EXCLUSIVE")
    try:
        yield db
    finally:
        bloqueur.rollback()
        bloqueur.close()
        backend_module.reset_backend()


def test_le_verrou_devient_une_indisponibilite(base_verrouillee) -> None:
    """Le cas mesuré : `OperationalError` faisait une page 500."""
    with pytest.raises(DatabaseUnavailableError):
        base_verrouillee.insert("INSERT INTO compteur (v) VALUES (?)", (1,))


def test_l_attente_suit_db_pool_timeout(base_verrouillee) -> None:
    """Sans lecture de la variable, le pilote imposait cinq secondes en dur."""
    debut = time.perf_counter()
    with pytest.raises(DatabaseUnavailableError):
        base_verrouillee.insert("INSERT INTO compteur (v) VALUES (?)", (1,))
    ecoule = time.perf_counter() - debut

    assert ecoule >= float(_ATTENTE) * 0.5, "l'attente doit avoir eu lieu"
    assert ecoule < 2.0, f"délai du pilote non ajusté : {ecoule:.1f}s"


def test_meme_la_lecture_devient_une_indisponibilite(base_verrouillee) -> None:
    """La lecture n'est pas épargnée, et c'est ce qui rend le verdict important.

    En mode journal par défaut (pas WAL), un verrou exclusif tient les lecteurs
    à distance autant que les écrivains. Une sauvegarde ou un `fixtures:load`
    ne dégrade donc pas une page sur deux, il fait attendre le site entier.
    Rendre 500 pendant ce temps aurait envoyé chercher un bug dans le code
    applicatif à chaque page.
    """
    with pytest.raises(DatabaseUnavailableError):
        base_verrouillee.fetch_all("SELECT v FROM compteur")


def test_l_ecriture_repasse_une_fois_le_verrou_rendu(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """La condition est passagère : c'est ce qui justifie le 503 plutôt qu'un 500."""
    fichier = tmp_path / "app.db"
    forge.configure(app_name="forge_sqlite_busy_test")
    monkeypatch.setenv("DB_BACKEND", "sqlite")
    monkeypatch.setenv("DB_NAME", str(fichier))
    monkeypatch.setenv("DB_POOL_TIMEOUT", _ATTENTE)
    from core.database import backend as backend_module
    from core.database import db

    backend_module.reset_backend()
    SQLiteBackend().get_admin_connection().close()
    try:
        db.execute("CREATE TABLE compteur (id INTEGER PRIMARY KEY, v INTEGER)")
        bloqueur = sqlite3.connect(str(fichier), isolation_level=None)
        bloqueur.execute("BEGIN EXCLUSIVE")
        with pytest.raises(DatabaseUnavailableError):
            db.insert("INSERT INTO compteur (v) VALUES (?)", (1,))
        bloqueur.rollback()
        bloqueur.close()

        assert db.insert("INSERT INTO compteur (v) VALUES (?)", (2,)) == 1
    finally:
        backend_module.reset_backend()


# ── La discrimination, sur le code et non le message ─────────────────────────

def test_le_backend_lit_le_code_sqlite() -> None:
    backend = SQLiteBackend()
    verrou = sqlite3.OperationalError("database is locked")
    verrou.sqlite_errorname = "SQLITE_BUSY"  # pyright: ignore[reportAttributeAccessIssue]

    assert backend.is_unavailable(verrou) is True


@pytest.mark.parametrize("nom", ["SQLITE_BUSY", "SQLITE_BUSY_SNAPSHOT",
                                 "SQLITE_BUSY_TIMEOUT", "SQLITE_LOCKED",
                                 "SQLITE_LOCKED_SHAREDCACHE"])
def test_toute_la_famille_du_verrou_est_reconnue(nom: str) -> None:
    backend = SQLiteBackend()
    erreur = sqlite3.OperationalError("verrou")
    erreur.sqlite_errorname = nom  # pyright: ignore[reportAttributeAccessIssue]

    assert backend.is_unavailable(erreur) is True


@pytest.mark.parametrize("nom", ["SQLITE_IOERR", "SQLITE_CANTOPEN",
                                 "SQLITE_READONLY", "SQLITE_CORRUPT"])
def test_les_pannes_durables_restent_des_500(nom: str) -> None:
    """Disque, permission, corruption : réessayer n'y changerait rien."""
    backend = SQLiteBackend()
    erreur = sqlite3.OperationalError("panne")
    erreur.sqlite_errorname = nom  # pyright: ignore[reportAttributeAccessIssue]

    assert backend.is_unavailable(erreur) is False


def test_une_erreur_sans_code_ne_passe_pas() -> None:
    """Exigence de stricte : dans le doute, faux."""
    backend = SQLiteBackend()

    assert backend.is_unavailable(sqlite3.OperationalError("message nu")) is False
    assert backend.is_unavailable(ValueError("rien à voir")) is False


def test_un_doublon_n_est_pas_une_indisponibilite() -> None:
    backend = SQLiteBackend()
    doublon = sqlite3.IntegrityError("UNIQUE constraint failed: t.c")

    assert backend.is_unavailable(doublon) is False
    assert backend.is_unique_violation(doublon) is True
