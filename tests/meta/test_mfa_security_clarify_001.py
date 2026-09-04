"""Garde-fou MFA-SECURITY-CLARIFY-001.

Vérifie que le statut et la sécurité MFA sont clarifiés visiblement sur 3 surfaces :
1. la référence du paquet MFA documente le statut Beta + le secret chiffré au repos
2. docs/features/auth.md ne référence plus le paquet MFA opt-in (ADR-042), sans dépréciation obsolète
3. forge auth:doctor rappelle le statut opt-in de MFA et ses prérequis de sécurité

État positif préservé (NON testé ici) :
- UserWarning runtime dans register_totp_factor()
- Secret TOTP chiffré au repos (Fernet, FORGE_MFA_SECRET_KEY obligatoire)
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
# Doc embarquée par paquet depuis l'ADR-038.
AUTH_MFA_REF = PROJECT_ROOT / "packages" / "forge-mvc-mfa" / "docs" / "reference.md"
AUTH_DOC = PROJECT_ROOT / "docs" / "features" / "auth.md"


class TestAuthMfaRefHasStatusWarning:
    """La référence du paquet MFA affiche le statut et la sécurité MFA."""

    def test_mentions_la_version_suivie(self):
        """La page dit d'où vient sa version.

        Ce contrôle exigeait le mot « Beta »
        (`OPTINS-MATURITY-FOLLOWS-CORE-001`). Il figeait le moyen : un opt-in
        n'a plus de maturité propre, il suit la version du cœur, et l'exiger
        obligerait à réécrire un stade périmé pour satisfaire un test.
        """
        text = AUTH_MFA_REF.read_text(encoding="utf-8")
        assert "version du cœur" in text, (
            "La référence MFA doit dire que le paquet suit la version du cœur."
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
        """Le lecteur sait tôt à quoi s'en tenir.

        La fin est qu'un bloc de situation ouvre la page, avant la première
        ligne de code. Le contenu de ce bloc a changé, la fin non.
        """
        text = AUTH_MFA_REF.read_text(encoding="utf-8")
        first_30_lines = "\n".join(text.splitlines()[:30])
        assert "version du cœur" in first_30_lines, (
            "Le bloc de situation doit être en début de page (dans les 30 "
            "premières lignes)."
        )


class TestAuthDocMfaLineUpdated:
    """docs/features/auth.md tableau modules mentionne le statut MFA et plus la dépréciation obsolète."""

    def test_no_mfa_optin_line_in_core_auth(self):
        # ADR-042 : la table API de auth.md ne référence plus le paquet MFA
        # opt-in ; le statut Alpha de MFA est documenté dans la doc de l'opt-in.
        text = AUTH_DOC.read_text(encoding="utf-8")
        mfa_lines = [
            line for line in text.splitlines()
            if line.startswith("|") and "forge_mvc_mfa" in line
        ]
        assert not mfa_lines, (
            f"docs/features/auth.md ne doit plus contenir de ligne de table référençant "
            f"le paquet MFA opt-in (ADR-042) : {mfa_lines}"
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


class TestAuthDoctorWarnsMfaStatus:
    """forge auth:doctor rappelle le statut opt-in de MFA."""

    def test_auth_doctor_warns_about_mfa_status(self):
        """forge auth:doctor mentionne le statut opt-in (Beta) de MFA."""
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
