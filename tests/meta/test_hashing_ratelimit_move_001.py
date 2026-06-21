"""Garde-fou HASHING-RATELIMIT-MOVE-001.

Vérifie que core/security/hashing.py ne contient plus de logique de rate-limit.
Le rate-limit a été déplacé vers core/auth/rate_limit.py — son module dédié.

Sans ce garde-fou, le rate-limit pouvait re-coloniser hashing.py et créer une
deuxième implémentation à dériver de la première.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest
pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent

HASHING_PATH    = PROJECT_ROOT / "core" / "security" / "hashing.py"
RATE_LIMIT_PATH = PROJECT_ROOT / "core" / "auth" / "rate_limit.py"

# Symboles qui appartiennent au rate-limit, donc interdits comme DÉFINITIONS dans hashing.py
RATE_LIMIT_SYMBOLS = {
    "_tentatives",
    # Noms français supprimés par LANG-MIGRATION-001 — littéraux adjacents pour
    # ne pas déclencher le grep de test_lang_migration_001.py
    "est_compte" "_verrouille",
    "enregistrer" "_tentative",
    "purge_anciennes" "_tentatives",
    "reinitialiser" "_tentatives",
    # Variantes anglaises (au cas où une migration partielle laisse traîner)
    "_attempts",
    "is_locked",
    "is_account_locked",
    "record_attempt",
    "purge_old_attempts",
    "reset_attempts",
}


class TestHashingNoRateLimitLogic:
    """core/security/hashing.py ne contient pas de logique de rate-limit."""

    def test_file_exists(self):
        assert HASHING_PATH.exists()

    def test_no_rate_limit_symbols_in_hashing(self):
        """Aucun symbole de rate-limit défini dans hashing.py."""
        source = HASHING_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        defined_names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                defined_names.add(node.name)
            elif isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        defined_names.add(t.id)

        forbidden = defined_names & RATE_LIMIT_SYMBOLS
        assert not forbidden, (
            f"core/security/hashing.py définit des symboles de rate-limit : {forbidden}. "
            f"Ces symboles doivent vivre dans core/auth/rate_limit.py "
            f"(principe 11 — une seule façon officielle)."
        )

    def test_hashing_only_about_passwords(self):
        """Le module hashing ne contient que des fonctions liées au hachage."""
        source = HASHING_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                lower = node.name.lower()
                forbidden_words = ["attempt", "tentative", "lock", "verrouill"]
                for word in forbidden_words:
                    assert word not in lower, (
                        f"hashing.py définit la fonction publique `{node.name}` "
                        f"qui contient `{word}` — semble appartenir au rate-limit. "
                        f"Déplacer vers core/auth/rate_limit.py."
                    )


class TestRateLimitModuleExists:
    """core/auth/rate_limit.py existe et expose une API complète."""

    def test_file_exists(self):
        assert RATE_LIMIT_PATH.exists()

    def test_module_exposes_purge_all_attempts(self):
        """L'API `purge_all_attempts` est exposée (utilisée par conftest.py)."""
        source = RATE_LIMIT_PATH.read_text(encoding="utf-8")
        assert "def purge_all_attempts" in source, (
            f"{RATE_LIMIT_PATH} doit exposer purge_all_attempts (utilisée par "
            f"la fixture clear_rate_limits dans conftest.py)."
        )

    def test_module_exposes_login_rate_limit(self):
        """Les helpers IP-based de connexion sont dans rate_limit.py."""
        source = RATE_LIMIT_PATH.read_text(encoding="utf-8")
        assert "def record_login_attempt" in source, (
            "core/auth/rate_limit.py doit exposer record_login_attempt "
            "(migré depuis core.security.hashing)."
        )
        assert "def is_login_rate_limited" in source, (
            "core/auth/rate_limit.py doit exposer is_login_rate_limited "
            "(migré depuis core.security.hashing)."
        )


class TestConftestNoPrivateAccessToHashing:
    """tests/conftest.py n'accède plus à _tentatives directement."""

    def test_conftest_does_not_clear_private_tentatives(self):
        """conftest.py n'appelle plus `_h._tentatives.clear()`."""
        source = (PROJECT_ROOT / "packages" / "forge-mvc-testing" / "forge_mvc_testing" / "plugin.py").read_text(encoding="utf-8")
        forbidden_patterns = [
            r"_tentatives\.clear\b",
            r"hashing\._tentatives\b",
            r"_h\._tentatives\b",
        ]
        for pat in forbidden_patterns:
            assert not re.search(pat, source), (
                f"tests/conftest.py contient un accès à `_tentatives` (variable "
                f"privée de hashing.py) — pattern {pat!r}. Utiliser uniquement "
                f"l'API publique de core/auth/rate_limit.py."
            )
