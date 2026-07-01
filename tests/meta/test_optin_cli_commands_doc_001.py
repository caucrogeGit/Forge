"""Garde-fou OPTIN-CLI-COMMANDS-DOC-001 : la doc du dispatch opt-in reste exacte.

La page contributing/optin-cli-commands.md explique comment un opt-in déclare
ses commandes CLI (entry points `forge_mvc.commands`, table `commands.py`). Ce
garde-fou la relie au code (`cli/commands/optin_dispatch.py`) pour qu'elle ne
dérive pas du groupe d'entry points réellement utilisé.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOC = PROJECT_ROOT / "docs" / "contributing" / "optin-cli-commands.md"


def _doc_text() -> str:
    return DOC.read_text(encoding="utf-8")


def test_doc_existe():
    assert DOC.is_file(), (
        "docs/contributing/optin-cli-commands.md doit exister (doc du dispatch "
        "des commandes opt-in)."
    )


def test_doc_documente_le_groupe_entry_point_reel():
    from cli.commands.optin_dispatch import _ENTRY_POINT_GROUP

    assert _ENTRY_POINT_GROUP in _doc_text(), (
        f"La doc doit mentionner le groupe d'entry points réel « {_ENTRY_POINT_GROUP} » "
        "(cf. cli/commands/optin_dispatch.py). Si le groupe change, mettre la doc à jour."
    )


@pytest.mark.parametrize("marker", [
    "commands.py",
    "COMMANDS",
    "[project.entry-points",
    "059-cli-command-dispatch-registry.md",
])
def test_doc_couvre_les_points_cles(marker: str):
    assert marker in _doc_text(), (
        f"La doc du dispatch opt-in doit couvrir « {marker} »."
    )
