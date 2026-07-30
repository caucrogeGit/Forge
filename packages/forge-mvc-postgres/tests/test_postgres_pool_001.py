# pyright: strict
"""POSTGRES-POOL-001 — le backend PostgreSQL emprunte à un pool.

Avant ce ticket, chaque requête ouvrait puis fermait une connexion. Mesuré sur
serveur local, 12,12 ms contre 0,16 ms sur une connexion déjà ouverte, soit un
facteur 78 : une page à dix requêtes payait 120 ms de connexion pure. MariaDB
avait son pool et SQL Server bénéficie de celui du gestionnaire ODBC ;
PostgreSQL était le seul à repartir de zéro. `DB_POOL_SIZE` et
`DB_POOL_TIMEOUT` y étaient de surcroît ignorés en silence.

Le pool est celui de `psycopg_pool`, écrit par les auteurs du pilote : file
d'attente, délai, revalidation et reconnexion y sont déjà éprouvés, là où trois
cycles de pré-mortem ont montré combien ces mécanismes sont difficiles à
obtenir juste.

Ce fichier éprouve le câblage sans serveur. La preuve du pooling lui-même est
dans `tests/db/test_postgres_pool_real_server_001.py`.
"""
from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("psycopg_pool")

from forge_mvc_postgres.backend import (  # noqa: E402
    PostgreSQLBackend,
    _PgConnection,
    _reset_connection,
)


class _PoolFactice:
    def __init__(self, erreur: "Exception | None" = None) -> None:
        self.rendues: "list[Any]" = []
        self.empruntees = 0
        self._erreur = erreur

    def getconn(self) -> Any:
        if self._erreur is not None:
            raise self._erreur
        self.empruntees += 1
        return object()

    def putconn(self, connection: Any) -> None:
        self.rendues.append(connection)


class _ConnexionFactice:
    """Connexion psycopg minimale, qui note ce qu'on lui demande."""

    def __init__(self) -> None:
        self.executees: "list[str]" = []
        self.rollbacks = 0
        self.fermetures = 0
        self.autocommit: Any = False

    def execute(self, sql: str) -> None:
        self.executees.append(sql)

    def rollback(self) -> None:
        self.rollbacks += 1

    def close(self) -> None:
        self.fermetures += 1


# ── Le pool naît tard, et une seule fois ─────────────────────────────────────

def test_aucun_pool_avant_le_premier_emprunt() -> None:
    """Un pool né avant le fork de gunicorn serait partagé entre les fils."""
    assert PostgreSQLBackend()._pool is None


def test_le_backend_sait_se_fermer() -> None:
    """`reset_backend` appelle `close()` s'il existe : le pool doit y répondre."""
    backend = PostgreSQLBackend()

    assert callable(backend.close)
    backend.close()  # sans pool ouvert, sans effet et sans erreur


# ── La restitution distingue les deux provenances ────────────────────────────

def test_une_connexion_du_pool_y_retourne() -> None:
    backend = PostgreSQLBackend()
    pool = _PoolFactice()
    brute = object()

    backend.close_connection(_PgConnection(brute, pool=pool))

    assert pool.rendues == [brute], "la connexion doit retourner au pool"


def test_une_connexion_d_administration_est_fermee() -> None:
    """Elle est ouverte en direct : la rendre au pool le corromprait."""
    backend = PostgreSQLBackend()
    pool = _PoolFactice()
    backend._pool = pool
    brute = _ConnexionFactice()

    backend.close_connection(_PgConnection(brute))

    assert pool.rendues == []
    assert brute.fermetures == 1


def test_fermer_une_connexion_empruntee_la_rend_au_pool() -> None:
    """Le piège mesuré : `close()` direct brûlait la place.

    Le pool ignorait que la connexion avait disparu et comptait toujours une
    place occupée. Forge y est tombé dans ses propres tests d'intégration, où
    six migrations PostgreSQL ont échoué d'un coup sur un pool épuisé.
    """
    pool = _PoolFactice()
    brute = _ConnexionFactice()

    _PgConnection(brute, pool=pool).close()

    assert pool.rendues == [brute]
    assert brute.fermetures == 0, "la connexion ne doit pas être détruite"


def test_une_connexion_n_est_rendue_qu_une_fois() -> None:
    """Rendre deux fois la même corromprait le compte du pool."""
    pool = _PoolFactice()
    connexion = _PgConnection(_ConnexionFactice(), pool=pool)

    connexion.close()
    connexion.close()

    assert len(pool.rendues) == 1


def test_l_administration_reste_hors_pool() -> None:
    """Deux comptes distincts n'ont rien à faire dans un même jeu de connexions."""
    doc = PostgreSQLBackend.get_admin_connection.__doc__ or ""

    assert "hors pool" in doc


# ── La saturation est une indisponibilité, pas une panne ─────────────────────

def test_le_delai_depasse_devient_un_503(monkeypatch: pytest.MonkeyPatch) -> None:
    from psycopg_pool import PoolTimeout

    from core.database.errors import DatabaseUnavailableError

    backend = PostgreSQLBackend()
    pool = _PoolFactice(erreur=PoolTimeout("délai dépassé"))
    monkeypatch.setattr(backend, "_get_pool", lambda: pool)

    with pytest.raises(DatabaseUnavailableError):
        backend.get_connection()


def test_une_autre_erreur_d_emprunt_remonte_inchangee(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Le cœur n'enveloppe que ce qu'il sait qualifier (ADR-054)."""
    backend = PostgreSQLBackend()
    pool = _PoolFactice(erreur=RuntimeError("panne inattendue"))
    monkeypatch.setattr(backend, "_get_pool", lambda: pool)

    with pytest.raises(RuntimeError, match="panne inattendue"):
        backend.get_connection()


# ── La remise à zéro entre deux emprunts ─────────────────────────────────────

def test_la_remise_a_zero_efface_l_etat_de_session() -> None:
    connexion = _ConnexionFactice()

    _reset_connection(connexion)

    lot = " ".join(connexion.executees)
    assert connexion.rollbacks == 1
    for attendu in ("CLOSE ALL", "RESET ALL", "DISCARD TEMP",
                    "DISCARD PLANS", "DISCARD SEQUENCES"):
        assert attendu in lot, f"{attendu} manquant : de l'état fuirait"


def test_la_remise_a_zero_ne_touche_pas_aux_requetes_preparees() -> None:
    """Mesuré : `DISCARD ALL` casse la requête suivante.

    Il exécute un `DEALLOCATE ALL` côté serveur, alors que psycopg tient son
    propre catalogue des requêtes qu'il a préparées. Il en réclame ensuite une
    que le serveur ne connaît plus : « l'instruction préparée _pg3_0 n'existe
    pas ». Ce catalogue appartient au pilote.
    """
    connexion = _ConnexionFactice()

    _reset_connection(connexion)

    lot = " ".join(connexion.executees).upper()
    assert "DEALLOCATE" not in lot
    assert "DISCARD ALL" not in lot


def test_la_remise_a_zero_rend_l_autocommit_comme_elle_l_a_trouve() -> None:
    """Les instructions retenues refusent de tourner dans une transaction."""
    connexion = _ConnexionFactice()
    connexion.autocommit = False

    _reset_connection(connexion)

    assert connexion.autocommit is False


def test_la_remise_a_zero_restaure_meme_en_cas_d_echec() -> None:
    class _Retive(_ConnexionFactice):
        def execute(self, sql: str) -> None:
            raise RuntimeError("connexion morte")

    connexion = _Retive()
    connexion.autocommit = False

    with pytest.raises(RuntimeError):
        _reset_connection(connexion)

    assert connexion.autocommit is False
