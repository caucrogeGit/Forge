"""Garde-fou LANDING-ARTICLES-CLICKABLE-001.

Vérifie que les 21 articles de la landing page sont wrappés dans un <a href>
pointant vers une page de documentation existante.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
LANDING = PROJECT_ROOT / "mvc" / "views" / "landing" / "index.html"
DOCS = PROJECT_ROOT / "docs"

EXPECTED_HREFS = [
    # Core Forge (17)
    "concepts.html",
    "front.html",
    "migrations.html",
    "entity_architecture.html",
    "crud.html",
    "reference/crud.html",
    "security.html",
    "auth.html",
    "media.html",
    "mail.html",
    "deployment.html",
    "api-json.html",
    "reference/api.html",
    "reference/cli-commands.html",
    # Modules opt-in (4)
    "reference/auth-mfa.html",
    "rbac.html",
    "reference/workflow.html",
    "reference/stats.html",
]


class TestLandingArticlesClickable:

    def test_landing_file_exists(self):
        assert LANDING.exists()

    def test_21_articles_are_wrapped_in_links(self):
        text = LANDING.read_text(encoding="utf-8")
        # Each wrapped article has <a href="..." class="block group">
        wrapped = re.findall(r'<a\s+href="[^"]+"\s+class="block group">', text)
        assert len(wrapped) == 21, (
            f"Attendu 21 articles wrappés dans <a class=\"block group\">, "
            f"trouvé {len(wrapped)}."
        )

    def test_all_wrapped_articles_have_group_hover_on_h3(self):
        text = LANDING.read_text(encoding="utf-8")
        # Extract each <a class="block group">...</a> block
        blocks = re.findall(
            r'<a\s+href="[^"]+"\s+class="block group">.*?</a>',
            text,
            re.DOTALL,
        )
        missing = [
            b for b in blocks
            if 'group-hover:landing-accent-text' not in b
        ]
        assert not missing, (
            f"{len(missing)} article(s) wrappé(s) sans group-hover:landing-accent-text sur le <h3>."
        )

    @pytest.mark.parametrize("href", sorted(set(EXPECTED_HREFS)))
    def test_href_target_doc_exists(self, href):
        # .html → .md (docs source)
        md_path = DOCS / href.replace(".html", ".md")
        assert md_path.exists(), (
            f"Page doc manquante pour href='{href}' : {md_path.relative_to(PROJECT_ROOT)}"
        )

    def test_articles_have_cursor_pointer(self):
        text = LANDING.read_text(encoding="utf-8")
        # All wrapped articles should have cursor-pointer
        article_blocks = re.findall(
            r'<a\s+href="[^"]+"\s+class="block group">\s*<article[^>]+>',
            text,
        )
        missing = [b for b in article_blocks if "cursor-pointer" not in b]
        assert not missing, (
            f"{len(missing)} article(s) wrappés sans cursor-pointer."
        )
