"""Garde-fou LANDING-LICENSE-WORDING-001.

Vérifie que la landing (source et générée) n'affiche pas « Open source », qui
serait juridiquement faux : Forge est sous licence propriétaire / source
disponible (voir LICENSE).

Mentions tolérées :
- docs/adr/003-language-convention.md : référence à l'écosystème global
- docs/philosophy/licence.md : phrase qui PRÉCISE que Forge n'est PAS open source
- CHANGELOG.md, docs/history/, docs/history/audits/ : historique
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent

LANDING_SOURCE = PROJECT_ROOT / "docs" / "index.html"
LANDING_GENERATED = PROJECT_ROOT / "docs" / "index.html"

_OPEN_SOURCE = re.compile(r"\bopen[\s-]source\b", re.IGNORECASE)
_NEGATIVE = re.compile(r"(n'est pas|not)\s+open[\s-]source", re.IGNORECASE)


def _problematic_lines(text: str) -> list[tuple[int, str]]:
    return [
        (i + 1, line)
        for i, line in enumerate(text.splitlines())
        if _OPEN_SOURCE.search(line) and not _NEGATIVE.search(line)
    ]


class TestLandingDoesNotClaimOpenSource:
    """La landing ne prétend pas être 'open source'."""

    def test_landing_source_no_open_source_claim(self):
        assert LANDING_SOURCE.exists(), f"{LANDING_SOURCE.relative_to(PROJECT_ROOT)} doit exister"
        hits = _problematic_lines(LANDING_SOURCE.read_text(encoding="utf-8"))
        assert not hits, (
            "docs/index.html affirme 'open source' : "
            + ", ".join(f"L.{n}: {line.strip()!r}" for n, line in hits)
            + " — Forge est sous licence propriétaire / source disponible (cf. LICENSE)"
        )

    def test_landing_generated_no_open_source_claim(self):
        """Si ce test échoue alors que la source est propre, lancer `forge sync:landing`."""
        assert LANDING_GENERATED.exists(), f"{LANDING_GENERATED.relative_to(PROJECT_ROOT)} doit exister"
        hits = _problematic_lines(LANDING_GENERATED.read_text(encoding="utf-8"))
        assert not hits, (
            "docs/index.html affirme 'open source' : "
            + ", ".join(f"L.{n}: {line.strip()!r}" for n, line in hits)
            + " — Régénérer via `forge sync:landing`"
        )

    def test_landing_uses_source_disponible_terminology(self):
        text = LANDING_SOURCE.read_text(encoding="utf-8")
        assert "source disponible" in text.lower(), (
            "docs/index.html devrait utiliser 'Source disponible' "
            "pour décrire la nature de la licence (cohérent avec LICENSE)"
        )


class TestLicenseDocumentIsAuthoritative:
    """Le LICENSE racine reste la source de vérité sur la nature de la licence."""

    def test_license_says_proprietary_source_available(self):
        text = (PROJECT_ROOT / "LICENSE").read_text(encoding="utf-8")
        assert "propriétaire" in text.lower(), (
            "LICENSE doit indiquer clairement le caractère propriétaire"
        )
        assert "source disponible" in text.lower() or "source-available" in text.lower(), (
            "LICENSE doit utiliser 'source disponible' pour décrire l'accès au code"
        )
