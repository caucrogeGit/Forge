"""Fixtures partagées des tests forge-mvc-fixtures.

Les tests unitaires (hors ``-m db``) n'ouvrent aucune base. ``fixtures:purge``
déroule désormais son démontage dans une transaction (``core.database``
``transaction()``, F52-bis) : on la remplace par un contexte factice, pour que
la commande s'exécute avec un ``tx`` mocké pendant que chaque test monkeypatche
``core.database.db.execute``. Sans base réelle, il n'y a rien à committer.

Les tests d'intégration réels vivent sous ``tests/db/`` (hors de ce paquet) et
gardent la vraie transaction.
"""
from __future__ import annotations

import contextlib
from collections.abc import Iterator
from typing import Any

import pytest


@pytest.fixture(autouse=True)
def _fake_transaction(monkeypatch: pytest.MonkeyPatch) -> None:
    @contextlib.contextmanager
    def _fake() -> Iterator[Any]:
        yield object()

    import core.database.transaction as tx_mod

    monkeypatch.setattr(tx_mod, "transaction", _fake)
