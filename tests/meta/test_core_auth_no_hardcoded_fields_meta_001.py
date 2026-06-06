"""Garde-fou documentaire CORE-AUTH-NO-HARDCODED-FIELDS-001.

Vérifie que :
- core/** ne contient plus d'accès direct user["UtilisateurId"] (crochet)
- core/** ne contient pas MotDePasse
- UtilisateurId dans core/ n'apparaît que dans le helper isolé _normalize_legacy_user
- Le helper _normalize_legacy_user est bien présent dans core/security/session.py
- authenticate_session() n'accède plus directement aux clés FR par crochet
- les starters peuvent légitimement contenir des champs FR (pas interdits)
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
CORE_ROOT = PROJECT_ROOT / "core"
SECURITY_SESSION = CORE_ROOT / "security" / "session.py"


def _core_sources() -> list[tuple[Path, str]]:
    """Retourne la liste (chemin, contenu) des fichiers Python sous core/."""
    result = []
    for f in CORE_ROOT.rglob("*.py"):
        if "__pycache__" in f.parts:
            continue
        result.append((f, f.read_text(encoding="utf-8")))
    return result


# ---------------------------------------------------------------------------
# core/** ne doit pas accéder directement aux champs FR par crochet
# ---------------------------------------------------------------------------


def test_core_has_no_bracket_access_to_utilisateur_id():
    """core/**/*.py ne doit pas contenir user["UtilisateurId"] (accès direct par crochet)."""
    violations = []
    for path, content in _core_sources():
        if 'user["UtilisateurId"]' in content or "user['UtilisateurId']" in content:
            violations.append(str(path.relative_to(PROJECT_ROOT)))
    assert not violations, (
        f"Accès direct user[\"UtilisateurId\"] trouvé dans : {violations}. "
        "Utiliser _normalize_legacy_user() pour isoler le mapping legacy."
    )


def test_core_has_no_mot_de_passe():
    """core/**/*.py ne doit pas contenir MotDePasse."""
    violations = []
    for path, content in _core_sources():
        if "MotDePasse" in content:
            violations.append(str(path.relative_to(PROJECT_ROOT)))
    assert not violations, f"MotDePasse trouvé dans core/ : {violations}"


# ---------------------------------------------------------------------------
# UtilisateurId dans core/ — uniquement dans le helper isolé
# ---------------------------------------------------------------------------


def test_utilisateur_id_only_in_normalize_helper():
    """UtilisateurId ne doit apparaître dans core/ que dans core/security/session.py."""
    violations = []
    for path, content in _core_sources():
        if "UtilisateurId" in content:
            rel = path.relative_to(PROJECT_ROOT)
            if rel != Path("core/security/session.py"):
                violations.append(str(rel))
    assert not violations, (
        f"UtilisateurId trouvé hors du helper isolé dans : {violations}"
    )


def test_normalize_helper_exists_in_security_session():
    """_normalize_legacy_user() doit être défini dans core/security/session.py."""
    if not SECURITY_SESSION.exists():
        pytest.skip("core/security/session.py introuvable")
    content = SECURITY_SESSION.read_text(encoding="utf-8")
    assert "def _normalize_legacy_user(" in content, (
        "_normalize_legacy_user() doit exister dans core/security/session.py"
    )


def test_normalize_helper_covers_utilisateur_id():
    """_normalize_legacy_user() doit couvrir la clé UtilisateurId en fallback."""
    if not SECURITY_SESSION.exists():
        pytest.skip("core/security/session.py introuvable")
    content = SECURITY_SESSION.read_text(encoding="utf-8")
    assert "UtilisateurId" in content, (
        "_normalize_legacy_user() doit référencer UtilisateurId comme fallback legacy"
    )


def test_normalize_helper_covers_generic_id_first():
    """_normalize_legacy_user() doit tester user.get('id') avant user.get('UtilisateurId')."""
    if not SECURITY_SESSION.exists():
        pytest.skip("core/security/session.py introuvable")
    content = SECURITY_SESSION.read_text(encoding="utf-8")
    pos_id = content.find('user.get("id")')
    pos_utilisateur = content.find('user.get("UtilisateurId")')
    assert pos_id != -1, "_normalize_legacy_user() doit contenir user.get('id')"
    assert pos_utilisateur != -1, "_normalize_legacy_user() doit contenir user.get('UtilisateurId')"
    assert pos_id < pos_utilisateur, (
        "user.get('id') doit apparaître avant user.get('UtilisateurId') dans _normalize_legacy_user()"
    )


def test_authenticate_session_uses_normalize_helper():
    """authenticate_session() doit appeler _normalize_legacy_user() et non accéder aux clés FR directement."""
    if not SECURITY_SESSION.exists():
        pytest.skip("core/security/session.py introuvable")
    content = SECURITY_SESSION.read_text(encoding="utf-8")
    assert "_normalize_legacy_user(user)" in content, (
        "authenticate_session() doit déléguer à _normalize_legacy_user(user)"
    )
