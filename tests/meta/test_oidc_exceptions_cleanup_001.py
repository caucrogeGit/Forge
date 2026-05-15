"""Garde-fou OIDC-EXCEPTIONS-CLEANUP-001.

Vérifie que core/auth/exceptions.py ne déclare plus d'exceptions OIDC.
OIDC a été retiré du core en ADR-004. G8 (CLI-AUTH-INIT-OIDC-SQL-001)
a nettoyé les SQL OIDC. T15 retire les 4 exceptions orphelines qui
n'étaient ni importées ni levées dans le code Forge.

Origine : audit F22 — 4 exceptions OIDC dans core/auth/exceptions.py
sans aucun usage actif (dead code).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
EXCEPTIONS_FILE = PROJECT_ROOT / "core" / "auth" / "exceptions.py"
AUTH_INIT_FILE = PROJECT_ROOT / "core" / "auth" / "__init__.py"

OIDC_EXCEPTION_CLASSES = [
    "InvalidOidcProviderError",
    "InvalidOidcClientConfigError",
    "InvalidOidcExternalIdentityError",
    "InvalidOidcAccountError",
]


class TestOidcExceptionsRemoved:
    """Les 4 classes d'exceptions OIDC ne sont plus déclarées."""

    @pytest.mark.parametrize("exception_name", OIDC_EXCEPTION_CLASSES)
    def test_exception_class_absent(self, exception_name: str):
        text = EXCEPTIONS_FILE.read_text(encoding="utf-8")
        assert f"class {exception_name}" not in text, (
            f"L'exception OIDC '{exception_name}' est encore déclarée dans "
            f"core/auth/exceptions.py. OIDC est retiré du core (ADR-004). "
            f"Ces exceptions sont dead code (T15 — F22)."
        )


class TestOidcExceptionsNotExported:
    """core/auth/__init__.py n'exporte pas les exceptions OIDC."""

    @pytest.mark.parametrize("exception_name", OIDC_EXCEPTION_CLASSES)
    def test_exception_not_exported(self, exception_name: str):
        text = AUTH_INIT_FILE.read_text(encoding="utf-8")
        assert exception_name not in text, (
            f"L'exception OIDC '{exception_name}' est référencée dans "
            f"core/auth/__init__.py alors qu'elle est retirée."
        )


class TestNoOidcReferencesInCoreAuth:
    """Aucun fichier de core/auth/ ne référence les exceptions OIDC."""

    def test_no_oidc_exception_imports_in_core_auth(self):
        core_auth_dir = PROJECT_ROOT / "core" / "auth"
        for py_file in core_auth_dir.glob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            for exception_name in OIDC_EXCEPTION_CLASSES:
                assert exception_name not in text, (
                    f"core/auth/{py_file.name} contient une référence à "
                    f"'{exception_name}'. À retirer."
                )
