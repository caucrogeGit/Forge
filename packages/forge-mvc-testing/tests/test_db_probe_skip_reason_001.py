"""TEST-DB-SKIP-REASON-001 : le motif de saut nomme la bonne cause.

Les fixtures d'intégration rangeaient toute erreur de connexion sous le mot
« injoignable », et leur commentaire assumait la confusion. Le défaut a coûté un
faux diagnostic vérifiable : un serveur MariaDB actif, à l'écoute, qui refusait
seulement les identifiants, a été lu comme un serveur arrêté.

Ces tests emploient des messages **réels** des trois pilotes, relevés en
condition, plutôt que des chaînes inventées. Un classificateur validé contre des
messages fictifs ne prouve rien du terrain.
"""
from __future__ import annotations

import pytest

pytest.importorskip("forge_mvc_testing")

from forge_mvc_testing.db_probe import (
    CAUSE_AUTH,
    CAUSE_UNKNOWN,
    CAUSE_UNREACHABLE,
    classify_connection_error,
    connection_failure_message,
)


# Messages relevés en condition réelle, pilote par pilote.
_REFUS_AUTH = [
    "Access denied for user 'root'@'localhost' (using password: NO)",
    "Access denied for user 'root'@'localhost' (using password: YES)",
    'connection failed: FATAL:  password authentication failed for user "postgres"',
    "[28000] [Microsoft][ODBC Driver 18 for SQL Server]Login failed for user 'sa'. (18456)",
]

_ABSENCE_SERVEUR = [
    "Can't connect to server on '127.0.0.1' (115)",
    "connection failed: Connection refused\n\tIs the server running on host \"127.0.0.1\"",
    "[08001] [Microsoft][ODBC Driver 18 for SQL Server]"
    "TCP Provider: Error code 0x274D (A network-related or instance-specific error)",
    "Connection timed out",
]


@pytest.mark.parametrize("message", _REFUS_AUTH)
def test_un_refus_d_identifiants_est_reconnu(message: str) -> None:
    assert classify_connection_error(RuntimeError(message)) == CAUSE_AUTH


@pytest.mark.parametrize("message", _ABSENCE_SERVEUR)
def test_une_absence_de_serveur_est_reconnue(message: str) -> None:
    assert classify_connection_error(RuntimeError(message)) == CAUSE_UNREACHABLE


def test_un_message_inconnu_ne_ment_pas() -> None:
    """Mieux vaut ne rien affirmer que d'affirmer la mauvaise cause.

    C'est tout le défaut d'origine : ranger d'office l'inconnu sous
    « injoignable » produisait un diagnostic faux avec l'aplomb du vrai.
    """
    assert classify_connection_error(RuntimeError("quelque chose a raté")) == CAUSE_UNKNOWN


def test_l_authentification_prime_sur_la_connexion() -> None:
    """Certains refus d'identifiants contiennent aussi le mot « connect ».

    Sans cet ordre, ils basculeraient à tort du côté « serveur absent », qui est
    exactement l'erreur que ce ticket corrige.
    """
    message = 'connection failed: FATAL:  password authentication failed for user "x"'

    assert classify_connection_error(RuntimeError(message)) == CAUSE_AUTH


@pytest.mark.parametrize("message", _REFUS_AUTH)
def test_le_motif_d_un_refus_dit_de_ne_pas_demarrer_le_serveur(message: str) -> None:
    """Le geste attendu doit être nommé, pas déduit par le lecteur."""
    motif = connection_failure_message(
        "MariaDB", RuntimeError(message), env_prefix="FORGE_TEST_DB"
    )

    assert "RÉPOND" in motif
    assert "FORGE_TEST_DB_PASSWORD" in motif
    assert "inutile de le démarrer" in motif
    assert "injoignable" not in motif, (
        "le mot qui a causé le faux diagnostic ne doit pas revenir sur ce cas"
    )


@pytest.mark.parametrize("message", _ABSENCE_SERVEUR)
def test_le_motif_d_une_absence_dit_de_demarrer_le_serveur(message: str) -> None:
    motif = connection_failure_message(
        "PostgreSQL", RuntimeError(message), env_prefix="FORGE_TEST_PG"
    )

    assert "injoignable" in motif
    assert "Démarrez le serveur" in motif
    assert "FORGE_TEST_PG_HOST" in motif


def test_le_motif_porte_toujours_l_erreur_d_origine() -> None:
    """Classer ne doit pas escamoter le message du pilote."""
    for message in (*_REFUS_AUTH, *_ABSENCE_SERVEUR, "cas inconnu"):
        motif = connection_failure_message(
            "SQL Server", RuntimeError(message), env_prefix="FORGE_TEST_MSSQL"
        )
        assert message.splitlines()[0] in motif


def test_le_motif_nomme_le_serveur_concerne() -> None:
    """Trois serveurs cohabitent en CI : le motif doit dire lequel a refusé."""
    for etiquette in ("MariaDB", "PostgreSQL", "SQL Server"):
        motif = connection_failure_message(
            etiquette, RuntimeError("Access denied"), env_prefix="FORGE_TEST_DB"
        )
        assert motif.startswith(etiquette)
