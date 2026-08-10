"""Tests HASHING-PBKDF2-REMOVE-001 — suppression de la création PBKDF2.

Vérifie que :
- hacher_mot_de_passe n'existe plus dans core.security.hashing
- ITERATIONS (constante de création) n'existe plus
- La vérification PBKDF2 reste fonctionnelle (verify_password_legacy)
- pbkdf2_needs_rehash retourne True pour tout hash PBKDF2
- Aucun fichier productif n'appelle hacher_mot_de_passe
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# TestCreationRemoved
# ---------------------------------------------------------------------------


class TestCreationRemoved:
    def test_hacher_mot_de_passe_does_not_exist(self):
        from core.security import hashing
        assert not hasattr(hashing, "hacher_mot_de_passe"), (
            "hacher_mot_de_passe aurait dû être retirée de core.security.hashing "
            "(création de hashes PBKDF2 interdite depuis Forge 2.10.0)"
        )

    def test_import_hacher_mot_de_passe_raises(self):
        with pytest.raises(ImportError):
            from core.security.hashing import hacher_mot_de_passe  # noqa: F401

    def test_iterations_constant_removed(self):
        from core.security import hashing
        assert not hasattr(hashing, "ITERATIONS"), (
            "ITERATIONS (constante de création) aurait dû être retirée"
        )


# ---------------------------------------------------------------------------
# TestVerificationKept
# ---------------------------------------------------------------------------


class TestVerificationKept:
    def test_verify_password_legacy_exists(self):
        from core.security.hashing import verify_password_legacy
        assert callable(verify_password_legacy)

    def test_verify_password_legacy_versioned_format(self):
        from core.security.hashing import verify_password_legacy
        password = "TestPassword123"
        sel = os.urandom(16)
        iterations = 600_000
        hash_bytes = hashlib.pbkdf2_hmac("sha256", password.encode(), sel, iterations)
        hash_stored = f"pbkdf2_sha256${iterations}${sel.hex()}${hash_bytes.hex()}"
        assert verify_password_legacy(password, hash_stored) is True
        assert verify_password_legacy("WrongPassword", hash_stored) is False

    def test_verify_password_legacy_legacy_format(self):
        from core.security.hashing import verify_password_legacy, LEGACY_ITERATIONS
        password = "LegacyPassword"
        sel = os.urandom(16)
        hash_bytes = hashlib.pbkdf2_hmac("sha256", password.encode(), sel, LEGACY_ITERATIONS)
        hash_stored = f"{sel.hex()}:{hash_bytes.hex()}"
        assert verify_password_legacy(password, hash_stored) is True
        assert verify_password_legacy("WrongPassword", hash_stored) is False


# ---------------------------------------------------------------------------
# TestPbkdf2NeedsRehashKept
# ---------------------------------------------------------------------------


class TestPbkdf2NeedsRehashKept:
    def test_function_exists(self):
        from core.security.hashing import pbkdf2_needs_rehash
        assert callable(pbkdf2_needs_rehash)

    def test_any_pbkdf2_hash_needs_rehash(self):
        """Tout hash PBKDF2 doit migrer vers Argon2id."""
        from core.security.hashing import pbkdf2_needs_rehash
        assert pbkdf2_needs_rehash("pbkdf2_sha256$600000$abc$def") is True
        assert pbkdf2_needs_rehash("pbkdf2_sha256$260000$abc$def") is True
        assert pbkdf2_needs_rehash("abc:def") is True
        assert pbkdf2_needs_rehash("") is True


# ---------------------------------------------------------------------------
# TestNoCreationCallsRemain
# ---------------------------------------------------------------------------


class TestNoCreationCallsRemain:
    # Racines productives réelles (`TESTS-DEAD-SKIPS-REVIVE-001`). `mvc/` a
    # quitté le dépôt avec l'ADR-044, et le balayage le sautait en silence au
    # lieu de balayer ce qui l'a remplacé : le squelette et les paquets opt-in,
    # deux endroits où du code de hachage peut vivre. Un saut n'est pas un
    # succès, et une racine absente doit faire échouer, pas taire.
    @pytest.mark.parametrize(
        "root_dir", ["core", "cli", "integrations", "packages", "skeleton"]
    )
    def test_no_hacher_mot_de_passe_calls(self, root_dir):
        root = ROOT / root_dir
        assert root.is_dir(), (
            f"{root_dir}/ a disparu du dépôt : corrigez la liste des racines "
            "productives au lieu de laisser ce contrôle se taire."
        )
        offenders = [
            str(f.relative_to(ROOT))
            for f in root.rglob("*.py")
            if "hacher_mot_de_passe(" in f.read_text(encoding="utf-8")
        ]
        assert not offenders, (
            f"Appels à hacher_mot_de_passe dans {root_dir}/ : {offenders}. "
            "Utiliser core.auth.password.hash_password() (Argon2id)."
        )
