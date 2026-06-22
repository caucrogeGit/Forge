"""Commande forge sync:landing — synchronise la landing vers docs/index.html."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import cli.output as out


SOURCE = Path("mvc") / "views" / "landing" / "index.html"
TARGET = Path("docs") / "index.html"
STATIC_SOURCE = Path("static")
STATIC_TARGET = Path("docs") / "static"
GENERATED_COMMENT = (
    "<!--\n"
    "  FICHIER GENERE PAR forge sync:landing.\n"
    "  Source canonique : mvc/views/landing/index.html\n"
    "  Ne pas modifier docs/index.html manuellement.\n"
    "-->\n"
)


class LandingSyncError(ValueError):
    """Erreur de synchronisation de la landing."""


def expected_docs_content(source_path: Path = SOURCE) -> str:
    if not source_path.exists():
        raise LandingSyncError(f"Source introuvable : {source_path.as_posix()}")
    return GENERATED_COMMENT + source_path.read_text(encoding="utf-8")


def sync_landing(
    *,
    source_path: Path = SOURCE,
    target_path: Path = TARGET,
) -> Path:
    content = expected_docs_content(source_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(content, encoding="utf-8")
    return target_path


def sync_static(
    *,
    source_dir: Path = STATIC_SOURCE,
    target_dir: Path = STATIC_TARGET,
) -> list[Path]:
    """Copie récursivement static/ vers docs/static/. Retourne les fichiers copiés."""
    if not source_dir.exists():
        return []
    copied = []
    for src_file in sorted(source_dir.rglob("*")):
        if src_file.is_file():
            rel = src_file.relative_to(source_dir)
            dst_file = target_dir / rel
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dst_file)
            copied.append(dst_file)
    return copied


def landing_is_synced(
    *,
    source_path: Path = SOURCE,
    target_path: Path = TARGET,
    source_dir: Path = STATIC_SOURCE,
    target_dir: Path = STATIC_TARGET,
) -> bool:
    if not target_path.exists():
        return False
    if target_path.read_text(encoding="utf-8") != expected_docs_content(source_path):
        return False
    if source_dir.exists():
        for src_file in source_dir.rglob("*"):
            if src_file.is_file():
                dst_file = target_dir / src_file.relative_to(source_dir)
                if not dst_file.exists():
                    return False
                if src_file.read_bytes() != dst_file.read_bytes():
                    return False
    return True


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] != "sync:landing":
        print("Usage : forge sync:landing [--check]")
        raise SystemExit(1)

    extra = args[1:]
    check = False
    if extra == ["--check"]:
        check = True
    elif extra:
        print(out.error(f"Arguments inconnus : {' '.join(extra)}"))
        raise SystemExit(1)

    try:
        if check:
            if landing_is_synced():
                print(out.ok("docs/index.html et docs/static/ sont synchronisés"))
                return
            print(out.error("Landing désynchronisée — lancez forge sync:landing"))
            raise SystemExit(1)

        target = sync_landing()
        print(out.written(target.as_posix()))
        for asset in sync_static():
            print(out.written(asset.as_posix()))
        print(out.ok("Landing synchronisée (HTML + assets statiques)"))
    except LandingSyncError as exc:
        print(out.error(str(exc)))
        raise SystemExit(1)
