"""Garde-fou DOCS-AUDITS-HISTORY-MIGRATION-001.

Vérifie que docs/audits/ ne contient plus de fichiers actifs (uniquement
des fichiers historiques archivés dans docs/history/audits/).

Sans ce garde-fou, docs/audits/ a tendance à être utilisé comme zone tampon
où s'accumulent les audits ponctuels qui finissent par polluer mkdocs build.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent

AUDITS_DIR         = PROJECT_ROOT / "docs" / "audits"
HISTORY_AUDITS_DIR = PROJECT_ROOT / "docs" / "history" / "audits"


class TestDocsAuditsMigrated:
    """docs/audits/ est vide ou n'existe plus."""

    def test_audits_dir_is_empty_or_absent(self):
        """docs/audits/ ne contient plus de fichiers .md."""
        if not AUDITS_DIR.exists():
            return
        md_files = list(AUDITS_DIR.glob("*.md"))
        non_readme = [f for f in md_files if f.name != "README.md"]
        assert not non_readme, (
            f"docs/audits/ contient {len(non_readme)} fichier(s) .md actif(s) : "
            f"{[f.name for f in non_readme]}. "
            f"Les audits ponctuels doivent être archivés dans docs/history/audits/."
        )


class TestHistoryAuditsDirExists:
    """docs/history/audits/ existe et contient les audits archivés."""

    def test_history_audits_dir_exists(self):
        assert HISTORY_AUDITS_DIR.exists(), (
            f"{HISTORY_AUDITS_DIR} doit exister pour archiver les audits."
        )

    def test_history_audits_has_readme(self):
        """docs/history/audits/README.md sert de page d'index."""
        readme = HISTORY_AUDITS_DIR / "README.md"
        assert readme.exists(), (
            f"{readme} doit exister pour expliquer le contenu archivé."
        )

    def test_history_audits_has_archived_files(self):
        """Au moins quelques fichiers archivés (preuve de migration)."""
        md_files = [f for f in HISTORY_AUDITS_DIR.glob("*.md") if f.name != "README.md"]
        assert len(md_files) >= 5, (
            f"docs/history/audits/ ne contient que {len(md_files)} fichier(s) "
            f"archivé(s). Vérifier que la migration depuis docs/audits/ a bien eu lieu."
        )


class TestNoBrokenInternalLinksToAudits:
    """Aucun lien interne actif ne pointe vers l'ancien chemin docs/audits/*.md."""

    def test_no_active_links_to_old_audits_path(self):
        """Aucun fichier .md actif ne lie vers 'audits/...md' sans 'history/'."""
        offenders: list[tuple[str, int, str]] = []
        for md in (PROJECT_ROOT / "docs").rglob("*.md"):
            if "history" in md.parts:
                continue
            text = md.read_text(encoding="utf-8")
            pat = re.compile(r"\]\(((?:\.\./)*)audits/([^)]+\.md)\)")
            for line_no, line in enumerate(text.splitlines(), start=1):
                for match in pat.finditer(line):
                    offenders.append((str(md.relative_to(PROJECT_ROOT)), line_no, line.strip()))

        assert not offenders, (
            "Liens internes vers l'ancien dossier audits/ trouvés :\n"
            + "\n".join(f"  {p}:{n} — {line!r}" for p, n, line in offenders)
            + "\nMettre à jour vers history/audits/."
        )
