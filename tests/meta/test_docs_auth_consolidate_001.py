"""Garde-fou DOCS-AUTH-MD-CONSOLIDATE-001.

Vérifie que docs/auth.md ne se contredit plus sur OIDC :
- la table API ne présente pas core.auth.oidc comme module fourni ;
- la liste des features disponibles n'inclut pas OIDC comme livré ;
- la section OIDC (ligne ~715) continue d'indiquer clairement que OIDC
  n'est pas fourni nativement par Forge 3.0 ;
- les notes de dépréciation MFA (Type 3, décision C2) sont conservées.

Sans ce garde-fou, un futur ajout dans la table API ou la liste de features
pourrait réintroduire une mention positive d'OIDC alors qu'aucun code OIDC
n'existe dans Forge 3.0.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
AUTH_MD = PROJECT_ROOT / "docs" / "auth.md"


class TestAuthMdNoOidcContradiction:
    """docs/auth.md ne se contredit plus sur OIDC."""

    def test_file_exists(self):
        assert AUTH_MD.exists()

    def test_no_phantom_oidc_module_in_table(self):
        """core.auth.oidc n'apparaît plus dans le fichier."""
        text = AUTH_MD.read_text(encoding="utf-8")
        assert "core.auth.oidc" not in text, (
            "docs/auth.md ne doit plus mentionner `core.auth.oidc` "
            "(module retiré par ADR-004 — remplacer par la ligne ❌ non fourni)"
        )

    def test_oidc_not_in_available_features_list(self):
        """La liste 'Les modules Auth/User disponibles couvrent' ne cite pas OIDC."""
        text = AUTH_MD.read_text(encoding="utf-8")
        # Extraire le bloc de la liste des features (entre "disponibles couvrent" et la prochaine ligne vide)
        match = re.search(
            r"disponibles couvrent aujourd'hui\s*:\s*\n(.*?)\n\n",
            text,
            re.DOTALL,
        )
        if match:
            features_block = match.group(1)
            assert "OIDC" not in features_block and "oidc" not in features_block, (
                "La liste 'Les modules Auth/User disponibles couvrent' ne doit pas "
                "lister OIDC comme feature disponible — OIDC n'est pas fourni par Forge 3.0 "
                "(voir section OIDC de auth.md)."
            )

    def test_api_table_tokens_row_preserved(self):
        """core.auth.tokens reste dans la table API (module légitime, existant)."""
        text = AUTH_MD.read_text(encoding="utf-8")
        assert "core.auth.tokens" in text, (
            "docs/auth.md doit conserver `core.auth.tokens` dans la table API "
            "(module existant core/auth/tokens.py — tokens à usage limité)."
        )

    def test_limites_section_says_oidc_not_provided(self):
        """La section OIDC contient une phrase claire indiquant que OIDC n'est pas fourni."""
        text = AUTH_MD.read_text(encoding="utf-8")
        patterns = [
            r"OIDC n'est pas fourni",
            r"OIDC.*non fourni",
            r"not provided.*OIDC",
        ]
        found = any(re.search(p, text, re.IGNORECASE) for p in patterns)
        assert found, (
            "docs/auth.md doit conserver une phrase claire indiquant que OIDC "
            "n'est pas fourni nativement par Forge 3.0 (section ## OIDC)."
        )

    def test_no_link_to_nonexistent_auth_oidc(self):
        """Aucun lien vers docs/auth-oidc.md si ce fichier n'existe pas."""
        oidc_doc = PROJECT_ROOT / "docs" / "auth-oidc.md"
        if oidc_doc.exists():
            return
        text = AUTH_MD.read_text(encoding="utf-8")
        matches = re.findall(r"\]\(.*?auth-oidc(?:\.md)?\)", text)
        assert not matches, (
            f"docs/auth.md contient {len(matches)} lien(s) vers auth-oidc.md "
            f"qui n'existe pas : {matches}"
        )


class TestAuthMdMfaDeprecationConserved:
    """Les notes de dépréciation MFA (Type 3, décision C2) sont conservées."""

    def test_mfa_deprecation_alias_note_present(self):
        """La mention core.auth.mfa comme alias de dépréciation reste dans la table."""
        text = AUTH_MD.read_text(encoding="utf-8")
        assert "core.auth.mfa" in text, (
            "docs/auth.md doit conserver `core.auth.mfa` (alias de dépréciation "
            "documenté dans la table API — décision Type 3 ticket C2)."
        )

    def test_mfa_deprecation_warning_note_present(self):
        """La note DeprecationWarning sur core.auth.mfa est conservée."""
        text = AUTH_MD.read_text(encoding="utf-8")
        has_warning = "DeprecationWarning" in text and "core.auth.mfa" in text
        assert has_warning, (
            "docs/auth.md doit conserver la note DeprecationWarning sur core.auth.mfa "
            "(décision Type 3 ticket C2 — ligne ~434)."
        )
