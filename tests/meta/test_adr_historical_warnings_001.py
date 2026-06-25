"""Garde-fou ADR-TITLES-3.0-REFRESH-001 (modifié — Option 2).

Vérifie la cohérence des ADR datés par version Forge :
- Tout ADR dont le titre contient 'Forge X.x' DOIT avoir un avertissement
  historique 'ADR historique' dans ses premières lignes
- L'avertissement et le titre doivent mentionner la MÊME version
- Les ADR avec titre daté sont des archives — leur titre n'est pas bumpé
  avec la version courante (différent de la doc active : T7/T8/T9)

Origine : audit F10 proposait de bumper Forge 2.x → Forge 3.x dans les
titres ADR-001 et ADR-002. Reconnaissance T17 a révélé que ces ADR ont
déjà des warnings historiques cohérents. Décision révisée : conserver
les titres datés (Principe 11 — legacy doit être daté).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
ADR_DIR = PROJECT_ROOT / "docs" / "adr"

TITLE_WITH_VERSION_PATTERN = re.compile(
    r"^#\s+ADR-\d+\s+.+\s+Forge\s+(\d+\.\d+|\d+\.x)\s*$",
    re.MULTILINE,
)

WARNING_PATTERN = re.compile(
    r'!!!\s*warning\s+"ADR\s+historique\s*[—\-:]\s*Forge\s+(\d+\.\d+|\d+\.x)"',
)


def _get_adr_files() -> list[Path]:
    return sorted([
        p for p in ADR_DIR.glob("*.md")
        if p.name not in ("README.md", "index.md")
    ])


class TestAdrFilesExist:

    def test_adr_dir_exists(self):
        assert ADR_DIR.exists()

    def test_at_least_8_adr(self):
        adrs = _get_adr_files()
        assert len(adrs) >= 8, (
            f"Au moins 8 ADR attendus, trouvé {len(adrs)} : "
            f"{[p.name for p in adrs]}"
        )


class TestAdrDatedTitlesHaveHistoricalWarning:

    def test_adr_001_has_historical_warning(self):
        adr = ADR_DIR / "001-auth-strategy.md"
        text = adr.read_text(encoding="utf-8")

        title_match = TITLE_WITH_VERSION_PATTERN.search(text)
        assert title_match, "ADR-001 titre attendu avec mention 'Forge X.x' (archive datée)."
        title_version = title_match.group(1)

        warning_match = WARNING_PATTERN.search(text)
        assert warning_match, (
            f"ADR-001 titre mentionne Forge {title_version} mais aucun warning "
            f"'!!! warning \"ADR historique — Forge X.x\"' trouvé."
        )

        assert title_match.group(1) == warning_match.group(1), (
            f"ADR-001 incohérence : titre = 'Forge {title_match.group(1)}', "
            f"warning = 'Forge {warning_match.group(1)}'. Doivent matcher."
        )

    def test_adr_002_has_historical_warning(self):
        adr = ADR_DIR / "002-session-strategy.md"
        text = adr.read_text(encoding="utf-8")

        title_match = TITLE_WITH_VERSION_PATTERN.search(text)
        assert title_match, "ADR-002 titre attendu avec mention 'Forge X.x' (archive datée)."
        title_version = title_match.group(1)

        warning_match = WARNING_PATTERN.search(text)
        assert warning_match, (
            f"ADR-002 titre mentionne Forge {title_version} mais aucun warning "
            f"'!!! warning \"ADR historique — Forge X.x\"' trouvé."
        )

        assert title_match.group(1) == warning_match.group(1), (
            f"ADR-002 incohérence : titre = 'Forge {title_match.group(1)}', "
            f"warning = 'Forge {warning_match.group(1)}'. Doivent matcher."
        )


class TestAllDatedAdrsAreConsistent:

    def test_all_dated_adrs_have_consistent_warning(self):
        violations = []
        for adr in _get_adr_files():
            text = adr.read_text(encoding="utf-8")
            title_match = TITLE_WITH_VERSION_PATTERN.search(text)
            if not title_match:
                continue
            title_version = title_match.group(1)
            warning_match = WARNING_PATTERN.search(text)
            if not warning_match:
                violations.append(
                    f"{adr.name} : titre = 'Forge {title_version}', "
                    f"aucun warning historique"
                )
                continue
            warning_version = warning_match.group(1)
            if title_version != warning_version:
                violations.append(
                    f"{adr.name} : titre = 'Forge {title_version}', "
                    f"warning = 'Forge {warning_version}' (incohérent)"
                )
        assert not violations, (
            "ADR datés sans warning cohérent :\n  " + "\n  ".join(violations)
        )


class TestUndatedAdrsHaveNoVersionInTitle:

    @pytest.mark.parametrize("name", [
        "003-language-convention.md",
        "004-core-perimeter.md",
        "005-packaging.md",
        "006-python-version.md",
        "007-charter-v2-adoption.md",
        "008-auth-audit-architecture.md",
    ])
    def test_undated_adr_has_no_version_title(self, name):
        adr = ADR_DIR / name
        if not adr.exists():
            pytest.skip(f"{name} absent")
        text = adr.read_text(encoding="utf-8")
        title_match = TITLE_WITH_VERSION_PATTERN.search(text)
        assert not title_match, (
            f"{name} a un titre daté 'Forge X.x' mais ne devrait pas. "
            f"Si la décision a été prise pour une version précise, "
            f"ajouter le warning historique correspondant."
        )
