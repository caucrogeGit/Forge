"""SEC-JINJA-AUTOESCAPE-001.

Le renderer de vues cœur (`Jinja2Renderer`) échappe désormais TOUTES les
extensions et les chaînes, pas seulement `.html`. Une valeur utilisateur
injectée dans une vue sans extension `.html` (`.txt`, `.svg`, sans extension)
ne doit plus produire de HTML brut exploitable (XSS).
"""
from __future__ import annotations

import pytest

from integrations.jinja2.renderer import Jinja2Renderer

PAYLOAD = "<script>alert(1)</script>"


@pytest.mark.parametrize("template_name", ["demo.txt", "demo.svg", "demo"])
def test_non_html_view_is_autoescaped(tmp_path, template_name):
    (tmp_path / template_name).write_text("{{ value }}", encoding="utf-8")
    renderer = Jinja2Renderer(str(tmp_path))
    out = renderer.render(template_name, {"value": PAYLOAD})
    assert "<script>" not in out
    assert "&lt;script&gt;" in out


def test_html_view_still_autoescaped(tmp_path):
    (tmp_path / "page.html").write_text("{{ value }}", encoding="utf-8")
    renderer = Jinja2Renderer(str(tmp_path))
    out = renderer.render("page.html", {"value": PAYLOAD})
    assert "&lt;script&gt;" in out


def test_safe_filter_still_emits_raw(tmp_path):
    """Le HTML voulu reste possible explicitement via `|safe`."""
    (tmp_path / "raw.html").write_text("{{ value | safe }}", encoding="utf-8")
    renderer = Jinja2Renderer(str(tmp_path))
    out = renderer.render("raw.html", {"value": "<b>ok</b>"})
    assert "<b>ok</b>" in out
