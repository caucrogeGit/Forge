"""Garde-fou CONTRIBUTING-MAIN-BRANCH-001.

Vérifie que les pages d'onboarding contributeur référencent la branche `main`
et non `master`. Sans ce garde-fou, CONTRIBUTING.md a historiquement dit
'créez une branche depuis master' alors que la branche principale est `main`,
bloquant tout nouveau contributeur dès la première commande git.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent

ONBOARDING_PAGES = [
    PROJECT_ROOT / "CONTRIBUTING.md",
    PROJECT_ROOT / "README.md",
    PROJECT_ROOT / "docs" / "philosophy" / "contributing.md",
]

_MASTER_PATTERNS = [
    re.compile(r"\bmaster\b\s*[:`]"),
    re.compile(r"branche\s+depuis\s+`?master"),
    re.compile(r"\bbranch\s+master\b"),
    re.compile(r"\bcheckout\s+master\b"),
    re.compile(r"\bcheckout\s+-b\s+\S+\s+master\b"),
    re.compile(r"--branch\s+master\b"),
    re.compile(r"\borigin/master\b"),
]


class TestOnboardingReferencesMainBranch:
    """Les pages d'onboarding ne référencent pas la branche `master`."""

    def test_files_exist(self):
        for page in ONBOARDING_PAGES:
            assert page.exists(), f"{page.relative_to(PROJECT_ROOT)} doit exister"

    def test_no_master_branch_in_onboarding_commands(self):
        for page in ONBOARDING_PAGES:
            text = page.read_text(encoding="utf-8")
            for line_no, line in enumerate(text.splitlines(), start=1):
                for pat in _MASTER_PATTERNS:
                    if pat.search(line):
                        raise AssertionError(
                            f"{page.relative_to(PROJECT_ROOT)}:{line_no} référence "
                            f"la branche `master`. La branche principale est `main`. "
                            f"Ligne : {line!r}"
                        )

    def test_contributing_mentions_main_explicitly(self):
        text = (PROJECT_ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
        assert "depuis `main`" in text or "from `main`" in text or "branche `main`" in text, (
            "CONTRIBUTING.md doit dire explicitement aux contributeurs de "
            "partir depuis la branche `main`"
        )
