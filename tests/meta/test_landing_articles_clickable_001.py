"""Garde-fou LANDING-ARTICLES-CLICKABLE-001.

Vérifie que les 21 cartes de la landing page sont wrappées dans un <a href>
pointant vers des URLs absolues valides de la documentation.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
LANDING = PROJECT_ROOT / "mvc" / "views" / "landing" / "index.html"
DOCS = PROJECT_ROOT / "docs"

BASE_URL = "https://caucrogegit.github.io/Forge/"

EXPECTED_DOC_PATHS = [
    # Core Forge (17 cartes)
    "concepts",
    "front",
    "migrations",
    "entity_architecture",
    "crud",
    "reference/crud",
    "security",
    "auth",
    "media",
    "mail",
    "reference/cli-commands",
    "deployment",
    "api-json",
    # Nouveau beta.6
    "entities/json-canonique",
    # Modules opt-in (4 cartes)
    "reference/auth-mfa",
    "rbac",
    "reference/workflow",
    "reference/stats",
]


class TestLandingArticlesClickable:

    def test_landing_file_exists(self):
        assert LANDING.exists()

    def test_21_articles_are_wrapped_in_links(self):
        text = LANDING.read_text(encoding="utf-8")
        wrapped = re.findall(r'<a\s+href="[^"]+"\s+class="block group"[^>]*>', text)
        assert len(wrapped) == 21, (
            f"Attendu 21 cartes wrappées dans <a class=\"block group\">, "
            f"trouvé {len(wrapped)}."
        )

    def test_all_wrapped_articles_have_group_hover_on_h3(self):
        text = LANDING.read_text(encoding="utf-8")
        blocks = re.findall(
            r'<a\s+href="[^"]+"\s+class="block group"[^>]*>.*?</a>',
            text,
            re.DOTALL,
        )
        missing = [b for b in blocks if 'group-hover:landing-accent-text' not in b]
        assert not missing, (
            f"{len(missing)} carte(s) sans group-hover:landing-accent-text sur le <h3>."
        )

    def test_all_links_are_absolute(self):
        text = LANDING.read_text(encoding="utf-8")
        hrefs = re.findall(r'<a\s+href="([^"]+)"\s+class="block group"', text)
        relative = [h for h in hrefs if not h.startswith("http")]
        assert not relative, (
            f"Liens relatifs trouvés (causent des 404) : {relative}"
        )

    @pytest.mark.parametrize("doc_path", sorted(set(EXPECTED_DOC_PATHS)))
    def test_doc_source_exists(self, doc_path):
        md_path = DOCS / f"{doc_path}.md"
        assert md_path.exists(), (
            f"Page doc manquante pour '{doc_path}' : {md_path.relative_to(PROJECT_ROOT)}"
        )

    def test_articles_have_cursor_pointer(self):
        text = LANDING.read_text(encoding="utf-8")
        article_blocks = re.findall(
            r'<a\s+href="[^"]+"\s+class="block group"[^>]*>\s*<article[^>]+>',
            text,
        )
        missing = [b for b in article_blocks if "cursor-pointer" not in b]
        assert not missing, (
            f"{len(missing)} carte(s) sans cursor-pointer."
        )
