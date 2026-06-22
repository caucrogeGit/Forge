"""Garde-fou DOCS-FORGE-2X-SWEEP-001.

Vérifie qu'aucune mention 'Forge 2.x' active (présent obsolète)
ne reste dans la doc de référence.

Mentions LÉGITIMES conservées :
- Titres ADR datés (cohérence T17)
- 'Depuis Forge X.Y.Z' (date d'introduction historique)
- 'Forge 2.x → 3.x' (politique de migration)
- Roadmap, deprecation-policy, lts-policy : historique de version

Mentions INTERDITES :
- 'Forge 2.x utilise/fournit/impose/...' (présent obsolète)
- 'restent officielles en Forge 2.x' (présent obsolète)
- 'conventions de Forge 2.x' (présent obsolète)

Origine : audit F27 — sweep final des 4 mentions actives obsolètes
restantes après T7/T8/T9/T13.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
# Doc des opt-ins embarquée par paquet (ADR-038) : balayée aussi.
PACKAGES_DIR = PROJECT_ROOT / "packages"

EXCLUDED_PATHS = [
    "docs/history",
    "docs/audits",
    "docs/adr",
    "docs/roadmap",
    "docs/release/deprecation-policy.md",
    "docs/release/lts-policy.md",
    "docs/features/migration-guide.md",
    "docs/release/release-policy.md",
]

ACTIVE_FORGE_2X_PATTERNS = [
    re.compile(r"Forge 2\.x\s+utilise\b", re.IGNORECASE),
    re.compile(r"Forge 2\.x\s+fournit\b", re.IGNORECASE),
    re.compile(r"Forge 2\.x\s+impose\b", re.IGNORECASE),
    re.compile(r"Forge 2\.x\s+exige\b", re.IGNORECASE),
    re.compile(r"Forge 2\.x\s+supporte\b", re.IGNORECASE),
    re.compile(r"Forge 2\.x\s+propose\b", re.IGNORECASE),
    re.compile(r"restent?\s+officielles?\s+en\s+Forge 2\.x", re.IGNORECASE),
    re.compile(r"conventions?\s+contractuelles?\s+de\s+Forge 2\.x", re.IGNORECASE),
    re.compile(r"actuellement\s+en\s+Forge 2\.x", re.IGNORECASE),
    re.compile(r"version\s+courante\s+Forge 2\.x", re.IGNORECASE),
]


def _is_excluded(path: Path) -> bool:
    rel_str = str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
    return any(rel_str.startswith(exc) for exc in EXCLUDED_PATHS)


def _find_active_doc_files() -> list[Path]:
    roots = [DOCS_DIR, *sorted(PACKAGES_DIR.glob("*/docs"))]
    return [
        p
        for root in roots
        for p in root.rglob("*.md")
        if not _is_excluded(p)
    ]


class TestNoActiveForge2XInDocs:
    """Les 4 mentions actives obsolètes ciblées ont été bumpées."""

    def test_auth_md_api_officielle_mentions_3x(self):
        """docs/features/auth.md : 'Depuis Forge 2.x, l'API officielle' mentionne aussi 3.x."""
        text = (DOCS_DIR / "features" / "auth.md").read_text(encoding="utf-8")
        for match in re.finditer(
            r"Depuis Forge 2\.x,?\s+l['']API officielle[^.]*\.",
            text,
        ):
            context = text[match.start():match.start() + 300]
            assert "Forge 3" in context or "3.x" in context, (
                f"Mention 'Depuis Forge 2.x, l'API officielle' sans mention 3.x. "
                f"Contexte : {context[:200]}"
            )

    def test_auth_md_briques_restent_officielles_3x(self):
        """docs/features/auth.md : 'restent officielles' en Forge 3.x, plus 2.x."""
        text = (DOCS_DIR / "features" / "auth.md").read_text(encoding="utf-8")
        assert not re.search(
            r"restent?\s+officielles?\s+en\s+Forge 2\.x", text, re.IGNORECASE
        ), (
            "docs/features/auth.md : 'restent officielles en Forge 2.x' doit être "
            "bumpé en 'Forge 3.x' (T20-B)."
        )

    def test_deployment_md_no_forge_2x_utilise(self):
        """docs/deployment/deployment.md : 'Forge 2.x utilise' bumpé en 'Forge 3.x'."""
        text = (DOCS_DIR / "deployment" / "deployment.md").read_text(encoding="utf-8")
        assert not re.search(r"Forge 2\.x\s+utilise\b", text, re.IGNORECASE), (
            "docs/deployment/deployment.md : 'Forge 2.x utilise...' doit être "
            "bumpé en 'Forge 3.x utilise...' (T20-C)."
        )

    def test_api_md_no_conventions_2x(self):
        """docs/reference/api.md : 'conventions contractuelles de Forge 2.x' bumpé."""
        text = (DOCS_DIR / "reference" / "api.md").read_text(encoding="utf-8")
        assert not re.search(
            r"conventions?\s+contractuelles?\s+de\s+Forge 2\.x", text, re.IGNORECASE
        ), (
            "docs/reference/api.md : 'conventions contractuelles de Forge 2.x' "
            "doit être bumpé en 'Forge 3.x' (T20-D)."
        )


class TestNoActiveForge2XAcrossDocs:
    """Aucune mention active 'Forge 2.x' (verbe présent) dans la doc active."""

    def test_no_active_patterns_in_active_docs(self):
        violations = []
        for doc in _find_active_doc_files():
            try:
                text = doc.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                continue
            for pattern in ACTIVE_FORGE_2X_PATTERNS:
                for match in pattern.finditer(text):
                    line_num = text[:match.start()].count("\n") + 1
                    violations.append(
                        f"{doc.relative_to(PROJECT_ROOT)}:{line_num} : "
                        f"'{match.group()}'"
                    )
        assert not violations, (
            "Mentions 'Forge 2.x' actives (présent obsolète) détectées :\n  "
            + "\n  ".join(violations[:20])
            + ("\n  ..." if len(violations) > 20 else "")
            + "\n\nBumper en 'Forge 3.x' ou reformuler au passé/historique."
        )


class TestHistoricalMentionsPreserved:
    """L'extraction de chaque module reste mentionnée (sans numéro de version
    interne 2.x, purgé : DOCS-PURGE-HISTORY-001)."""

    @pytest.mark.parametrize("doc_path,expected_mention", [
        # ADR-042 : features/auth.md ne porte plus la mention d'extraction MFA
        # (section MFA retirée du cœur). La mention reste dans la doc de l'opt-in.
        ("../packages/forge-mvc-mfa/docs/reference.md", "Module extrait"),
        # forge-mvc-stats : doc embarquée par paquet (ADR-038).
        ("../packages/forge-mvc-stats/docs/reference.md", "Module extrait"),
        ("../packages/forge-mvc-workflow/docs/reference.md", "Module extrait"),
    ])
    def test_historical_extraction_mention_preserved(
        self, doc_path: str, expected_mention: str
    ):
        path = DOCS_DIR / doc_path
        if not path.exists():
            pytest.skip(f"{doc_path} absent")
        text = path.read_text(encoding="utf-8")
        assert expected_mention in text, (
            f"{doc_path} : mention historique '{expected_mention}' attendue mais "
            f"manquante. T20 ne doit PAS retirer les références historiques "
            f"d'extraction de modules."
        )
