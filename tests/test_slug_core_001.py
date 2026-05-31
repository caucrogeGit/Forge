"""SLUG-CORE-001 (ADR-017) — module URL-slug canonique core/slug.py.

`slugify` transforme un texte quelconque en slug kebab-case (translittération
des accents via stdlib) ; `is_valid_slug` valide un slug existant (path-safe).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from core.slug import DEFAULT_MAX_LENGTH, is_valid_slug, slugify

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ── slugify : transformation ─────────────────────────────────────────────────

class TestSlugify:
    @pytest.mark.parametrize("text, expected", [
        ("accueil", "accueil"),
        ("ma-page", "ma-page"),
        ("ma_page", "ma-page"),
        ("MaPage", "ma-page"),
        ("HTTPServer", "http-server"),
        ("Premier contact avec Forge", "premier-contact-avec-forge"),
        ("Écrire avec Forge !", "ecrire-avec-forge"),
        ("Été à Châteauroux", "ete-a-chateauroux"),
        ("  espaces   multiples  ", "espaces-multiples"),
        ("ponctuation!?@#$%", "ponctuation"),
        ("déjà-slug-2", "deja-slug-2"),
        ("carte ESP32", "carte-esp32"),
    ])
    def test_transforms(self, text, expected):
        assert slugify(text) == expected

    def test_is_path_safe(self):
        # Une entrée de type chemin ne produit jamais de chemin.
        result = slugify("../admin/secret")
        assert "/" not in result and ".." not in result
        assert is_valid_slug(result)

    def test_compacts_and_strips_dashes(self):
        assert slugify("--a---b--") == "a-b"

    def test_bounds_length_without_trailing_dash(self):
        out = slugify("mot " * 100, max_length=20)
        assert len(out) <= 20
        assert not out.endswith("-")
        assert is_valid_slug(out, max_length=20)

    @pytest.mark.parametrize("empty", ["", "   ", "-", "!!!", "..."])
    def test_empty_result_raises(self, empty):
        with pytest.raises(ValueError):
            slugify(empty)

    def test_result_always_valid(self):
        for text in ["MaPage", "Écrire !", "carte ESP32", "a.b.c", "Hello_World"]:
            assert is_valid_slug(slugify(text))


# ── is_valid_slug : validation ───────────────────────────────────────────────

class TestIsValidSlug:
    @pytest.mark.parametrize("slug", [
        "accueil", "ma-page", "premier-contact", "carte-esp32", "a", "a-b-c", "2024-bilan",
    ])
    def test_valid(self, slug):
        assert is_valid_slug(slug)

    @pytest.mark.parametrize("bad", [
        "", "MaPage", "ma_page", "ma page", "écrire", "-leading", "trailing-",
        "double--dash", "../admin", "a/b", "a\\b", "a..b", "UPPER",
    ])
    def test_invalid(self, bad):
        assert not is_valid_slug(bad)

    def test_rejects_over_max_length(self):
        assert not is_valid_slug("a" * (DEFAULT_MAX_LENGTH + 1))
        assert is_valid_slug("a" * DEFAULT_MAX_LENGTH)


# ── §11 : public_page délègue au module canonique ───────────────────────────

class TestSingleSource:
    def test_public_page_uses_core_slug(self):
        src = (PROJECT_ROOT / "forge_cli" / "public_page.py").read_text(encoding="utf-8")
        assert "from core.slug import slugify" in src

    def test_migration_slug_stays_separate(self):
        # slugify_migration_name (snake_case, filenames) reste distinct (ADR-017 D1).
        src = (PROJECT_ROOT / "forge_cli" / "entities" / "migrations.py").read_text(encoding="utf-8")
        assert "def slugify_migration_name" in src
