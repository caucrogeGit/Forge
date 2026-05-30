"""Garde-fou DOC-INSTALL-INDEX-SIX-OPTINS-001.

Forge compte **six** modules opt-in officiels : mfa, rbac, workflow,
stats, media, iot. Plusieurs docs « état courant » affirmaient encore
« 4 modules opt-in » ou « cinq opt-ins » après l'ajout de media puis iot.

Ce garde-fou empêche la réapparition d'un compte périmé dans les
documents qui décrivent l'état COURANT. Il **exclut volontairement** les
archives narratives (``docs/roadmap/``, ``docs/history/``, ``CHANGELOG.md``)
où une mention historique de « 4 opt-ins » (état d'une version passée)
reste légitime — voir charte v2, ``docs/history/`` = mémoire brute.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent

# Docs décrivant l'état COURANT de Forge (pas les archives versionnées).
CURRENT_STATE_DOCS = [
    "README.md",
    "CONTRIBUTING.md",
    "CHARTE_DOC.md",
    "docs/install/index.md",
    "docs/install/core-dev.md",
    "docs/release/release-policy.md",
]

# Tournures qui figent un compte d'opt-ins périmé comme état courant.
FORBIDDEN_COUNTS = [
    "4 modules opt-in",
    "4 opt-in",
    "quatre modules opt-in",
    "5 modules opt-in",
    "cinq opt-ins",
    "5 opt-ins officiels",
    "les cinq opt-ins",
]

EXPECTED_OPTINS = [
    "forge-mvc-mfa",
    "forge-mvc-rbac",
    "forge-mvc-workflow",
    "forge-mvc-stats",
    "forge-mvc-media",
    "forge-mvc-iot",
]


@pytest.mark.parametrize("doc", CURRENT_STATE_DOCS)
def test_no_stale_optin_count(doc):
    path = PROJECT_ROOT / doc
    if not path.exists():
        pytest.skip(f"{doc} absent")
    text = path.read_text(encoding="utf-8")
    offenders = [phrase for phrase in FORBIDDEN_COUNTS if phrase in text]
    assert not offenders, (
        f"{doc} fige un compte d'opt-ins périmé (il y en a six) : {offenders}"
    )


def test_release_policy_lists_all_six_optins():
    text = (PROJECT_ROOT / "docs" / "release" / "release-policy.md").read_text(encoding="utf-8")
    missing = [m for m in EXPECTED_OPTINS if m not in text]
    assert not missing, (
        f"docs/release/release-policy.md ne mentionne pas tous les opt-ins : {missing}"
    )
