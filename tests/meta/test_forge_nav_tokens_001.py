"""Garde-fou FORGE-NAV-TOKENS-001.

La navigation de la landing (docs/index.html) et celle de la documentation
(header Material, docs/stylesheets/extra.css) partagent UNE seule source de
valeurs de design : docs/static/forge-tokens.css. Ce test verrouille ce câblage
pour éviter toute dérive (couleurs/hauteurs qui divergent à nouveau entre les
deux barres).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TOKENS = PROJECT_ROOT / "docs" / "static" / "forge-tokens.css"
LANDING = PROJECT_ROOT / "docs" / "index.html"
EXTRA = PROJECT_ROOT / "docs" / "stylesheets" / "extra.css"
INPUT_CSS = PROJECT_ROOT / "docs" / "static" / "src" / "input.css"
MKDOCS = PROJECT_ROOT / "mkdocs.yml"

_REQUIRED_TOKENS = (
    "--forge-nav-bg",
    "--forge-accent",
    "--forge-accent-rgb",
    "--forge-nav-height",
    "--forge-nav-height-compact",
)


def test_tokens_file_defines_all_tokens():
    assert TOKENS.exists(), "docs/static/forge-tokens.css doit exister (source unique)."
    content = TOKENS.read_text(encoding="utf-8")
    for token in _REQUIRED_TOKENS:
        assert f"{token}:" in content, (
            f"forge-tokens.css doit définir {token}"
        )


def test_landing_loads_tokens():
    """La landing charge forge-tokens.css avant tailwind.css."""
    html = LANDING.read_text(encoding="utf-8")
    assert "static/forge-tokens.css" in html, (
        "docs/index.html doit charger forge-tokens.css"
    )
    assert html.index("forge-tokens.css") < html.index("tailwind.css"), (
        "forge-tokens.css doit être chargé avant tailwind.css"
    )


def test_docs_loads_tokens_before_extra():
    """mkdocs charge forge-tokens.css avant extra.css (pour que les var() résolvent)."""
    cfg = MKDOCS.read_text(encoding="utf-8")
    assert "static/forge-tokens.css" in cfg, (
        "mkdocs.yml (extra_css) doit inclure static/forge-tokens.css"
    )
    assert cfg.index("static/forge-tokens.css") < cfg.index("stylesheets/extra.css"), (
        "forge-tokens.css doit précéder stylesheets/extra.css dans extra_css"
    )


def test_both_sides_use_tokens_not_hardcoded():
    """La barre de la landing (input.css) et le header de doc (extra.css) utilisent
    les tokens, et n'embarquent plus la couleur/teinte d'accent en dur."""
    extra = EXTRA.read_text(encoding="utf-8")
    inp = INPUT_CSS.read_text(encoding="utf-8")

    assert "var(--forge-nav-bg)" in extra, (
        "extra.css doit utiliser var(--forge-nav-bg) pour le fond du header"
    )
    assert "var(--forge-accent)" in extra and "var(--forge-accent)" in inp, (
        "extra.css et input.css doivent utiliser var(--forge-accent)"
    )
    assert "#E8651A" not in extra, (
        "extra.css ne doit plus coder l'orange en dur (#E8651A) : utiliser var(--forge-accent)"
    )
    assert "#E8651A" not in inp, (
        "input.css ne doit plus coder l'orange en dur (#E8651A) : utiliser var(--forge-accent)"
    )
