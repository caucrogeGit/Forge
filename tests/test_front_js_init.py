from __future__ import annotations

import json
from pathlib import Path

import pytest

from cli.assets import front


HTMX_CONTENT = "/* htmx local test asset */\n"
ALPINE_CONTENT = "/* alpine local test asset */\n"
APP_JS_CONTENT = "// Forge application JavaScript entrypoint.\n"
LAYOUT_CONTENT = "<html><head></head><body>{{ content }}</body></html>\n"


def _write_project(root: Path) -> None:
    (root / "static/js").mkdir(parents=True)
    (root / "mvc/views/layouts").mkdir(parents=True)
    (root / "static/js/app.js").write_text(APP_JS_CONTENT, encoding="utf-8")
    (root / "mvc/views/layouts/app.html").write_text(LAYOUT_CONTENT, encoding="utf-8")
    (root / "package.json").write_text(
        json.dumps(
            {
                "scripts": {
                    "build:css": "tailwindcss -i ./static/src/input.css -o ./static/tailwind.css --minify",
                },
                "dependencies": {
                    "tailwindcss": "^4.2.2",
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_htmx_node_module(root: Path) -> None:
    source = root / "node_modules/htmx.org/dist/htmx.min.js"
    source.parent.mkdir(parents=True)
    source.write_text(HTMX_CONTENT, encoding="utf-8")


def _write_alpine_node_module(root: Path) -> None:
    source = root / "node_modules/alpinejs/dist/cdn.min.js"
    source.parent.mkdir(parents=True)
    source.write_text(ALPINE_CONTENT, encoding="utf-8")


def _package(root: Path) -> dict:
    return json.loads((root / "package.json").read_text(encoding="utf-8"))


def test_js_init_htmx_adds_official_npm_dependency(tmp_path):
    _write_project(tmp_path)

    front.init_htmx(tmp_path)

    package = _package(tmp_path)
    assert package["dependencies"]["htmx.org"] == front.HTMX_VERSION
    assert "htmx" not in package["dependencies"]


def test_js_init_htmx_preserves_existing_htmx_org_version(tmp_path):
    _write_project(tmp_path)
    package = _package(tmp_path)
    package["dependencies"]["htmx.org"] = "^2.1.0"
    (tmp_path / "package.json").write_text(
        json.dumps(package, indent=2) + "\n",
        encoding="utf-8",
    )

    front.init_htmx(tmp_path)

    assert _package(tmp_path)["dependencies"]["htmx.org"] == "^2.1.0"


def test_js_init_htmx_copies_local_vendor_file_from_node_modules(tmp_path):
    _write_project(tmp_path)
    _write_htmx_node_module(tmp_path)

    front.init_htmx(tmp_path)

    target = tmp_path / "static/vendor/htmx/htmx.min.js"
    assert target.read_text(encoding="utf-8") == HTMX_CONTENT


def test_js_init_htmx_does_not_overwrite_existing_vendor_file(tmp_path):
    _write_project(tmp_path)
    _write_htmx_node_module(tmp_path)
    target = tmp_path / "static/vendor/htmx/htmx.min.js"
    target.parent.mkdir(parents=True)
    target.write_text("/* existing */\n", encoding="utf-8")

    front.init_htmx(tmp_path)

    assert target.read_text(encoding="utf-8") == "/* existing */\n"


def test_js_init_htmx_is_idempotent(tmp_path):
    _write_project(tmp_path)
    _write_htmx_node_module(tmp_path)

    front.init_htmx(tmp_path)
    first_package = (tmp_path / "package.json").read_text(encoding="utf-8")
    first_vendor = (tmp_path / "static/vendor/htmx/htmx.min.js").read_text(encoding="utf-8")
    front.init_htmx(tmp_path)

    assert (tmp_path / "package.json").read_text(encoding="utf-8") == first_package
    assert (tmp_path / "static/vendor/htmx/htmx.min.js").read_text(encoding="utf-8") == first_vendor


def test_js_init_htmx_preserves_application_javascript(tmp_path):
    _write_project(tmp_path)

    front.init_htmx(tmp_path)

    assert (tmp_path / "static/js/app.js").read_text(encoding="utf-8") == APP_JS_CONTENT


def test_js_init_htmx_creates_application_javascript_if_missing(tmp_path):
    _write_project(tmp_path)
    (tmp_path / "static/js/app.js").unlink()

    front.init_htmx(tmp_path)

    assert (tmp_path / "static/js/app.js").is_file()


def test_js_init_htmx_does_not_modify_layouts(tmp_path):
    _write_project(tmp_path)
    _write_htmx_node_module(tmp_path)

    front.init_htmx(tmp_path)

    assert (tmp_path / "mvc/views/layouts/app.html").read_text(encoding="utf-8") == LAYOUT_CONTENT


def test_js_init_htmx_does_not_add_alpine(tmp_path):
    _write_project(tmp_path)
    _write_htmx_node_module(tmp_path)

    front.init_htmx(tmp_path)

    package = _package(tmp_path)
    assert "alpinejs" not in package["dependencies"]
    assert "alpine" not in (tmp_path / "static/vendor/htmx/htmx.min.js").read_text(encoding="utf-8").lower()


def test_js_init_htmx_without_node_modules_prepares_dependency_only(tmp_path, capsys):
    _write_project(tmp_path)

    created_vendor = front.init_htmx(tmp_path)

    captured = capsys.readouterr()
    assert created_vendor is False
    assert "npm install" in captured.out
    assert not (tmp_path / "static/vendor/htmx/htmx.min.js").exists()


def test_front_main_accepts_js_init_htmx(tmp_path, monkeypatch):
    _write_project(tmp_path)
    _write_htmx_node_module(tmp_path)
    monkeypatch.chdir(tmp_path)

    front.main(["js:init", "htmx"])

    assert (tmp_path / "static/vendor/htmx/htmx.min.js").is_file()


def test_js_init_alpine_adds_official_npm_dependency(tmp_path):
    _write_project(tmp_path)

    front.init_alpine(tmp_path)

    package = _package(tmp_path)
    assert package["dependencies"]["alpinejs"] == front.ALPINE_VERSION


def test_js_init_alpine_preserves_existing_alpinejs_version(tmp_path):
    _write_project(tmp_path)
    package = _package(tmp_path)
    package["dependencies"]["alpinejs"] = "^3.15.0"
    (tmp_path / "package.json").write_text(
        json.dumps(package, indent=2) + "\n",
        encoding="utf-8",
    )

    front.init_alpine(tmp_path)

    assert _package(tmp_path)["dependencies"]["alpinejs"] == "^3.15.0"


def test_js_init_alpine_creates_vendor_directory_without_node_modules(tmp_path):
    _write_project(tmp_path)

    created_vendor = front.init_alpine(tmp_path)

    assert created_vendor is False
    assert (tmp_path / "static/vendor/alpine").is_dir()
    assert not (tmp_path / "static/vendor/alpine/alpine.min.js").exists()


def test_js_init_alpine_prints_vendor_directory_status(tmp_path, capsys):
    _write_project(tmp_path)

    front.init_alpine(tmp_path)

    captured = capsys.readouterr()
    assert "static/vendor/alpine" in captured.out


def test_js_init_alpine_copies_local_vendor_file_from_node_modules(tmp_path):
    _write_project(tmp_path)
    _write_alpine_node_module(tmp_path)

    front.init_alpine(tmp_path)

    target = tmp_path / "static/vendor/alpine/alpine.min.js"
    assert target.read_text(encoding="utf-8") == ALPINE_CONTENT


def test_js_init_alpine_does_not_overwrite_existing_vendor_file(tmp_path):
    _write_project(tmp_path)
    _write_alpine_node_module(tmp_path)
    target = tmp_path / "static/vendor/alpine/alpine.min.js"
    target.parent.mkdir(parents=True)
    target.write_text("/* existing alpine */\n", encoding="utf-8")

    front.init_alpine(tmp_path)

    assert target.read_text(encoding="utf-8") == "/* existing alpine */\n"


def test_js_init_alpine_is_idempotent(tmp_path):
    _write_project(tmp_path)
    _write_alpine_node_module(tmp_path)

    front.init_alpine(tmp_path)
    first_package = (tmp_path / "package.json").read_text(encoding="utf-8")
    first_vendor = (tmp_path / "static/vendor/alpine/alpine.min.js").read_text(encoding="utf-8")
    front.init_alpine(tmp_path)

    assert (tmp_path / "package.json").read_text(encoding="utf-8") == first_package
    assert (tmp_path / "static/vendor/alpine/alpine.min.js").read_text(encoding="utf-8") == first_vendor


def test_js_init_alpine_preserves_application_javascript(tmp_path):
    _write_project(tmp_path)

    front.init_alpine(tmp_path)

    assert (tmp_path / "static/js/app.js").read_text(encoding="utf-8") == APP_JS_CONTENT


def test_js_init_alpine_preserves_existing_htmx_files(tmp_path):
    _write_project(tmp_path)
    htmx_target = tmp_path / "static/vendor/htmx/htmx.min.js"
    htmx_target.parent.mkdir(parents=True)
    htmx_target.write_text(HTMX_CONTENT, encoding="utf-8")

    front.init_alpine(tmp_path)

    assert htmx_target.read_text(encoding="utf-8") == HTMX_CONTENT


def test_js_init_alpine_does_not_modify_layouts(tmp_path):
    _write_project(tmp_path)
    _write_alpine_node_module(tmp_path)

    front.init_alpine(tmp_path)

    assert (tmp_path / "mvc/views/layouts/app.html").read_text(encoding="utf-8") == LAYOUT_CONTENT


def test_js_init_alpine_without_node_modules_prints_workflow(tmp_path, capsys):
    _write_project(tmp_path)

    created_vendor = front.init_alpine(tmp_path)

    captured = capsys.readouterr()
    assert created_vendor is False
    assert "npm install" in captured.out
    assert "node_modules/alpinejs/dist/cdn.min.js" in captured.out


def test_front_main_accepts_js_init_alpine(tmp_path, monkeypatch):
    _write_project(tmp_path)
    _write_alpine_node_module(tmp_path)
    monkeypatch.chdir(tmp_path)

    front.main(["js:init", "alpine"])

    assert (tmp_path / "static/vendor/alpine/alpine.min.js").is_file()


def test_js_init_htmx_alpine_adds_both_official_dependencies(tmp_path):
    _write_project(tmp_path)

    front.init_htmx_alpine(tmp_path)

    package = _package(tmp_path)
    assert package["dependencies"]["htmx.org"] == front.HTMX_VERSION
    assert package["dependencies"]["alpinejs"] == front.ALPINE_VERSION
    assert "htmx" not in package["dependencies"]


def test_js_init_htmx_alpine_preserves_existing_versions(tmp_path):
    _write_project(tmp_path)
    package = _package(tmp_path)
    package["dependencies"]["htmx.org"] = "^2.1.0"
    package["dependencies"]["alpinejs"] = "^3.15.0"
    (tmp_path / "package.json").write_text(
        json.dumps(package, indent=2) + "\n",
        encoding="utf-8",
    )

    front.init_htmx_alpine(tmp_path)

    dependencies = _package(tmp_path)["dependencies"]
    assert dependencies["htmx.org"] == "^2.1.0"
    assert dependencies["alpinejs"] == "^3.15.0"


def test_js_init_htmx_alpine_creates_vendor_directories_without_node_modules(tmp_path):
    _write_project(tmp_path)

    result = front.init_htmx_alpine(tmp_path)

    assert result == {"htmx": False, "alpine": False}
    assert (tmp_path / "static/vendor/htmx").is_dir()
    assert (tmp_path / "static/vendor/alpine").is_dir()


def test_js_init_htmx_alpine_copies_both_vendor_files_from_node_modules(tmp_path):
    _write_project(tmp_path)
    _write_htmx_node_module(tmp_path)
    _write_alpine_node_module(tmp_path)

    result = front.init_htmx_alpine(tmp_path)

    assert result == {"htmx": True, "alpine": True}
    assert (tmp_path / "static/vendor/htmx/htmx.min.js").read_text(encoding="utf-8") == HTMX_CONTENT
    assert (tmp_path / "static/vendor/alpine/alpine.min.js").read_text(encoding="utf-8") == ALPINE_CONTENT


def test_js_init_htmx_alpine_does_not_overwrite_existing_vendor_files(tmp_path):
    _write_project(tmp_path)
    _write_htmx_node_module(tmp_path)
    _write_alpine_node_module(tmp_path)
    htmx_target = tmp_path / "static/vendor/htmx/htmx.min.js"
    alpine_target = tmp_path / "static/vendor/alpine/alpine.min.js"
    htmx_target.parent.mkdir(parents=True)
    alpine_target.parent.mkdir(parents=True)
    htmx_target.write_text("/* existing htmx */\n", encoding="utf-8")
    alpine_target.write_text("/* existing alpine */\n", encoding="utf-8")

    front.init_htmx_alpine(tmp_path)

    assert htmx_target.read_text(encoding="utf-8") == "/* existing htmx */\n"
    assert alpine_target.read_text(encoding="utf-8") == "/* existing alpine */\n"


def test_js_init_htmx_alpine_preserves_application_javascript(tmp_path):
    _write_project(tmp_path)

    front.init_htmx_alpine(tmp_path)

    assert (tmp_path / "static/js/app.js").read_text(encoding="utf-8") == APP_JS_CONTENT


def test_js_init_htmx_alpine_is_idempotent(tmp_path):
    _write_project(tmp_path)
    _write_htmx_node_module(tmp_path)
    _write_alpine_node_module(tmp_path)

    front.init_htmx_alpine(tmp_path)
    first_package = (tmp_path / "package.json").read_text(encoding="utf-8")
    first_htmx = (tmp_path / "static/vendor/htmx/htmx.min.js").read_text(encoding="utf-8")
    first_alpine = (tmp_path / "static/vendor/alpine/alpine.min.js").read_text(encoding="utf-8")
    front.init_htmx_alpine(tmp_path)

    assert (tmp_path / "package.json").read_text(encoding="utf-8") == first_package
    assert (tmp_path / "static/vendor/htmx/htmx.min.js").read_text(encoding="utf-8") == first_htmx
    assert (tmp_path / "static/vendor/alpine/alpine.min.js").read_text(encoding="utf-8") == first_alpine


def test_js_init_htmx_alpine_does_not_modify_layouts(tmp_path):
    _write_project(tmp_path)
    _write_htmx_node_module(tmp_path)
    _write_alpine_node_module(tmp_path)

    front.init_htmx_alpine(tmp_path)

    assert (tmp_path / "mvc/views/layouts/app.html").read_text(encoding="utf-8") == LAYOUT_CONTENT


def test_js_init_htmx_alpine_prints_clear_sections(tmp_path, capsys):
    _write_project(tmp_path)

    front.init_htmx_alpine(tmp_path)

    captured = capsys.readouterr()
    assert "HTMX" in captured.out
    assert "Alpine.js" in captured.out
    assert "npm install" in captured.out


def test_front_main_accepts_js_init_htmx_alpine(tmp_path, monkeypatch):
    _write_project(tmp_path)
    _write_htmx_node_module(tmp_path)
    _write_alpine_node_module(tmp_path)
    monkeypatch.chdir(tmp_path)

    front.main(["js:init", "htmx-alpine"])

    assert (tmp_path / "static/vendor/htmx/htmx.min.js").is_file()
    assert (tmp_path / "static/vendor/alpine/alpine.min.js").is_file()


def test_front_main_rejects_unknown_command():
    with pytest.raises(SystemExit):
        front.main(["js:init", "vue"])
