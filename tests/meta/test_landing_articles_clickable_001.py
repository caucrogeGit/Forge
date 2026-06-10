"""Garde-fou LANDING-ARTICLES-CLICKABLE-001.

Vérifie que les 40 cartes de la landing page sont wrappées dans un <a href>
pointant vers des URLs valides de la documentation.
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
    # Core Forge (16 cartes)
    "guide/concepts",
    "features/front",
    "features/migrations",
    "features/entity_architecture",
    "features/crud",
    "reference/crud",
    "philosophy/security",
    "features/auth",
    "features/media",
    "features/mail",
    "reference/cli-commands",
    "deployment/deployment",
    "reference/api-json",
    # Nouveau beta.6 — page spécifique entity-schema
    "entities/entity-schema",
    # Modules opt-in (11 cartes)
    "reference/auth-mfa",
    "features/rbac",
    "reference/workflow",
    "reference/stats",
    "starters/welcome-files/installation",
    "starters/welcome-images/installation",
    "starters/welcome-iot/installation",
    "starters/welcome-video/installation",
    "starters/welcome-audio/installation",
    "starters/welcome-mail/installation",
    "entities/pivot-advanced",
    # Section Starters (13 cartes de progression)
    "starters/welcome-forge/debutant/welcome",
    "starters/welcome-mfa/installation",
    "starters/welcome-rbac/installation",
    "starters/welcome-workflow/installation",
    "starters/welcome-stats/installation",
    "starters/welcome-helpers/installation",
    "starters/welcome-markdown/installation",
]


class TestLandingArticlesClickable:

    def test_landing_file_exists(self):
        assert LANDING.exists()

    def test_40_articles_are_wrapped_in_links(self):
        text = LANDING.read_text(encoding="utf-8")
        wrapped = re.findall(r'<a\s+href="[^"]+"\s+class="block group"[^>]*>', text)
        assert len(wrapped) == 40, (
            f"Attendu 40 cartes wrappées dans <a class=\"block group\">, "
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

    def test_all_card_links_root_relative(self):
        # Les cartes pointent vers la doc en liens racine-relatifs (/docs/forge/…),
        # valides sur le site publié ; les liens externes restent en http(s).
        text = LANDING.read_text(encoding="utf-8")
        hrefs = re.findall(r'<a\s+href="([^"]+)"\s+class="block group"', text)
        invalid = [h for h in hrefs if not (h.startswith("/docs/forge/") or h.startswith("http"))]
        assert not invalid, (
            f"Liens de carte non conformes (attendu /docs/forge/… ou http) : {invalid}"
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
