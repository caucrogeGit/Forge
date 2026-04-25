from __future__ import annotations

from pathlib import Path

import forge_cli.output as out
from core.uploads.storage import ensure_upload_dirs


UPLOAD_ROOT = Path("storage") / "uploads"
UPLOAD_CATEGORIES = ("images", "documents", "tmp")


def init_upload_storage(root: Path = UPLOAD_ROOT) -> list[Path]:
    paths = ensure_upload_dirs(root, UPLOAD_CATEGORIES)
    for directory in paths:
        (directory / ".gitkeep").touch(exist_ok=True)
    return paths


def main(args: list[str]) -> None:
    if args != ["upload:init"]:
        print("Usage : forge upload:init")
        raise SystemExit(1)

    paths = init_upload_storage()
    for path in paths:
        print(out.ok(f"Dossier prêt : {path.as_posix()}"))
    print(out.ok("Stockage upload initialisé."))
