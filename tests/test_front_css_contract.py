"""Contrat CSS standard de Forge."""

from __future__ import annotations

import json
from pathlib import Path


def test_tailwind_build_script_is_declared():
    package = json.loads(Path("package.json").read_text(encoding="utf-8"))

    assert package["scripts"]["build:css"] == (
        "npx @tailwindcss/cli -i ./static/src/input.css -o ./static/tailwind.css --minify"
    )
    assert "tailwindcss" in package["dependencies"]
    assert "@tailwindcss/cli" in package["dependencies"]


def test_tailwind_source_and_compiled_files_exist():
    assert Path("static/src/input.css").is_file()
    assert Path("static/tailwind.css").is_file()


def test_application_javascript_entrypoint_exists_without_front_frameworks():
    app_js = Path("static/js/app.js")

    assert app_js.is_file()

    content = app_js.read_text(encoding="utf-8").lower()
    assert "htmx" not in content
    assert "alpine" not in content


def test_htmx_vendor_file_is_not_committed_by_default():
    assert not Path("static/vendor/htmx/htmx.min.js").exists()


def test_alpine_vendor_file_is_not_committed_by_default():
    assert not Path("static/vendor/alpine/alpine.min.js").exists()


def test_front_documentation_mentions_application_javascript_directory():
    front_doc = Path("docs/features/front.md").read_text(encoding="utf-8")

    assert "static/js/" in front_doc
    assert "static/js/app.js" in front_doc


def test_generated_views_reference_tailwind_css():
    make_crud = Path("forge_cli/entities/make_crud.py").read_text(encoding="utf-8")

    assert "/static/tailwind.css" in make_crud
