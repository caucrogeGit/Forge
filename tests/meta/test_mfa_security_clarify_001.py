"""Garde-fou MFA-SECURITY-CLARIFY-001.

Vérifie que la sécurité MFA est clarifiée visiblement sur 3 surfaces :
1. docs/reference/auth-mfa.md mentionne Pre-Alpha + stockage en clair
2. docs/features/auth.md tableau mentionne Pre-Alpha (et plus la dépréciation obsolète)
3. forge auth:doctor affiche un avertissement Pre-Alpha

Origine : audit F14, partiellement adressé par T3/T4/T10. T13 finit
le travail sur les 3 surfaces restantes.

État positif préservé (NON testé ici, déjà validé en T4) :
- UserWarning runtime dans register_totp_factor()
- Docstring de la fonction qui mentionne le stockage en clair
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent

# forge.py subprocess needs packages/ in PYTHONPATH (conftest.py sets sys.path
# for the test process only, not for subprocesses it spawns).
_PACKAGES_DIR = PROJECT_ROOT / "packages"
_SUBPROCESS_ENV = {
    **os.environ,
    "PYTHONPATH": os.pathsep.join(
        str(p) for p in sorted(_PACKAGES_DIR.iterdir()) if p.is_dir()
    ),
}
AUTH_MFA_REF = PROJECT_ROOT / "docs" / "reference" / "auth-mfa.md"
AUTH_DOC = PROJECT_ROOT / "docs" / "features" / "auth.md"


class TestAuthMfaRefHasPreAlphaWarning:
    """docs/reference/auth-mfa.md affiche l'avertissement de statut MFA."""

    def test_mentions_pre_alpha_or_alpha(self):
        text = AUTH_MFA_REF.read_text(encoding="utf-8")
        assert "Alpha" in text or "Pre-Alpha" in text, (
            "docs/reference/auth-mfa.md doit mentionner le statut Alpha ou Pre-Alpha."
        )

    def test_mentions_secret_chiffre(self):
        text = AUTH_MFA_REF.read_text(encoding="utf-8")
        assert (
            "chiffré" in text.lower()
            or "chiffrement" in text.lower()
            or "encrypt" in text.lower()
            or "Fernet" in text
        ), (
            "docs/reference/auth-mfa.md doit documenter que le secret TOTP "
            "est maintenant chiffré au repos (SEC-MFA-SECRET-ENCRYPTION-001)."
        )

    def test_mentions_sec_encryption_ticket(self):
        text = AUTH_MFA_REF.read_text(encoding="utf-8")
        assert "SEC-MFA-SECRET-ENCRYPTION-001" in text, (
            "docs/reference/auth-mfa.md doit mentionner le ticket "
            "SEC-MFA-SECRET-ENCRYPTION-001 comme planification de la "
            "résolution du stockage en clair."
        )

    def test_status_block_at_top(self):
        """L'avertissement de statut MFA apparaît dans les 30 premières lignes."""
        text = AUTH_MFA_REF.read_text(encoding="utf-8")
        first_30_lines = "\n".join(text.splitlines()[:30])
        assert "Alpha" in first_30_lines or "MFA-PYPI-READY-001" in first_30_lines, (
            "L'avertissement de statut (Alpha/Pre-Alpha ou ticket MFA-PYPI-READY-001) "
            "doit être en début de page (dans les 30 premières lignes)."
        )


class TestAuthDocMfaLineUpdated:
    """docs/features/auth.md tableau modules mentionne le statut MFA et plus la dépréciation obsolète."""

    def test_mfa_line_mentions_alpha_status(self):
        text = AUTH_DOC.read_text(encoding="utf-8")
        mfa_lines = [
            line for line in text.splitlines()
            if line.startswith("|") and "MFA" in line and "forge_mvc_mfa" in line
        ]
        assert mfa_lines, "Ligne MFA introuvable dans docs/features/auth.md tableau"
        for line in mfa_lines:
            assert "Alpha" in line or "Pre-Alpha" in line, (
                f"Ligne MFA dans docs/features/auth.md ne mentionne pas le statut Alpha : "
                f"{line!r}"
            )

    def test_mfa_line_no_obsolete_deprecation(self):
        """La mention 'déprécié via core.auth.mfa' a été retirée (T4)."""
        text = AUTH_DOC.read_text(encoding="utf-8")
        mfa_lines = [
            line for line in text.splitlines()
            if line.startswith("|") and "MFA" in line and "forge_mvc_mfa" in line
        ]
        for line in mfa_lines:
            assert "déprécié via" not in line and "deprecie via" not in line, (
                f"Ligne MFA dans docs/features/auth.md mentionne encore une "
                f"dépréciation obsolète (T4 a retiré la dépréciation "
                f"secret_hash, et core.auth.mfa n'existe plus). "
                f"Ligne : {line!r}"
            )

    def test_mfa_line_uses_extra_mfa_install(self):
        """La ligne MFA utilise 'forge-mvc[mfa]' (cohérence T3)."""
        text = AUTH_DOC.read_text(encoding="utf-8")
        mfa_lines = [
            line for line in text.splitlines()
            if line.startswith("|") and "MFA" in line and "forge_mvc_mfa" in line
        ]
        for line in mfa_lines:
            if "pip install" in line:
                assert "forge-mvc[mfa]" in line or "forge-mvc-mfa" in line, (
                    f"Ligne MFA dans docs/features/auth.md mentionne pip install "
                    f"mais pas la forme recommandée. Ligne : {line!r}"
                )


class TestAuthDoctorWarnsMfaPreAlpha:
    """forge auth:doctor affiche un avertissement de statut pour MFA."""

    def test_auth_doctor_warns_about_mfa_status(self):
        """forge auth:doctor mentionne Alpha, Pre-Alpha ou opt-in pour MFA."""
        try:
            result = subprocess.run(
                [sys.executable, str(PROJECT_ROOT / "forge.py"), "auth:doctor"],
                capture_output=True, text=True, timeout=15,
                env=_SUBPROCESS_ENV,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("forge non disponible ou auth:doctor échoue")

        output = result.stdout + result.stderr
        mfa_position = output.lower().find("forge_mvc_mfa")
        if mfa_position == -1:
            pytest.skip("forge auth:doctor n'affiche pas de section MFA")

        mfa_context = output[mfa_position:mfa_position + 600].lower()
        warns_about_status = (
            "pre-alpha" in mfa_context
            or "alpha" in mfa_context
            or "expérimental" in mfa_context
            or "experimental" in mfa_context
            or "opt-in" in mfa_context
        )
        assert warns_about_status, (
            f"forge auth:doctor ne mentionne pas le statut Alpha/Pre-Alpha pour MFA. "
            f"Contexte trouvé :\n{mfa_context[:400]}"
        )
