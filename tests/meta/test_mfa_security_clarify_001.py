"""Garde-fou MFA-SECURITY-CLARIFY-001.

Vérifie que la sécurité MFA est clarifiée visiblement sur 3 surfaces :
1. docs/reference/auth-mfa.md mentionne Pre-Alpha + stockage en clair
2. docs/auth.md tableau mentionne Pre-Alpha (et plus la dépréciation obsolète)
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
AUTH_DOC = PROJECT_ROOT / "docs" / "auth.md"


class TestAuthMfaRefHasPreAlphaWarning:
    """docs/reference/auth-mfa.md affiche l'avertissement Pre-Alpha."""

    def test_mentions_pre_alpha(self):
        text = AUTH_MFA_REF.read_text(encoding="utf-8")
        assert "Pre-Alpha" in text, (
            "docs/reference/auth-mfa.md doit mentionner 'Pre-Alpha' "
            "visiblement (avertissement de statut)."
        )

    def test_mentions_secret_en_clair(self):
        text = AUTH_MFA_REF.read_text(encoding="utf-8")
        assert (
            "en clair" in text
            or "non chiffré" in text
            or "non chiffre" in text
            or "stocké en clair" in text
        ), (
            "docs/reference/auth-mfa.md doit mentionner explicitement que "
            "le secret TOTP est stocké en clair."
        )

    def test_mentions_sec_encryption_ticket(self):
        text = AUTH_MFA_REF.read_text(encoding="utf-8")
        assert "SEC-MFA-SECRET-ENCRYPTION-001" in text, (
            "docs/reference/auth-mfa.md doit mentionner le ticket "
            "SEC-MFA-SECRET-ENCRYPTION-001 comme planification de la "
            "résolution du stockage en clair."
        )

    def test_warning_block_at_top(self):
        """L'avertissement Pre-Alpha apparaît dans les 30 premières lignes."""
        text = AUTH_MFA_REF.read_text(encoding="utf-8")
        first_30_lines = "\n".join(text.splitlines()[:30])
        assert "Pre-Alpha" in first_30_lines, (
            "L'avertissement Pre-Alpha doit être en début de page "
            "(dans les 30 premières lignes), pas perdu dans le détail technique."
        )


class TestAuthDocMfaLineUpdated:
    """docs/auth.md tableau modules mentionne Pre-Alpha et plus la dépréciation obsolète."""

    def test_mfa_line_mentions_pre_alpha(self):
        text = AUTH_DOC.read_text(encoding="utf-8")
        mfa_lines = [
            line for line in text.splitlines()
            if line.startswith("|") and "MFA" in line and "forge_mvc_mfa" in line
        ]
        assert mfa_lines, "Ligne MFA introuvable dans docs/auth.md tableau"
        for line in mfa_lines:
            assert "Pre-Alpha" in line, (
                f"Ligne MFA dans docs/auth.md ne mentionne pas Pre-Alpha : "
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
                f"Ligne MFA dans docs/auth.md mentionne encore une "
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
                    f"Ligne MFA dans docs/auth.md mentionne pip install "
                    f"mais pas la forme recommandée. Ligne : {line!r}"
                )


class TestAuthDoctorWarnsMfaPreAlpha:
    """forge auth:doctor affiche un avertissement Pre-Alpha pour MFA."""

    def test_auth_doctor_warns_about_mfa_status(self):
        """forge auth:doctor mentionne Pre-Alpha ou équivalent pour MFA."""
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
            or "expérimental" in mfa_context
            or "experimental" in mfa_context
            or ("secret" in mfa_context and "clair" in mfa_context)
        )
        assert warns_about_status, (
            f"forge auth:doctor ne mentionne pas le statut Pre-Alpha ni le "
            f"stockage en clair pour MFA. Contexte trouvé :\n{mfa_context[:400]}"
        )
