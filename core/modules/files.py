# pyright: strict
"""Copie contrôlée des fichiers déclarés par un module Forge."""

from __future__ import annotations

import fnmatch
import re
import shutil
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from .manifest import ModuleManifest, ModuleManifestError, load_module_manifest
from .registry import (
    MODULE_REGISTRY_FILE,
    load_installed_modules_registry,
    save_installed_modules_registry,
)


__all__ = [
    "INSTALLABLE_PROVIDES",
    "ModuleFileConflictError",
    "ModuleFileInstallError",
    "ModuleFileInstallResult",
    "install_module_files",
    "prepare_module_file_installation",
    "_planned_file_pairs",
]

INSTALLABLE_PROVIDES: frozenset[str] = frozenset({
    "entities",
    "controllers",
    "views",
    "docs",
})
TARGET_ROOTS: dict[str, Path] = {
    "entities": Path("mvc/entities"),
    "controllers": Path("mvc/controllers"),
    "views": Path("mvc/views"),
}
IGNORED_DIRS: frozenset[str] = frozenset({"__pycache__", ".git", ".venv"})
IGNORED_FILES: frozenset[str] = frozenset({".env", ".DS_Store", "Thumbs.db"})
IGNORED_PATTERNS: tuple[str, ...] = ("*.pyc", "*.tmp", "*.bak")
_URL_RE = re.compile(r"https?://|ftp://|file://", re.IGNORECASE)


class ModuleFileInstallError(ValueError):
    """Erreur de préparation ou copie des fichiers d'un module Forge."""


class ModuleFileConflictError(ModuleFileInstallError):
    """Au moins une cible existe déjà."""

    def __init__(self, conflicts: tuple[str, ...]) -> None:
        self.conflicts = conflicts
        super().__init__("Conflit de fichiers : " + ", ".join(conflicts))


@dataclass(frozen=True)
class ModuleFileInstallResult:
    module_name: str
    dry_run: bool
    installed: bool
    planned_files: tuple[tuple[str, str], ...]
    copied_files: tuple[str, ...]
    message: str
    manifest: ModuleManifest


