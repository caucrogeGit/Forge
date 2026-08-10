"""Garde-fou ROADMAP-B10-CONSISTENCY-SWEEP-001.

Verrouille la cohérence de la section Phase B10 de
``docs/roadmap/forge-roadmap.md`` :

  * la section ``## Phase B10`` existe ;
  * les 5 sous-sections officielles sont présentes et dans l'ordre attendu
    (Bloquants immédiats → Critiques pré-RC → Durcissement et garde-fous →
    Cohérence release → Clôture) ;
  * aucune mention obsolète de compteur fragile (``15 tickets ci-dessus``,
    ``16 tickets``, ``Durcissement (7 tickets)``) ne subsiste ;
  * tous les tickets ajoutés en cours de phase sont présents dans la
    section B10 (avec le bon statut) ;
  * ``B10-CLOSING-AUDIT-001`` apparaît AVANT ``RELEASE-BETA10-001``.

Les assertions visent la **structure et les marqueurs sémantiques**, pas
le texte exact. La roadmap reste réécrivable éditorialement.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]


_REPO_ROOT = Path(__file__).resolve().parents[2]
_ROADMAP = _REPO_ROOT / "docs" / "roadmap" / "forge-roadmap.md"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def roadmap_text() -> str:
    assert _ROADMAP.is_file(), f"{_ROADMAP.relative_to(_REPO_ROOT)} doit exister."
    return _ROADMAP.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def b10_section(roadmap_text: str) -> str:
    """Renvoie le bloc de texte de la phase B10 — depuis l'en-tête
    ``## Phase B10`` jusqu'à la section H2 suivante."""
    match = re.search(r"^##\s+Phase B10.*$", roadmap_text, re.MULTILINE)
    assert match is not None, "Section `## Phase B10` introuvable dans la roadmap."
    rest = roadmap_text[match.start():]
    next_h2 = re.search(r"\n##\s+", rest[1:])  # +1 pour sauter l'H2 courant
    return rest[: next_h2.start() + 1] if next_h2 else rest


# ---------------------------------------------------------------------------
# Structure de la phase B10
# ---------------------------------------------------------------------------


class TestB10SectionStructure:
    def test_phase_header_present(self, roadmap_text):
        assert re.search(r"^##\s+Phase B10\b", roadmap_text, re.MULTILINE), (
            "L'en-tête `## Phase B10` doit exister dans la roadmap."
        )

    @pytest.mark.parametrize("subheading", [
        "Bloquants immédiats",
        "Critiques pré-RC",
        "Durcissement et garde-fous",
        "Cohérence release",
        "Clôture",
    ])
    def test_subsection_present(self, b10_section, subheading):
        assert re.search(
            rf"^###\s+{re.escape(subheading)}\b",
            b10_section,
            re.MULTILINE,
        ), (
            f"La sous-section `### {subheading}` doit exister dans Phase B10."
        )

    def test_subsections_ordered_correctly(self, b10_section):
        """Les 5 sous-sections officielles apparaissent dans l'ordre."""
        order_expected = [
            "Bloquants immédiats",
            "Critiques pré-RC",
            "Durcissement et garde-fous",
            "Cohérence release",
            "Clôture",
        ]
        positions = []
        for name in order_expected:
            m = re.search(
                rf"^###\s+{re.escape(name)}\b",
                b10_section,
                re.MULTILINE,
            )
            assert m is not None, f"Sous-section `### {name}` manquante."
            positions.append((name, m.start()))
        sorted_positions = sorted(positions, key=lambda x: x[1])
        actual_order = [name for name, _ in sorted_positions]
        assert actual_order == order_expected, (
            f"Sous-sections B10 mal ordonnées : reçu {actual_order!r}, "
            f"attendu {order_expected!r}."
        )


# ---------------------------------------------------------------------------
# Compteurs fragiles bannis
# ---------------------------------------------------------------------------


class TestNoFragileCounters:
    """Les compteurs littéraux du type `(7 tickets)`, `15 tickets ci-dessus`,
    `Total Phase B10 : 16 tickets prévus` étaient incohérents avec l'état
    réel après ajouts hors-audit. On ne veut plus AUCUN compteur littéral
    dans la phase B10 — la structure suffit."""

    _FORBIDDEN_PATTERNS = (
        r"15 tickets ci-dessus",
        r"16 tickets",
        r"17 tickets",
        r"Durcissement\s*\(\d+\s*tickets?\)",
        r"Critiques pré-RC\s*\(\d+\s*tickets?\)",
        r"Bloquants immédiats\s*\(\d+\s*tickets?\)",
        r"Clôture\s*\(\d+\s*tickets?\)",
        r"Total Phase B10\s*:\s*\d+\s*tickets?",
    )

    @pytest.mark.parametrize("pattern", _FORBIDDEN_PATTERNS)
    def test_pattern_absent_from_b10(self, b10_section, pattern):
        assert not re.search(pattern, b10_section), (
            f"Compteur fragile détecté dans la phase B10 : pattern "
            f"`{pattern}`. Retirer le compteur littéral — la structure "
            "par sous-sections suffit."
        )


# ---------------------------------------------------------------------------
# Tickets attendus en B10
# ---------------------------------------------------------------------------


