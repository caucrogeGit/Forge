"""Garde-fou VERSION-COHERENCE-1.0-001.

Vérifie que les documents publics actifs ne contiennent pas de références
de version trompeuses présentant la trajectoire 3.x comme actuelle ou future.

Ce garde-fou ne s'applique pas aux fichiers d'historique (docs/history/),
au CHANGELOG, aux ADR (qui comportent leurs propres avertissements historiques),
ni à l'historique git.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent

# Documents publics actifs susceptibles de contenir des références trompeuses.
# Ne pas inclure docs/history/, CHANGELOG.md, ni docs/adr/.
PUBLIC_DOCS = [
    PROJECT_ROOT / "docs" / "stability-contract.md",
    PROJECT_ROOT / "docs" / "release-policy.md",
    PROJECT_ROOT / "docs" / "auth.md",
    PROJECT_ROOT / "docs" / "deployment.md",
    PROJECT_ROOT / "docs" / "deprecation-policy.md",
    PROJECT_ROOT / "docs" / "lts-policy.md",
]

# Patterns interdits : version 3.x présentée comme trajectoire actuelle ou future
_FORBIDDEN = [
    # Publication PyPI annoncée comme prévue en 3.1
    (r"[Pp]r[ée]vue 3\.1\+", "Publication opt-in annoncée 'Prévue 3.1+' — utiliser '1.0.0-beta.5'"),
    # Version explicite 3.1.0 attachée à un ticket
    (r"SEC-MFA-SECRET-ENCRYPTION-001\s*\(3\.", "Ticket MFA avec version '3.1.0' — utiliser 'post-1.0'"),
    # Commande d'installation opt-in avec version 3.1
    (r"disponible sur PyPI en 3\.1\b", "Mention 'disponible sur PyPI en 3.1' — obsolète"),
    # Titre de document annonçant 'Forge 3.x'
    (r"^#\s+Contrat de stabilit[eé]\s+Forge 3\.", "Titre du contrat de stabilité encore en 3.x"),
]


class TestNoMisleadingVersionReferences:
    """Les documents publics actifs ne contiennent pas de références 3.x trompeuses."""

    @pytest.mark.parametrize("doc_path", PUBLIC_DOCS, ids=[p.name for p in PUBLIC_DOCS])
    def test_no_misleading_3x_version(self, doc_path: Path):
        if not doc_path.exists():
            pytest.skip(f"{doc_path.name} n'existe pas")
        text = doc_path.read_text(encoding="utf-8")
        violations = []
        for pattern, description in _FORBIDDEN:
            if re.search(pattern, text, re.MULTILINE):
                violations.append(f"  • {description}  [{pattern}]")
        assert not violations, (
            f"{doc_path.name} contient des références de version 3.x trompeuses :\n"
            + "\n".join(violations)
        )


class TestStabilityContractIsFor1x:
    """Le contrat de stabilité décrit la série 1.x, pas 3.x."""

    def test_title_mentions_1x(self):
        doc = PROJECT_ROOT / "docs" / "stability-contract.md"
        if not doc.exists():
            pytest.skip("stability-contract.md n'existe pas")
        text = doc.read_text(encoding="utf-8")
        assert "Forge 1.x" in text, (
            "docs/stability-contract.md doit mentionner 'Forge 1.x' comme série courante."
        )

    def test_title_not_3x(self):
        doc = PROJECT_ROOT / "docs" / "stability-contract.md"
        if not doc.exists():
            pytest.skip("stability-contract.md n'existe pas")
        first_line = doc.read_text(encoding="utf-8").splitlines()[0]
        assert "3.x" not in first_line, (
            f"Le titre du contrat de stabilité contient encore '3.x' : {first_line!r}"
        )


class TestReleasePolicyOptInVersions:
    """La release-policy référence la trajectoire 1.0.0-beta.5 pour les opt-ins."""

    def test_optin_publication_references_beta5(self):
        doc = PROJECT_ROOT / "docs" / "release-policy.md"
        if not doc.exists():
            pytest.skip("release-policy.md n'existe pas")
        text = doc.read_text(encoding="utf-8")
        assert "1.0.0-beta.5" in text, (
            "docs/release-policy.md doit mentionner '1.0.0-beta.5' "
            "comme cible de publication coordonnée des opt-ins."
        )


class TestRoadmapActiveSection:
    """La roadmap publique ne présente pas 3.x comme trajectoire active ou future."""

    def test_no_beyond_3x(self):
        roadmap = PROJECT_ROOT / "docs" / "roadmap" / "forge-roadmap.md"
        if not roadmap.exists():
            pytest.skip("forge-roadmap.md n'existe pas")
        text = roadmap.read_text(encoding="utf-8")
        assert "au-delà de 3.0" not in text, (
            "forge-roadmap.md contient 'au-delà de 3.0' — "
            "utiliser 'au-delà de la version 1.0.0 stable'."
        )

    def test_trajectory_mentions_beta6(self):
        roadmap = PROJECT_ROOT / "docs" / "roadmap" / "forge-roadmap.md"
        if not roadmap.exists():
            pytest.skip("forge-roadmap.md n'existe pas")
        text = roadmap.read_text(encoding="utf-8")
        assert "1.0.0-beta.6" in text, (
            "forge-roadmap.md doit mentionner '1.0.0-beta.6' "
            "comme T0 des tests terrain (conforme ADR-009)."
        )

    def test_trajectory_mentions_rc1(self):
        roadmap = PROJECT_ROOT / "docs" / "roadmap" / "forge-roadmap.md"
        if not roadmap.exists():
            pytest.skip("forge-roadmap.md n'existe pas")
        text = roadmap.read_text(encoding="utf-8")
        assert "1.0.0-rc1" in text, (
            "forge-roadmap.md doit mentionner '1.0.0-rc1' "
            "comme étape avant stable (conforme ADR-009)."
        )
