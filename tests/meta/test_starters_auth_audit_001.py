"""STARTERS-AUTH-AUDIT-001 — Audit Auth des starters.

Vérifie que :
- les starters ne contiennent pas d'usage injustifié de core.security.hashing ;
- le script create_auth_user du starter 4 (suivi) génère un hash Argon2id ;
- le starter 2 (utilisateurs-auth) utilise déjà l'API Auth moderne.
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


# ── Starter 4 (suivi) : hash Argon2id ────────────────────────────────────────

def test_starter_suivi_create_auth_user_utilise_hash_password():
    """Le script create_auth_user du starter suivi utilise hash_password (Argon2id)."""
    script = (
        STARTERS_DIR / "suivi-comportement-eleves" / "files" / "scripts" / "create_auth_user.py"
    ).read_text(encoding="utf-8")
    assert "hash_password(PASSWORD)" in script
    assert "hacher_mot_de_passe" not in script


def test_starter_suivi_create_auth_user_importe_core_auth():
    """Le script create_auth_user du starter suivi importe depuis core.auth.password."""
    script = (
        STARTERS_DIR / "suivi-comportement-eleves" / "files" / "scripts" / "create_auth_user.py"
    ).read_text(encoding="utf-8")
    assert "from core.auth.password import hash_password" in script


def test_starter_suivi_auth_controller_utilise_check_password():
    """Le contrôleur auth du starter suivi utilise _check_password (Argon2id en priorité)."""
    controller = (
        STARTERS_DIR / "suivi-comportement-eleves" / "files" / "mvc" / "controllers" / "auth_controller.py"
    ).read_text(encoding="utf-8")
    assert "_check_password" in controller
    assert "verify_password" in controller


def test_starter_suivi_auth_controller_chemin_direct_verifier_absent():
    """Le chemin principal du contrôleur suivi ne doit pas appeler directement
    verify_password_legacy pour la vérification du mot de passe au login."""
    controller = (
        STARTERS_DIR / "suivi-comportement-eleves" / "files" / "mvc" / "controllers" / "auth_controller.py"
    ).read_text(encoding="utf-8")
    # verify_password_legacy peut apparaître dans _check_password (repli), pas directement dans login
    assert "and verify_password_legacy(" not in controller


def test_starter_suivi_hash_argon2id_genere():
    """hash_password produit réellement un hash Argon2id ($argon2id$...)."""
    from core.auth.password import hash_password
    h = hash_password("secret123")
    assert h.startswith("$argon2id$"), f"Hash inattendu : {h[:30]}"


# ── Starter 2 (utilisateurs-auth) : déjà conforme ───────────────────────────

def test_starter_utilisateurs_auth_utilise_hash_password():
    """Le starter utilisateurs-auth utilise hash_password (Argon2id) — déjà conforme."""
    script = (
        STARTERS_DIR / "utilisateurs-auth" / "files" / "scripts" / "create_auth_user.py"
    ).read_text(encoding="utf-8")
    assert "hash_password(PASSWORD)" in script


def test_starter_utilisateurs_auth_controller_utilise_verify_password():
    """Le contrôleur auth du starter utilisateurs-auth utilise verify_password."""
    controller = (
        STARTERS_DIR / "utilisateurs-auth" / "files" / "mvc" / "controllers" / "auth_controller.py"
    ).read_text(encoding="utf-8")
    assert "verify_password" in controller


# ── Starters sans auth ne contiennent rien de legacy ────────────────────────

def test_starters_sans_auth_ne_contiennent_pas_hashing():
    """Les starters contact-simple, carnet-contacts et communes-sejours n'ont pas de legacy hashing."""
    for name in ("contact-simple", "carnet-contacts", "communes-sejours"):
        for py_file in (STARTERS_DIR / name).rglob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            assert "hacher_mot_de_passe" not in content
            assert "verify_password_legacy" not in content
            assert "core.security.hashing" not in content
