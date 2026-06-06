"""STARTERS-AUTH-AUDIT-001 — Audit Auth des starters.

Vérifie que :
- les starters ne contiennent pas d'usage injustifié de core.security.hashing ;
- le starter 2 (users-core-auth) utilise déjà l'API Auth moderne.
"""

from __future__ import annotations

from pathlib import Path

import pytest
pytestmark = pytest.mark.meta

ROOT = Path(__file__).resolve().parents[2]
STARTERS_DIR = ROOT / "forge_cli" / "starters" / "data"


# ── Absence de legacy dans les starters ──────────────────────────────────────

def test_aucun_hacher_mot_de_passe_dans_starters():
    """Aucun starter ne doit contenir hacher_mot_de_passe (PBKDF2 legacy)."""
    for py_file in STARTERS_DIR.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        assert "hacher_mot_de_passe" not in content, (
            f"Usage legacy 'hacher_mot_de_passe' trouvé dans {py_file.relative_to(ROOT)}"
        )


def test_no_verify_password_legacy_direct_in_login_starters():
    """Aucun starter ne doit appeler verify_password_legacy directement dans le chemin login."""
    for py_file in STARTERS_DIR.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        if "verify_password_legacy" in content:
            assert "_check_password" in content, (
                f"{py_file.relative_to(ROOT)} utilise verify_password_legacy sans _check_password."
            )


# Les tests test_starter_users_core_auth_utilise_hash_password et
# test_starter_users_core_auth_controller_utilise_verify_password ont été
# retirés : ils inspectaient le starter supprimé `users-core-auth`.


# ── Starters sans auth ne contiennent rien de legacy ────────────────────────

def test_starters_sans_auth_ne_contiennent_pas_hashing():
    """Le starter first-crud-generated (sans auth) n'a pas de legacy hashing."""
    for name in ("first-crud-generated",):
        for py_file in (STARTERS_DIR / name).rglob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            assert "hacher_mot_de_passe" not in content
            assert "verify_password_legacy" not in content
            assert "core.security.hashing" not in content
