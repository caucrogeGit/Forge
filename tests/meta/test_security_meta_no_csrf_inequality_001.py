"""Garde-fou méta SECURITY-META-NO-CSRF-INEQUALITY-001.

Vérifie que les fichiers de sécurité CSRF canoniques ne contiennent pas
de comparaison naïve (== ou !=) sur des tokens CSRF.

Complète test_csrf_dedup_constant_time_meta_001 en ciblant explicitement
les patterns d'inégalité bruts qui contourneraient hmac.compare_digest.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
MIDDLEWARE = PROJECT_ROOT / "core" / "security" / "middleware.py"
DECORATORS = PROJECT_ROOT / "core" / "security" / "decorators.py"

CSRF_FILES = [MIDDLEWARE, DECORATORS]

# Patterns dangereux : comparaison brute sur des noms de variables CSRF
# Intentionnellement limités aux fichiers canoniques, pas à tout le dépôt.
_DANGEROUS_PATTERNS = [
    r"csrf_token\s*[!=]=",
    r"[!=]=\s*csrf_token",
    r"token_form\s*[!=]=",
    r"[!=]=\s*token_form",
    r"token_session\s*[!=]=",
    r"[!=]=\s*token_session",
    r"provided\s*[!=]=\s*expected",
    r"expected\s*[!=]=\s*provided",
]


def _read(path: Path) -> str:
    if not path.exists():
        pytest.skip(f"{path.relative_to(PROJECT_ROOT)} introuvable")
    return path.read_text(encoding="utf-8")


@pytest.mark.parametrize("path", CSRF_FILES, ids=lambda p: p.name)
def test_no_naive_csrf_equality_in_security_files(path: Path):
    """Les fichiers CSRF canoniques ne doivent pas comparer des tokens via == ou !=."""
    src = _read(path)
    for pattern in _DANGEROUS_PATTERNS:
        match = re.search(pattern, src)
        assert match is None, (
            f"Comparaison CSRF naïve détectée dans {path.name} "
            f"(pattern {pattern!r}, ligne contenant : {match.group()!r}). "
            "Utiliser hmac.compare_digest() via CsrfMiddleware."
        )


def test_middleware_uses_compare_digest_not_equality():
    """core/security/middleware.py doit utiliser compare_digest, jamais == ou != sur les tokens."""
    src = _read(MIDDLEWARE)
    assert "compare_digest" in src, (
        "CsrfMiddleware.check() doit utiliser hmac.compare_digest ou secrets.compare_digest"
    )
    # Vérification que compare_digest encapsule bien la comparaison (pas == en plus)
    assert re.search(r"compare_digest\s*\(", src), (
        "compare_digest doit être appelé comme fonction, pas juste mentionné"
    )


def test_no_csrf_phantom_module():
    """core/security/csrf.py ne doit pas exister — le canonique est middleware.py."""
    csrf_module = PROJECT_ROOT / "core" / "security" / "csrf.py"
    assert not csrf_module.exists(), (
        "core/security/csrf.py ne doit pas exister. "
        "Le CSRF canonique est CsrfMiddleware dans core.security.middleware."
    )


def test_middleware_rejects_none_tokens():
    """core/security/middleware.py doit rejeter les tokens absents avant compare_digest."""
    src = _read(MIDDLEWARE)
    assert re.search(r"not\s+expected\b|not\s+provided\b|is\s+None", src), (
        "CsrfMiddleware doit rejeter les tokens None explicitement "
        "(empêche None != None → False)"
    )


def test_decorators_no_autonomous_csrf_validation():
    """core/security/decorators.py ne doit pas réimplémenter la validation CSRF."""
    src = _read(DECORATORS)
    # Aucun appel direct à session.get("csrf_token") dans decorators (serait une implémentation parallèle)
    assert 'session.get("csrf_token")' not in src and "session.get('csrf_token')" not in src, (
        "decorators.py ne doit pas lire csrf_token directement depuis la session — "
        "déléguer entièrement à CsrfMiddleware.check()"
    )
    # L'appel .check( doit être présent (délégation)
    assert ".check(" in src, (
        "require_csrf doit déléguer via _csrf_check.check(request)"
    )
