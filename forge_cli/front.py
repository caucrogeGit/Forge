from __future__ import annotations

import json
import shutil
from pathlib import Path

import forge_cli.output as out


HTMX_PACKAGE = "htmx.org"
HTMX_VERSION = "^2.0.0"
HTMX_SOURCE = Path("node_modules") / HTMX_PACKAGE / "dist" / "htmx.min.js"
HTMX_TARGET = Path("static") / "vendor" / "htmx" / "htmx.min.js"
ALPINE_PACKAGE = "alpinejs"
ALPINE_VERSION = "^3.14.0"
ALPINE_SOURCE = Path("node_modules") / ALPINE_PACKAGE / "dist" / "cdn.min.js"
ALPINE_TARGET = Path("static") / "vendor" / "alpine" / "alpine.min.js"
APP_JS = Path("static") / "js" / "app.js"
PACKAGE_JSON = Path("package.json")


def _read_package_json(path: Path) -> dict:
    if not path.exists():
        return {
            "scripts": {},
            "dependencies": {},
        }
    return json.loads(path.read_text(encoding="utf-8"))


def _write_package_json(path: Path, data: dict) -> None:
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def ensure_npm_dependency(root: Path, package_name: str, default_version: str) -> bool:
    package_path = root / PACKAGE_JSON
    package = _read_package_json(package_path)
    dependencies = package.setdefault("dependencies", {})
    if package_name in dependencies:
        return False
    dependencies[package_name] = default_version
    _write_package_json(package_path, package)
    return True


def ensure_app_js(project_root: Path) -> None:
    app_js = project_root / APP_JS
    app_js.parent.mkdir(parents=True, exist_ok=True)
    if not app_js.exists():
        app_js.write_text(
            "// Forge application JavaScript entrypoint.\n"
            "// Add project-specific JavaScript here.\n",
            encoding="utf-8",
        )
        print(out.created(APP_JS.as_posix()))
    else:
        print(out.preserved(APP_JS.as_posix()))


def init_vendor_script(
    *,
    root: Path | None,
    label: str,
    package_name: str,
    package_version: str,
    source_path: Path,
    target_path: Path,
    command: str,
) -> bool:
    project_root = (root or Path.cwd()).resolve()

    ensure_app_js(project_root)

    dependency_changed = ensure_npm_dependency(project_root, package_name, package_version)
    if dependency_changed:
        print(out.written(PACKAGE_JSON.as_posix() + f"  dépendance {package_name} ajoutée"))
    else:
        print(out.preserved(PACKAGE_JSON.as_posix() + f"  dépendance {package_name} déjà présente"))

    target = project_root / target_path
    if target.parent.exists():
        print(out.preserved(target_path.parent.as_posix()))
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        print(out.created(target_path.parent.as_posix()))

    if target.exists():
        print(out.preserved(target_path.as_posix() + "  fichier existant conservé"))
    else:
        source = project_root / source_path
        if source.exists():
            shutil.copyfile(source, target)
            print(out.created(target_path.as_posix()))
        else:
            print(out.info(f"{label} déclaré dans package.json. Lancez npm install puis relancez {command}."))
            print(out.info(f"Source attendue : {source_path.as_posix()}"))

    print(out.ok(f"Initialisation {label} terminée."))
    return target.exists()


def init_htmx(root: Path | None = None) -> bool:
    return init_vendor_script(
        root=root,
        label="HTMX",
        package_name=HTMX_PACKAGE,
        package_version=HTMX_VERSION,
        source_path=HTMX_SOURCE,
        target_path=HTMX_TARGET,
        command="forge js:init htmx",
    )


def init_alpine(root: Path | None = None) -> bool:
    return init_vendor_script(
        root=root,
        label="Alpine.js",
        package_name=ALPINE_PACKAGE,
        package_version=ALPINE_VERSION,
        source_path=ALPINE_SOURCE,
        target_path=ALPINE_TARGET,
        command="forge js:init alpine",
    )


def init_htmx_alpine(root: Path | None = None) -> dict[str, bool]:
    print(out.info("Initialisation combinée : HTMX"))
    htmx_ready = init_htmx(root)
    print(out.info("Initialisation combinée : Alpine.js"))
    alpine_ready = init_alpine(root)
    print(out.ok("Initialisation HTMX + Alpine.js terminée."))
    return {
        "htmx": htmx_ready,
        "alpine": alpine_ready,
    }


def main(args: list[str]) -> None:
    if args == ["js:init", "htmx"]:
        init_htmx()
        return

    if args == ["js:init", "alpine"]:
        init_alpine()
        return

    if args == ["js:init", "htmx-alpine"]:
        init_htmx_alpine()
        return

    print("Usage : forge js:init htmx | forge js:init alpine | forge js:init htmx-alpine")
    raise SystemExit(1)
