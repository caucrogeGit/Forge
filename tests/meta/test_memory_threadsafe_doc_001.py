"""Garde-fou SESSIONS-MEMORY-THREADSAFE-DOC-001.

Vérifie que docs/reference/sessions.md documente précisément le comportement
concurrent de MemorySessionStore : verrou RLock, garanties intra-processus,
limites multi-worker / multi-processus, perte des sessions au redémarrage,
et renvoi vers les backends persistants ou partagés.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
SESSIONS_DOC = PROJECT_ROOT / "docs" / "reference" / "sessions.md"


def _text() -> str:
    if not SESSIONS_DOC.exists():
        pytest.skip("docs/reference/sessions.md n'existe pas")
    return SESSIONS_DOC.read_text(encoding="utf-8")


class TestMemorySessionStoreMentioned:
    """La doc mentionne MemorySessionStore."""

    def test_memory_store_present(self):
        assert "MemorySessionStore" in _text(), (
            "docs/reference/sessions.md doit mentionner MemorySessionStore"
        )


class TestThreadingMentioned:
    """La doc mentionne le mécanisme de thread-safety (threading.RLock ou RLock)."""

    def test_threading_rlock_mentioned(self):
        text = _text()
        assert "threading.RLock" in text or "RLock" in text or "threading" in text, (
            "docs/reference/sessions.md doit mentionner threading.RLock "
            "ou le verrou RLock de MemorySessionStore"
        )


class TestMonoProcessusMentioned:
    """La doc clarifie que MemorySessionStore est mono-processus."""

    def test_mono_processus_mentioned(self):
        assert "mono-processus" in _text(), (
            "docs/reference/sessions.md doit mentionner la limite mono-processus"
        )


class TestMultiWorkerMentioned:
    """La doc mentionne explicitement les limites multi-worker / multi-processus."""

    def test_multi_worker_or_multi_processus_mentioned(self):
        text = _text()
        assert "multi-worker" in text or "multi-processus" in text, (
            "docs/reference/sessions.md doit mentionner les limites "
            "multi-worker ou multi-processus"
        )


class TestRestartLossMentioned:
    """La doc précise que les sessions sont perdues au redémarrage."""

    def test_restart_loss_mentioned(self):
        text = _text()
        assert "redémarrage" in text and (
            "perdues" in text or "perd" in text or "lost" in text
        ), (
            "docs/reference/sessions.md doit préciser que les sessions sont "
            "perdues au redémarrage du processus"
        )


class TestPersistentBackendRecommended:
    """La doc recommande un backend persistant ou partagé comme alternative."""

    def test_file_session_store_mentioned_as_alternative(self):
        assert "FileSessionStore" in _text(), (
            "docs/reference/sessions.md doit mentionner FileSessionStore "
            "comme alternative persistante"
        )

    def test_mariadb_session_store_mentioned_as_alternative(self):
        assert "MariaDbSessionStore" in _text(), (
            "docs/reference/sessions.md doit mentionner MariaDbSessionStore "
            "comme alternative multi-processus"
        )


class TestConcurrencyTestsReferenced:
    """La doc référence les tests de concurrence existants."""

    def test_concurrency_tests_referenced(self):
        assert "test_concurrency_session_001" in _text(), (
            "docs/reference/sessions.md doit référencer test_concurrency_session_001 "
            "comme confirmation des garanties thread-safety"
        )
