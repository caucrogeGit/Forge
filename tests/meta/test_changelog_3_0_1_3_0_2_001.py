"""Garde-fou CHANGELOG-3.0.1-3.0.2-001.

Vérifie la cohérence structurelle du CHANGELOG après insertion des sections
[3.0.1] et [3.0.2] :
- [3.0.0] a une date réelle (pas TBD)
- [3.0.1] existe avec la bonne date et les tickets attendus
- [3.0.2] existe en tête comme section Unreleased avec les 12 tickets Scénario C
- L'ordre des sections est cohérent (3.0.2 > 3.0.1 > 3.0.0 > 3.0.0rc1)
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]

PROJECT_ROOT = Path(__file__).parent.parent.parent
CHANGELOG = PROJECT_ROOT / "CHANGELOG.md"


def _text() -> str:
    return CHANGELOG.read_text(encoding="utf-8")


class TestChangelogExists:

    def test_changelog_exists(self):
        assert CHANGELOG.exists()

    def test_changelog_not_empty(self):
        assert len(_text()) > 1000


class TestSection300Date:

    def test_300_has_real_date(self):
        text = _text()
        assert "## [3.0.0] — TBD" not in text, (
            "[3.0.0] a encore la date TBD — elle doit être 2026-05-12"
        )

    def test_300_has_correct_date(self):
        text = _text()
        assert "## [3.0.0] — 2026-05-12" in text


class TestSection301Exists:

    def test_301_section_present(self):
        assert "## [3.0.1] — 2026-05-12" in _text()

    def test_301_has_sessions_lang_align(self):
        assert "SESSIONS-LANG-ALIGN-001" in _text()

    def test_301_has_cli_auth_init(self):
        assert "CLI-AUTH-INIT-OIDC-SQL-001" in _text()

    def test_301_has_packaging_forge_module(self):
        assert "PACKAGING-FORGE-MODULE-001" in _text()

    def test_301_has_release_bump(self):
        assert "RELEASE-3.0.1-PATCH-STABLE-001" in _text()

    @pytest.mark.parametrize("ticket", [
        "DOCS-CLI-COMMANDS-REFERENCE-001",
        "DOCS-INSTALLATION-WINDOWS-001",
        "LANDING-SEARCH-BAR-001",
        "LANDING-POSITIONNEMENT-VISIBILITY-001",
        "DOCS-RELEASE-LOCAL-STARTERS-COUNT-001",
    ])
    def test_301_has_pr_tickets(self, ticket):
        assert ticket in _text(), f"{ticket} absent de la section [3.0.1]"


class TestSection302Exists:

    def test_302_section_present(self):
        text = _text()
        assert "## [3.0.2]" in text

    def test_302_is_released(self):
        """T22 a daté [3.0.2] — la section ne doit plus être Unreleased."""
        import re
        text = _text()
        assert re.search(r"## \[3\.0\.2\]\s+[—-]\s+\d{4}-\d{2}-\d{2}", text), (
            "[3.0.2] doit avoir une date réelle (T22 release)"
        )
        assert "## [3.0.2] — Unreleased" not in text, (
            "[3.0.2] ne doit plus être 'Unreleased' — release T22 effectuée"
        )

    @pytest.mark.parametrize("ticket", [
        "PYTEST-REPRODUCIBLE-001",
        "PACKAGING-SRC-LAYOUT-001",
        "MFA-SECRET-HASH-DEPRECATION-RESOLVE-001",
        "MFA-PRODUCTION-DECISION-001",
        "OIDC-EXCEPTIONS-CLEANUP-001",
        "CORE-RBAC-PLUGIN-MECHANISM-001",
        "PACKAGING-WHEEL-CONTENT-001",
        "STABILITY-CONTRACT-3.0-REFRESH-001",
        "CLAUDE-MD-3.0.2-REFRESH-001",
        "SESSION-KEYS-DOCSTRING-001",
        "ADR-TITLES-3.0-REFRESH-001",
    ])
    def test_302_has_scenario_c_tickets(self, ticket):
        assert ticket in _text(), f"{ticket} absent de la section [3.0.2]"


class TestSectionOrder:

    def test_302_before_301(self):
        text = _text()
        pos_302 = text.index("## [3.0.2]")
        pos_301 = text.index("## [3.0.1]")
        assert pos_302 < pos_301, "[3.0.2] doit apparaître avant [3.0.1]"

    def test_301_before_300(self):
        text = _text()
        pos_301 = text.index("## [3.0.1]")
        pos_300 = text.index("## [3.0.0] —")
        assert pos_301 < pos_300, "[3.0.1] doit apparaître avant [3.0.0]"

    def test_300_before_rc1(self):
        text = _text()
        pos_300 = text.index("## [3.0.0] —")
        pos_rc1 = text.index("## [3.0.0rc1]")
        assert pos_300 < pos_rc1, "[3.0.0] doit apparaître avant [3.0.0rc1]"

    def test_latest_at_top_after_header(self):
        """La première section doit être la plus récente, par sa date.

        Cette vérification s'appuyait sur une liste de sections acceptables
        écrite en dur, qu'il fallait allonger à chaque release et qui a
        justement fait échouer le passage en rc3.
        L'ordre se lit maintenant dans le fichier lui-même, par comparaison des
        dates : rien à maintenir, et la garantie est plus forte qu'avec une
        liste, qui n'attrapait pas une section insérée au mauvais endroit
        (RELEASE-VERSION-BUMP-RC3-001).
        """
        text = _text()
        entetes = re.findall(
            r"^## \[([^\]]+)\](?:\s*[\u2014\-:]\s*(\d{4}-\d{2}-\d{2}))?",
            text, re.MULTILINE)
        assert entetes, "Aucune section ## trouvée"

        premiere, premiere_date = entetes[0]
        if premiere == "Non publié":
            return

        assert premiere_date, (
            f"La première section « {premiere} » n'a pas de date : impossible "
            "de vérifier qu'elle est la plus récente."
        )
        plus_recente = max(date for _, date in entetes if date)
        assert premiere_date == plus_recente, (
            f"La première section est « {premiere} » du {premiere_date}, alors "
            f"que le fichier contient une section du {plus_recente}."
        )
