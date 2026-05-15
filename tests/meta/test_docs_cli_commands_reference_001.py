"""Garde-fou DOCS-CLI-COMMANDS-REFERENCE-001.

Vérifie que la référence CLI documente les commandes principales et est
correctement intégrée à la navigation mkdocs.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
REFERENCE_PATH = PROJECT_ROOT / "docs" / "reference" / "cli-commands.md"


class TestCliReferenceExists:

    def test_file_exists(self):
        assert REFERENCE_PATH.exists(), (
            "docs/reference/cli-commands.md doit exister."
        )

    def test_has_three_invocation_modes(self):
        text = REFERENCE_PATH.read_text(encoding="utf-8")
        for mode in ["python -m forge", "python forge.py", "forge "]:
            assert mode in text, (
                f"Mode `{mode}` manquant dans la référence CLI."
            )


class TestCoreCommandsDocumented:

    EXPECTED_COMMANDS = [
        "forge new",
        "forge doctor",
        "forge project:check",
        "forge routes:list",
        "forge make:entity",
        "forge make:crud",
        "forge make:relation",
        "forge sync:entity",
        "forge db:init",
        "forge db:apply",
        "forge migration:status",
        "forge migration:apply",
        "forge migration:make",
        "forge auth:init",
        "forge auth:doctor",
        "forge auth:user:create",
        "forge auth:user:list",
        "forge mail:init",
        "forge mail:test",
        "forge module:list",
        "forge module:install",
        "forge starter:list",
        "forge starter:build",
        "forge upload:init",
        "forge js:init",
        "forge deploy:init",
        "forge deploy:check",
        "forge sync:landing",
        "forge --version",
        "forge --help",
    ]

    @pytest.mark.parametrize("cmd", EXPECTED_COMMANDS)
    def test_command_present(self, cmd):
        text = REFERENCE_PATH.read_text(encoding="utf-8")
        assert cmd in text, (
            f"Commande `{cmd}` manquante dans docs/reference/cli-commands.md."
        )


class TestReferenceInNav:

    def test_nav_includes_reference(self):
        mkdocs = (PROJECT_ROOT / "mkdocs.yml").read_text(encoding="utf-8")
        assert "cli-commands" in mkdocs, (
            "docs/reference/cli-commands.md doit être dans la nav mkdocs.yml."
        )


class TestGettingStartedLinksToReference:

    def test_getting_started_links_to_cli(self):
        text = (PROJECT_ROOT / "docs" / "getting-started.md").read_text(encoding="utf-8")
        assert "cli-commands" in text, (
            "docs/getting-started.md doit lier vers reference/cli-commands.md."
        )
