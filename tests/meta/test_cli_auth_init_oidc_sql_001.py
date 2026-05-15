"""Garde-fous CLI-AUTH-INIT-OIDC-SQL-001.

forge auth:init ne genere plus de SQL OIDC, en coherence avec ADR-004
(OIDC hors perimetre Forge 3.0) et le code Python de cmd_auth_init.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
AUTH_CLI = PROJECT_ROOT / "forge_cli" / "auth.py"


class TestAuthInitNoOidcSqlTemplates:
    """AUTH_SQL_FILES dans forge_cli/auth.py ne reference pas de SQL OIDC."""

    def test_auth_sql_files_no_oidc_accounts(self):
        text = AUTH_CLI.read_text(encoding="utf-8")
        assert "auth_oidc_accounts" not in text, (
            "forge_cli/auth.py reference encore auth_oidc_accounts — "
            "retirer la generation SQL OIDC (ADR-004)."
        )

    def test_auth_sql_files_no_oidc_identities(self):
        text = AUTH_CLI.read_text(encoding="utf-8")
        assert "auth_oidc_identities" not in text, (
            "forge_cli/auth.py reference encore auth_oidc_identities — "
            "retirer la generation SQL OIDC (ADR-004)."
        )


class TestDocsAuthMdNoOidcSqlListing:
    """docs/auth.md ne liste pas auth_oidc_*.sql comme sortie d'auth:init."""

    def test_auth_md_no_oidc_accounts_sql(self):
        text = (PROJECT_ROOT / "docs" / "auth.md").read_text(encoding="utf-8")
        assert "auth_oidc_accounts.sql" not in text, (
            "docs/auth.md mentionne encore auth_oidc_accounts.sql comme "
            "sortie d'auth:init — a retirer."
        )

    def test_auth_md_no_oidc_identities_sql(self):
        text = (PROJECT_ROOT / "docs" / "auth.md").read_text(encoding="utf-8")
        assert "auth_oidc_identities.sql" not in text, (
            "docs/auth.md mentionne encore auth_oidc_identities.sql."
        )
