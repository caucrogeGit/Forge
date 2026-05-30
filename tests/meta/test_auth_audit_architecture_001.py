"""Tests AUTH-AUDIT-CLARIFY-ARCHITECTURE-001 : architecture audit documentee.

Verifie que :
- L'ADR-008 existe et decrit les trois briques (contrat, logger, table SQL).
- L'ADR-008 dit explicitement que Forge ne persiste pas en base.
- docs/features/auth.md a une section sur l'audit.
- Le docstring de core/auth/audit.py mentionne que la persistance est applicative.
- core/ et forge_cli/ ne contiennent aucun INSERT INTO auth_audit_log.
"""
from __future__ import annotations

from pathlib import Path

import pytest
pytestmark = pytest.mark.meta


# ── ADR-008 ───────────────────────────────────────────────────────────────────

class TestAdr008Exists:

    def test_adr_008_exists(self):
        adr = Path("docs/adr/008-auth-audit-architecture.md")
        assert adr.exists(), (
            "ADR-008 sur l'architecture audit doit exister "
            "(AUTH-AUDIT-CLARIFY-ARCHITECTURE-001)"
        )

    def test_adr_008_mentions_contract(self):
        content = Path("docs/adr/008-auth-audit-architecture.md").read_text(encoding="utf-8")
        assert "AuthAuditEvent" in content, "ADR-008 doit mentionner AuthAuditEvent"

    def test_adr_008_mentions_logger(self):
        content = Path("docs/adr/008-auth-audit-architecture.md").read_text(encoding="utf-8")
        assert "forge.auth.audit" in content, "ADR-008 doit mentionner le logger forge.auth.audit"

    def test_adr_008_mentions_sql_table(self):
        content = Path("docs/adr/008-auth-audit-architecture.md").read_text(encoding="utf-8")
        assert "auth_audit_log" in content, "ADR-008 doit mentionner la table auth_audit_log"

    def test_adr_008_states_forge_does_not_persist(self):
        content = Path("docs/adr/008-auth-audit-architecture.md").read_text(encoding="utf-8").lower()
        assert "forge n'écrit pas" in content or "forge ne persiste pas" in content, (
            "ADR-008 doit dire explicitement que Forge ne persiste pas en base"
        )

    def test_adr_008_mentions_applicative_decision(self):
        content = Path("docs/adr/008-auth-audit-architecture.md").read_text(encoding="utf-8").lower()
        assert "applicative" in content or "application" in content, (
            "ADR-008 doit mentionner que la persistance est une decision applicative"
        )


# ── docs/features/auth.md ──────────────────────────────────────────────────────────────

class TestAuthDocHasAuditSection:

    def test_auth_doc_has_audit_section(self):
        doc = Path("docs/features/auth.md")
        assert doc.exists(), "docs/features/auth.md doit exister"
        content = doc.read_text(encoding="utf-8")
        assert "audit" in content.lower(), (
            "docs/features/auth.md devrait avoir une section sur l'audit"
        )

    def test_auth_doc_mentions_adr_008(self):
        content = Path("docs/features/auth.md").read_text(encoding="utf-8")
        assert "ADR-008" in content or "008-auth-audit-architecture" in content, (
            "docs/features/auth.md devrait pointer vers l'ADR-008"
        )

    def test_auth_doc_mentions_persistence_is_applicative(self):
        content = Path("docs/features/auth.md").read_text(encoding="utf-8").lower()
        assert "applicative" in content or "application" in content, (
            "docs/features/auth.md devrait mentionner que la persistance est applicative"
        )


# ── Docstring core/auth/audit.py ──────────────────────────────────────────────

class TestAuditModuleDocstring:

    def test_docstring_exists(self):
        import core.auth.audit
        assert core.auth.audit.__doc__, "core/auth/audit.py doit avoir un docstring"

    def test_docstring_mentions_applicative_persistence(self):
        import core.auth.audit
        doc = core.auth.audit.__doc__ or ""
        assert any(keyword in doc.lower() for keyword in [
            "applicative", "application", "applicatif"
        ]), (
            "Le docstring de core/auth/audit.py devrait preciser que "
            "la persistance des audits est une decision applicative"
        )

    def test_docstring_mentions_no_db_access(self):
        import core.auth.audit
        doc = core.auth.audit.__doc__ or ""
        assert "base de donn" in doc.lower() or "acces" in doc.lower(), (
            "Le docstring doit mentionner l'absence d'acces base de donnees"
        )


# ── Garde-fou : aucun INSERT dans core/ ni forge_cli/ ─────────────────────────

class TestForgeDoesNotInsertAudit:
    """core/ et forge_cli/ ne font pas d'INSERT INTO auth_audit_log."""

    def test_no_insert_in_core(self):
        offenders = []
        for root in [Path("core"), Path("forge_cli")]:
            if not root.exists():
                continue
            for py_file in root.rglob("*.py"):
                if "__pycache__" in str(py_file):
                    continue
                content = py_file.read_text(encoding="utf-8")
                for line in content.splitlines():
                    stripped = line.strip()
                    if stripped.startswith("#"):
                        continue
                    if "INSERT" in line and "auth_audit_log" in line:
                        offenders.append(f"{py_file}: {stripped[:80]}")
        assert not offenders, (
            "core/ ou forge_cli/ contiennent du code INSERT INTO auth_audit_log "
            "(contredit ADR-008, persistance applicative) :\n"
            + "\n".join(offenders)
        )
