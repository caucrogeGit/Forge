"""Garde-fou documentaire CSRF-DEDUP-CONSTANT-TIME-001.

Vérifie que :
- core/security/decorators.py n'utilise plus de comparaison naïve pour le CSRF
- core/security/decorators.py délègue à CsrfMiddleware
- core/security/middleware.py utilise compare_digest pour le CSRF
- il n'y a pas deux implémentations concurrentes de validation CSRF dans les fichiers canoniques
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
DECORATORS = PROJECT_ROOT / "core" / "security" / "decorators.py"
MIDDLEWARE = PROJECT_ROOT / "core" / "security" / "middleware.py"


def _read(path: Path) -> str:
    if not path.exists():
        pytest.skip(f"{path.relative_to(PROJECT_ROOT)} introuvable")
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Pas de comparaison naïve dans decorators.py
# ---------------------------------------------------------------------------


def test_decorators_has_no_naive_csrf_comparison():
    """core/security/decorators.py ne doit pas utiliser != ou == pour comparer des tokens CSRF."""
    src = _read(DECORATORS)
    # Cherche un pattern naïf lié à csrf_token : token_form != token_session ou similaire
    naive_patterns = [
        r"token_form\s*!=\s*token_session",
        r"token_session\s*!=\s*token_form",
        r"token_form\s*==\s*token_session",
        r"csrf_token.*!=",
        r"!=.*csrf_token",
    ]
    for pattern in naive_patterns:
        assert not re.search(pattern, src), (
            f"Comparaison naïve CSRF trouvée dans {DECORATORS.name} : {pattern!r}. "
            "Utiliser hmac.compare_digest() via CsrfMiddleware."
        )


def test_decorators_require_csrf_delegates_to_csrf_middleware():
    """core/security/decorators.py doit importer et utiliser CsrfMiddleware."""
    src = _read(DECORATORS)
    assert "CsrfMiddleware" in src, (
        "require_csrf doit déléguer à CsrfMiddleware (import requis dans decorators.py)"
    )
    assert "_csrf_check" in src or "_CsrfMiddleware" in src or "CsrfMiddleware()" in src, (
        "require_csrf doit instancier ou utiliser CsrfMiddleware"
    )


def test_decorators_require_csrf_calls_check_method():
    """require_csrf doit appeler .check(request) et non sa propre logique de comparaison."""
    src = _read(DECORATORS)
    assert ".check(" in src, (
        "require_csrf doit appeler _csrf_check.check(request) ou équivalent"
    )


# ---------------------------------------------------------------------------
# middleware.py utilise compare_digest
# ---------------------------------------------------------------------------


def test_middleware_uses_compare_digest():
    """core/security/middleware.py doit utiliser compare_digest pour valider le token CSRF."""
    src = _read(MIDDLEWARE)
    assert "compare_digest" in src, (
        "CsrfMiddleware.check() doit utiliser hmac.compare_digest ou secrets.compare_digest"
    )


def test_middleware_handles_none_tokens():
    """core/security/middleware.py doit rejeter explicitement les tokens None."""
    src = _read(MIDDLEWARE)
    # La vérification "if not expected or not provided" garantit le rejet des None
    assert "not expected" in src or "not provided" in src or "is None" in src, (
        "CsrfMiddleware doit rejeter explicitement les tokens absents (None)"
    )


# ---------------------------------------------------------------------------
# Unicité de la logique de validation CSRF
# ---------------------------------------------------------------------------


def test_no_competing_csrf_validation_in_decorators():
    """decorators.py ne doit pas contenir sa propre logique de validation CSRF
    en parallèle de la délégation à CsrfMiddleware."""
    src = _read(DECORATORS)
    # Il ne doit pas y avoir de session.get("csrf_token") dans require_csrf
    # (cela signifierait une implémentation parallèle)
    # On cherche un pattern qui indique une lecture directe du token dans la session
    assert "token_session" not in src, (
        "decorators.py ne doit plus contenir 'token_session' — "
        "la validation est entièrement déléguée à CsrfMiddleware"
    )
    assert "token_form" not in src, (
        "decorators.py ne doit plus contenir 'token_form' — "
        "la validation est entièrement déléguée à CsrfMiddleware"
    )


def test_no_csrf_module_phantom():
    """core/security/csrf.py ne doit pas exister — le module canonique est middleware.py."""
    csrf_module = PROJECT_ROOT / "core" / "security" / "csrf.py"
    assert not csrf_module.exists(), (
        "core/security/csrf.py ne doit pas exister. "
        "Le CSRF canonique est dans core.security.middleware.CsrfMiddleware."
    )
