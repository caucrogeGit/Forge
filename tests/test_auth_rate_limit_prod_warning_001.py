"""Tests — AUTH-RATE-LIMIT-PROD-WARNING-001.

Verrouille le diagnostic de démarrage qui avertit lorsque Forge tourne en
APP_ENV=prod avec un session store mémoire (et donc, par construction,
des rate-limits mémoire — non configurables dans la série 1.0.0).

Le module `core.prod_warnings` n'écrit jamais dans la configuration : il
se contente de produire un message (`format_memory_store_warning`) et de
l'émettre via le logger fourni quand la condition est remplie. La
gestion des stores ne doit pas être modifiée.
"""
from __future__ import annotations

import logging

import pytest

from core.prod_warnings import (
    PROD_ENV,
    emit_memory_store_warning_if_needed,
    format_memory_store_warning,
    is_memory_session_store,
    should_warn_memory_store_in_prod,
)
from core.sessions.contract import SessionStore
from core.sessions.memory_store import MemorySessionStore


# ── Helpers ──────────────────────────────────────────────────────────────────


class _FakePersistentStore:
    """Stub minimal — n'a juste pas besoin d'être une MemorySessionStore.

    Le test ne sert pas le contrat SessionStore complet ; il vérifie que
    `is_memory_session_store` distingue bien le store par défaut d'un store
    persistant injecté par l'utilisateur.
    """


# ── is_memory_session_store ──────────────────────────────────────────────────


class TestIsMemorySessionStore:
    def test_none_is_memory(self):
        # forge.configure(session_store=None) garde le défaut MemorySessionStore.
        assert is_memory_session_store(None) is True

    def test_memory_instance_is_memory(self):
        assert is_memory_session_store(MemorySessionStore()) is True

    def test_other_store_is_not_memory(self):
        assert is_memory_session_store(_FakePersistentStore()) is False


# ── should_warn_memory_store_in_prod ────────────────────────────────────────


class TestShouldWarn:
    def test_dev_memory_does_not_warn(self):
        assert should_warn_memory_store_in_prod("dev", MemorySessionStore()) is False

    def test_test_memory_does_not_warn(self):
        assert should_warn_memory_store_in_prod("test", MemorySessionStore()) is False

    def test_prod_memory_warns(self):
        assert should_warn_memory_store_in_prod("prod", MemorySessionStore()) is True

    def test_prod_none_warns(self):
        # None = pas configuré = défaut mémoire.
        assert should_warn_memory_store_in_prod("prod", None) is True

    def test_prod_persistent_does_not_warn(self):
        assert should_warn_memory_store_in_prod("prod", _FakePersistentStore()) is False

    @pytest.mark.parametrize("value", ["PROD", "Prod", "  prod  "])
    def test_env_value_is_case_and_whitespace_insensitive(self, value):
        assert should_warn_memory_store_in_prod(value, None) is True


# ── format_memory_store_warning ─────────────────────────────────────────────


class TestWarningMessage:
    def test_mentions_production(self):
        assert PROD_ENV in format_memory_store_warning()

    def test_mentions_memory(self):
        assert "mémoire" in format_memory_store_warning()

    def test_mentions_sessions(self):
        assert "Sessions" in format_memory_store_warning()

    def test_mentions_rate_limit(self):
        assert "Rate-limit" in format_memory_store_warning()


# ── emit_memory_store_warning_if_needed ─────────────────────────────────────


class TestEmitWarning:
    def test_emits_on_prod_memory(self, caplog):
        caplog.set_level(logging.WARNING)
        emitted = emit_memory_store_warning_if_needed("prod", None)
        assert emitted is True
        joined = "\n".join(r.getMessage() for r in caplog.records)
        assert "AVERTISSEMENT-PROD" in joined
        assert "Sessions" in joined

    def test_silent_in_dev(self, caplog):
        caplog.set_level(logging.WARNING)
        emitted = emit_memory_store_warning_if_needed("dev", None)
        assert emitted is False
        assert not [r for r in caplog.records if "AVERTISSEMENT-PROD" in r.getMessage()]

    def test_silent_in_prod_with_persistent_store(self, caplog):
        caplog.set_level(logging.WARNING)
        emitted = emit_memory_store_warning_if_needed("prod", _FakePersistentStore())
        assert emitted is False
        assert not [r for r in caplog.records if "AVERTISSEMENT-PROD" in r.getMessage()]

    def test_does_not_mutate_config(self):
        import core.forge as forge
        before = forge.get("session_store")
        emit_memory_store_warning_if_needed("prod", None)
        assert forge.get("session_store") is before

    def test_does_not_replace_session_store(self):
        """Le warning n'a aucun effet de bord — le store global n'est pas touché."""
        from core.sessions.manager import get_session_store
        before = get_session_store()
        emit_memory_store_warning_if_needed("prod", None)
        assert get_session_store() is before

    def test_uses_provided_logger(self):
        seen: list[str] = []
        custom = logging.getLogger("forge.test.custom")
        handler = logging.Handler()
        handler.emit = lambda record: seen.append(record.getMessage())
        custom.addHandler(handler)
        custom.setLevel(logging.WARNING)
        try:
            emit_memory_store_warning_if_needed("prod", None, logger=custom)
        finally:
            custom.removeHandler(handler)
        assert any("AVERTISSEMENT-PROD" in m for m in seen)


# ── Cohérence avec le contrat SessionStore ──────────────────────────────────


class TestMemoryStoreIsSessionStore:
    """Sanity : le défaut Forge implémente bien le contrat SessionStore.

    Garde-fou indirect : si MemorySessionStore cesse d'être détecté comme
    `SessionStore`, le warning ne fonctionnera plus correctement.
    """

    def test_memory_store_is_a_session_store(self):
        assert isinstance(MemorySessionStore(), SessionStore)
