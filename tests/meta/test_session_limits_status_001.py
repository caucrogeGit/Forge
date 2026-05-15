"""Garde-fous SESSION-LIMITS-STATUS-AUDIT-001.

Verifie que SECURITY.md et README.md ne presentent plus les backends de
session comme des "tickets futurs" ou "prevus" alors qu'ils sont livres
depuis Forge 3.0 (SESSION-STORE-CONTRACT-001, SESSION-FILE-STORE-001,
SESSION-MARIADB-STORE-001 — tous marques livres dans la roadmap et ADR-002).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent


class TestSessionStoresDelivered:
    """Les trois stores de session sont presents dans core/sessions/."""

    def test_contract_exists(self):
        assert (PROJECT_ROOT / "core" / "sessions" / "contract.py").exists(), (
            "core/sessions/contract.py introuvable — SessionStore Protocol attendu."
        )

    def test_file_store_exists(self):
        assert (PROJECT_ROOT / "core" / "sessions" / "file_store.py").exists(), (
            "core/sessions/file_store.py introuvable — FileSessionStore attendu."
        )

    def test_mariadb_store_exists(self):
        assert (PROJECT_ROOT / "core" / "sessions" / "mariadb_store.py").exists(), (
            "core/sessions/mariadb_store.py introuvable — MariaDbSessionStore attendu."
        )


class TestSecurityMdNoPhantomSessionTickets:
    """SECURITY.md ne liste pas les tickets session comme prevus/futurs."""

    def setup_method(self):
        self.text = (PROJECT_ROOT / "SECURITY.md").read_text(encoding="utf-8")

    def test_no_planned_session_store_contract(self):
        assert "SESSION-STORE-CONTRACT-001" not in self.text or (
            "prévu" not in self.text and "futur" not in self.text
        ), (
            "SECURITY.md mentionne SESSION-STORE-CONTRACT-001 comme ticket "
            "futur/prevu alors qu'il est livre."
        )

    def test_no_planned_session_file_store(self):
        assert "SESSION-FILE-STORE-001" not in self.text or (
            "prévu" not in self.text and "futur" not in self.text
        ), (
            "SECURITY.md mentionne SESSION-FILE-STORE-001 comme ticket "
            "futur/prevu alors qu'il est livre."
        )

    def test_no_planned_session_mariadb_store(self):
        assert "SESSION-MARIADB-STORE-001" not in self.text or (
            "prévu" not in self.text and "futur" not in self.text
        ), (
            "SECURITY.md mentionne SESSION-MARIADB-STORE-001 comme ticket "
            "futur/prevu alors qu'il est livre."
        )

    def test_security_md_describes_available_stores(self):
        """SECURITY.md decrit les backends disponibles, pas des tickets futurs."""
        assert "MemorySessionStore" in self.text or "FileSessionStore" in self.text, (
            "SECURITY.md devrait decrire les backends de session disponibles "
            "(MemorySessionStore, FileSessionStore, MariaDbSessionStore)."
        )


class TestReadmeMdNoPhantomSessionTickets:
    """README.md ne liste pas les tickets session comme prevus/futurs."""

    def setup_method(self):
        self.text = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    def test_no_tickets_futurs_session_store_contract(self):
        is_future = "tickets futurs" in self.text and "SESSION-STORE-CONTRACT-001" in self.text
        assert not is_future, (
            "README.md mentionne SESSION-STORE-CONTRACT-001 avec 'tickets futurs' "
            "alors qu'il est livre."
        )