_EXPECTED_DELIVERED_B10 = [
    # Bloquants immédiats
    "AUTH-SESSION-HARDENING-TESTS-ALIGN-001",
    "RELEASE-VALIDATE-PEP440-SEMVERSION-001",
    "DOCS-OPTINS-PYPI-BETA9-SWEEP-001",
    # Critiques pré-RC
    "WSGI-SECURITY-HEADERS-001",
    "TESTS-OPTIN-IMPORTORSKIP-001",
    "CI-PAGES-MKDOCS-STRICT-001",
    "DEPENDENCY-AUDIT-RELEASE-GUARD-001",
    # Durcissement et garde-fous
    "UPLOADS-SYMLINK-DEFENSE-001",
    "MFA-SECRET-KEY-BOOT-VALIDATION-001",
    "APP-PY-PROD-HOST-GUARD-001",
    "DOCS-CLI-COMMANDS-EXAMPLES-RESTRUCTURE-001",
    "DOCS-IMPORTS-VALIDITY-SWEEP-001",
    "DOCS-SITE-ARTIFACT-POLICY-001",
    "TESTS-AUTOUSE-FIXTURES-AUDIT-001",
    "LANDING-CONTACT-NAV-FORM-001",
    "ENV-PROD-DB-ADMIN-SECRETS-POLICY-001",
    # Cohérence release
    "RELEASE-VALIDATE-PATH-ROBUSTNESS-001",
    "ROADMAP-B10-CONSISTENCY-SWEEP-001",
    "RELEASE-TAG-CONVENTION-TEST-ALIGN-001",
    # Clôture (livré quand l'audit a conclu GO)
    "B10-CLOSING-AUDIT-001",
    # Release (livré une fois la beta.10 préparée et taguée localement)
    "RELEASE-BETA10-001",
]

_EXPECTED_PENDING_B10: list[str] = []


class TestExpectedTicketsPresent:
    @pytest.mark.parametrize("ticket", _EXPECTED_DELIVERED_B10)
    def test_delivered_ticket_marked_livre(self, b10_section, ticket):
        # On cherche la ligne du tableau contenant le ticket + statut **livré**.
        pattern = rf"\|\s*`{re.escape(ticket)}`\s*\|\s*\*\*livré\*\*\s*\|"
        assert re.search(pattern, b10_section), (
            f"Le ticket `{ticket}` doit apparaître en B10 avec le statut "
            "« **livré** »."
        )

    def test_pending_ticket_marked_a_faire(self, b10_section):
        """Chaque ticket encore à faire apparaît en B10 avec ce statut.

        Écrit en boucle et non en `parametrize` (`TESTS-DEAD-SKIPS-REVIVE-001`).
        `_EXPECTED_PENDING_B10` est vide, tous les tickets B10 étant livrés, et
        une paramétrisation vide rend un test **sauté**, donc invisible. La
        liste vide est justement l'état qu'on veut voir tenir.
        """
        manquants: list[str] = []
        for ticket in _EXPECTED_PENDING_B10:
            pattern = rf"\|\s*`{re.escape(ticket)}`\s*\|\s*à faire\s*\|"
            if not re.search(pattern, b10_section):
                manquants.append(ticket)
        assert not manquants, (
            "Ces tickets doivent apparaître en B10 avec le statut « à faire » : "
            + ", ".join(manquants)
        )


# ---------------------------------------------------------------------------
# Ordre des tickets de clôture
# ---------------------------------------------------------------------------


class TestClosureTicketsOrder:
    def test_closing_audit_before_release(self, b10_section):
        """`B10-CLOSING-AUDIT-001` doit précéder `RELEASE-BETA10-001` —
        on audite avant de releaser."""
        idx_audit = b10_section.find("B10-CLOSING-AUDIT-001")
        idx_release = b10_section.find("RELEASE-BETA10-001")
        assert idx_audit > 0, "B10-CLOSING-AUDIT-001 absent de B10."
        assert idx_release > 0, "RELEASE-BETA10-001 absent de B10."
        assert idx_audit < idx_release, (
            "B10-CLOSING-AUDIT-001 doit précéder RELEASE-BETA10-001 dans la "
            "section Clôture — on audite avant de releaser, jamais l'inverse."
        )


# ---------------------------------------------------------------------------
# Corrections terrain hors-audit conservées
# ---------------------------------------------------------------------------


class TestTerrainCorrectionsKept:
    """Les corrections terrain TLS (hors audit B10 initial) doivent rester
    documentées dans une sous-section dédiée."""

    def test_terrain_subsection_exists(self, b10_section):
        assert re.search(
            r"^###\s+Corrections terrain hors-audit",
            b10_section,
            re.MULTILINE,
        ), "La sous-section `### Corrections terrain hors-audit` doit exister."

    @pytest.mark.parametrize("ticket", [
        "APP-PY-TLS-HANDSHAKE-PER-THREAD-001",
        "APP-PY-TLS-HANDSHAKE-DOCS-001",
    ])
    def test_terrain_ticket_present(self, b10_section, ticket):
        assert ticket in b10_section, (
            f"Ticket terrain `{ticket}` absent de la sous-section "
            "« Corrections terrain hors-audit »."
        )
