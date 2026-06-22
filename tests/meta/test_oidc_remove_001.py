"""Tests OIDC-REMOVE-OR-EXTRACT-001 : suppression complete d'OIDC."""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


class TestOidcFilesRemoved:
    """Tous les fichiers OIDC ont ete supprimes du depot."""

    @pytest.mark.parametrize("removed_path", [
        "core/auth/experimental/oidc.py",
        "core/auth/experimental/oidc_identity.py",
        "core/auth/oidc.py",
        "core/auth/oidc_identity.py",
        "mvc/models/sql/auth_oidc_accounts.sql",
        "mvc/models/sql/auth_oidc_identities.sql",
    ])
    def test_path_removed(self, removed_path):
        assert not Path(removed_path).exists(), (
            f"{removed_path} aurait du etre supprime"
        )

    @pytest.mark.parametrize("test_file", [
        "tests/test_auth_oidc_account.py",
        "tests/test_auth_oidc_account_table.py",
        "tests/test_auth_oidc_audit.py",
        "tests/test_auth_oidc_contract.py",
        "tests/test_auth_oidc_flow.py",
        "tests/test_auth_oidc_identity.py",
        "tests/test_oidc_scope_clarify_001.py",
    ])
    def test_test_file_removed(self, test_file):
        assert not Path(test_file).exists(), (
            f"{test_file} aurait du etre supprime"
        )


class TestOidcImportsRemoved:
    """Aucun fichier Forge n'importe ou ne reference OIDC."""

    @pytest.mark.parametrize("forbidden_pattern", [
        "from core.auth.oidc",
        "from core.auth.experimental.oidc",
        "import core.auth.oidc",
        "from forge_mvc_oidc",
        "import forge_mvc_oidc",
    ])
    def test_no_forbidden_imports(self, forbidden_pattern):
        roots = [Path("core"), Path("mvc"), Path("forge_cli"), Path("tests")]
        this_file = Path(__file__).resolve()
        offenders = []
        for root in roots:
            if not root.exists():
                continue
            for py_file in root.rglob("*.py"):
                if py_file.resolve() == this_file:
                    continue
                content = py_file.read_text(encoding="utf-8")
                if forbidden_pattern in content:
                    offenders.append(str(py_file))
        assert not offenders, (
            f"Imports OIDC a supprimer dans : {offenders}"
        )


class TestOidcConstantsRemoved:
    """Les constantes OIDC sont retirees de core.auth."""

    def test_audit_no_oidc_events(self):
        from core.auth import audit
        oidc_attrs = [a for a in dir(audit) if "OIDC" in a or "oidc" in a]
        assert not oidc_attrs, (
            f"Constantes OIDC restantes dans core.auth.audit : {oidc_attrs}"
        )

    def test_rate_limit_no_oidc_constants(self):
        from core.auth import rate_limit
        oidc_attrs = [a for a in dir(rate_limit) if "OIDC" in a or "oidc" in a]
        assert not oidc_attrs, (
            f"Constantes OIDC restantes dans core.auth.rate_limit : {oidc_attrs}"
        )

    def test_core_auth_no_oidc_exports(self):
        import core.auth
        oidc_attrs = [
            a for a in dir(core.auth)
            if ("OIDC" in a or "oidc" in a) and not a.startswith("_")
        ]
        assert not oidc_attrs, (
            f"Exports OIDC restants dans core.auth : {oidc_attrs}"
        )


class TestPyprojectClean:
    def test_no_oidc_extra(self):
        content = Path("pyproject.toml").read_text(encoding="utf-8")
        assert "oidc =" not in content.lower(), (
            "Extra 'oidc' present dans pyproject.toml"
        )
        assert "forge-mvc-oidc" not in content, (
            "Reference a forge-mvc-oidc dans pyproject.toml"
        )


class TestDocsClean:
    def test_auth_doc_no_oidc_api_section(self):
        """ADR-042 : auth.md (cœur) ne présente pas OIDC comme une API.

        La section OIDC a été retirée du cœur lors du découplage ; OIDC reste
        non fourni nativement (cf. limites de production)."""
        content = Path("docs/features/auth.md").read_text(encoding="utf-8")
        assert "## OIDC" not in content, (
            "docs/features/auth.md ne doit plus contenir de section OIDC (ADR-042)."
        )

    def test_changelog_mentions_oidc_removal(self):
        content = Path("CHANGELOG.md").read_text(encoding="utf-8")
        assert "OIDC-REMOVE-OR-EXTRACT-001" in content
