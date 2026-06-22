from __future__ import annotations

from pathlib import Path

import cli._support.output as out

# FILES-CLI-RENAME-001 (ADR-019) : l'upload est un opt-in (forge-mvc-files).
from forge_mvc_files.storage import ensure_upload_dirs


UPLOAD_ROOT = Path("storage") / "uploads"
UPLOAD_CATEGORIES = ("images", "documents", "tmp")
IMAGE_VARIANT_SUBDIRS = ("images/thumbnail", "images/medium")


def init_upload_storage(root: Path = UPLOAD_ROOT) -> list[Path]:
    paths = ensure_upload_dirs(root, UPLOAD_CATEGORIES)
    for directory in paths:
        (directory / ".gitkeep").touch(exist_ok=True)
    return paths


def init_media_storage(root: Path = UPLOAD_ROOT) -> list[Path]:
    """Initialise le stockage média : dossiers de base + sous-dossiers variantes."""
    paths = init_upload_storage(root)
    for variant in IMAGE_VARIANT_SUBDIRS:
        variant_dir = root / variant
        variant_dir.mkdir(parents=True, exist_ok=True)
        (variant_dir / ".gitkeep").touch(exist_ok=True)
        paths.append(variant_dir)
    return paths


def main(args: list[str]) -> None:
    command = args[0] if args else ""

    if command == "upload:init":
        paths = init_upload_storage()
        for path in paths:
            print(out.ok(f"Dossier prêt : {path.as_posix()}"))
        print(out.ok("Stockage upload initialisé."))
        return

    if command == "media:init":
        paths = init_media_storage()
        for path in paths:
            print(out.ok(f"Dossier prêt : {path.as_posix()}"))
        print(out.ok("Stockage média initialisé."))
        return

    print("Usage : forge upload:init | forge media:init")
    raise SystemExit(1)
