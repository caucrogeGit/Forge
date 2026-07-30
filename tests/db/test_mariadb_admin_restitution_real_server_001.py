"""MARIADB-ADMIN-RESTITUTION-001, mesure sur serveur réel.

Le défaut a été trouvé par une sonde du cinquième cycle de pré-mortem qui
fermait une connexion d'administration par `close_connection`, la voie normale
du contrat : la file bornée levait « Semaphore released too many times » après
avoir pourtant fermé la connexion.

Le pendant hors base est
`packages/forge-mvc-mariadb/tests/test_mariadb_admin_restitution_001.py`.
"""
from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.db


def test_fermer_une_connexion_d_administration_ne_leve_plus(
    real_db: None, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from core.database.backend import get_backend

    # La fixture d'intégration ne pose que les identifiants applicatifs : on
    # fournit les identifiants d'administration, lus séparément (ADR-033).
    monkeypatch.setenv("DB_ADMIN_LOGIN", os.environ.get("DB_APP_LOGIN", ""))
    monkeypatch.setenv("DB_ADMIN_PWD", os.environ.get("DB_APP_PWD", ""))
    backend = get_backend()
    # Le pool doit exister pour que la file existe : un emprunt le crée.
    probe = backend.get_connection()
    backend.close_connection(probe)

    admin = backend.get_admin_connection(database=os.environ.get("DB_NAME", ""))
    backend.close_connection(admin)  # levait ValueError avant le correctif


def test_le_pool_garde_sa_capacite_exacte_apres(real_db: None) -> None:
    """Ni jeton perdu ni jeton gagné : la capacité doit être exactement celle du départ.

    Le pool des tests est à deux connexions. Deux emprunts simultanés doivent
    encore passer, et le compteur de la file doit être plein au repos.
    """
    from typing import Any

    from core.database.backend import get_backend

    backend = get_backend()
    gate: Any = backend._gate  # pyright: ignore[reportAttributeAccessIssue]

    au_repos = gate._value
    a = backend.get_connection()
    b = backend.get_connection()
    backend.close_connection(a)
    backend.close_connection(b)

    assert gate._value == au_repos, "la capacité doit revenir exactement au repos"