def _safe_relative_path(value: Any, *, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ModuleFileInstallError(f"{label}: chemin manquant")
    if _URL_RE.search(value):
        raise ModuleFileInstallError(f"{label}: ne doit pas contenir d'URL")
    normalized = value.replace("\\", "/")
    if any(part == ".." for part in normalized.split("/")):
        raise ModuleFileInstallError(f"{label}: ne doit pas contenir '..'")
    path = Path(value)
    if path.is_absolute():
        raise ModuleFileInstallError(f"{label}: ne doit pas être un chemin absolu")
    return Path(normalized)


def _safe_registry_source(source: str) -> Path:
    return _safe_relative_path(source, label="source")


def _target_root(module_name: str, provide: str) -> Path:
    if provide == "docs":
        return Path("docs/modules") / module_name
    return TARGET_ROOTS[provide]


def _is_ignored(path: Path) -> bool:
    parts = path.parts
    if any(part in IGNORED_DIRS for part in parts):
        return True
    if any(part.startswith(".") for part in parts):
        return True
    if path.name in IGNORED_FILES:
        return True
    return any(fnmatch.fnmatch(path.name, pattern) for pattern in IGNORED_PATTERNS)


def _iter_module_files(source_root: Path) -> list[Path]:
    if not source_root.exists():
        raise ModuleFileInstallError(f"Chemin déclaré introuvable : {source_root.as_posix()}")
    if source_root.is_symlink():
        raise ModuleFileInstallError(f"Lien symbolique refusé : {source_root.as_posix()}")
    if source_root.is_file():
        return [source_root]
    result: list[Path] = []
    for path in sorted(source_root.rglob("*")):
        if path.is_symlink():
            raise ModuleFileInstallError(
                f"Lien symbolique refusé dans le module : {path.relative_to(source_root).as_posix()}"
            )
        if not path.is_file():
            continue
        relative = path.relative_to(source_root)
        if _is_ignored(relative):
            continue
        result.append(path)
    return result


def _load_installed_manifest(module_name: str, registry_path: str | Path) -> tuple[ModuleManifest, Path]:
    registry = load_installed_modules_registry(registry_path)
    installed = registry.get("installed", {})
    if module_name not in installed:
        raise ModuleFileInstallError(
            f"Module non installé : {module_name}\nLance d'abord : forge module:install {module_name}"
        )
    source_dir = _safe_registry_source(installed[module_name].get("source", ""))
    try:
        manifest = load_module_manifest(source_dir / "module.json")
    except ModuleManifestError as exc:
        raise ModuleFileInstallError(str(exc)) from exc
    if manifest.name != module_name:
        raise ModuleFileInstallError(
            f"module.json incohérent : attendu {module_name}, obtenu {manifest.name}"
        )
    return manifest, source_dir


def _planned_file_pairs(manifest: ModuleManifest, source_dir: Path) -> tuple[tuple[str, str], ...]:
    planned: list[tuple[str, str]] = []
    for provide in manifest.provides:
        if provide not in INSTALLABLE_PROVIDES:
            continue
        raw_path = manifest.paths.get(provide)
        if not raw_path:
            raise ModuleFileInstallError(
                f"paths.{provide}: obligatoire quand provides contient {provide!r}"
            )
        source_rel = _safe_relative_path(raw_path, label=f"paths.{provide}")
        source_root = source_dir / source_rel
        target_root = _target_root(manifest.name, provide)
        for source_file in _iter_module_files(source_root):
            relative = Path(source_file.name) if source_root.is_file() else source_file.relative_to(source_root)
            if _is_ignored(relative):
                continue
            target = target_root / relative
            planned.append((source_file.as_posix(), target.as_posix()))
    if not planned:
        raise ModuleFileInstallError(
            f"Le module {manifest.name} ne déclare aucun fichier installable."
        )
    return tuple(planned)


def prepare_module_file_installation(
    module_name: str,
    *,
    registry_path: str | Path = MODULE_REGISTRY_FILE,
) -> ModuleFileInstallResult:
    manifest, source_dir = _load_installed_manifest(module_name, registry_path)
    planned = _planned_file_pairs(manifest, source_dir)
    conflicts = tuple(target for _, target in planned if Path(target).exists())
    if conflicts:
        raise ModuleFileConflictError(conflicts)
    return ModuleFileInstallResult(
        module_name=manifest.name,
        dry_run=False,
        installed=False,
        planned_files=planned,
        copied_files=(),
        message=f"Installation prête : {manifest.name}",
        manifest=manifest,
    )


def _update_registry_files_installed(
    module_name: str,
    copied_files: tuple[str, ...],
    registry_path: str | Path,
) -> None:
    registry = load_installed_modules_registry(registry_path)
    entry = registry["installed"][module_name]
    existing = entry.get("files_installed", [])
    merged = list(dict.fromkeys([*existing, *copied_files]))
    entry["files_installed"] = merged
    save_installed_modules_registry(registry, registry_path)


def install_module_files(
    module_name: str,
    *,
    registry_path: str | Path = MODULE_REGISTRY_FILE,
    dry_run: bool = False,
) -> ModuleFileInstallResult:
    prepared = prepare_module_file_installation(module_name, registry_path=registry_path)
    if dry_run:
        return replace(
            prepared,
            dry_run=True,
            message=f"Installation simulée des fichiers : {module_name}",
        )

    copied: list[str] = []
    for source, target in prepared.planned_files:
        target_path = Path(target)
        if target_path.exists():
            raise ModuleFileConflictError((target,))
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied.append(target)

    copied_files = tuple(copied)
    _update_registry_files_installed(module_name, copied_files, registry_path)
    return replace(
        prepared,
        installed=True,
        copied_files=copied_files,
        message=f"Fichiers installés : {module_name}",
    )
