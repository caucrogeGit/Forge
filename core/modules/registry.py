# pyright: strict
"""Registre des modules Forge installés."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from .manifest import ModuleManifest


_URL_RE = re.compile(r"https?://|ftp://", re.IGNORECASE)

MODULE_REGISTRY_FILE = "forge_modules.json"


class ModuleRegistryError(ValueError):
    """Erreur liée au registre des modules installés."""


class ModuleAlreadyInstalledError(ModuleRegistryError):
    """Le module est déjà présent dans le registre."""


@dataclass(frozen=True)
class ModuleInstallResult:
    manifest: ModuleManifest
    registry_path: str
    dry_run: bool
    installed: bool
    message: str


def load_installed_modules_registry(
    path: str | Path = MODULE_REGISTRY_FILE,
) -> dict[str, Any]:
    """Charge le registre. Retourne {"installed": {}} si le fichier est absent."""
    p = Path(path)
    if not p.exists():
        return {"installed": {}}
    try:
        raw = p.read_text(encoding="utf-8")
    except OSError as exc:
        raise ModuleRegistryError(f"impossible de lire {p}: {exc}") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ModuleRegistryError(f"JSON invalide dans {p}: {exc}") from exc
    if not isinstance(data, dict) or "installed" not in data:
        raise ModuleRegistryError(
            f"structure invalide dans {p} : clé 'installed' manquante"
        )
    if not isinstance(data["installed"], dict):
        raise ModuleRegistryError(
            f"structure invalide dans {p} : 'installed' doit être un dictionnaire"
        )
    return cast("dict[str, Any]", data)


def save_installed_modules_registry(
    registry: dict[str, Any],
    path: str | Path = MODULE_REGISTRY_FILE,
) -> None:
    """Écrit le registre en JSON lisible."""
    p = Path(path)
    try:
        p.write_text(
            json.dumps(registry, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError as exc:
        raise ModuleRegistryError(f"impossible d'écrire {p}: {exc}") from exc


def is_module_installed(registry: dict[str, Any], name: str) -> bool:
    """Retourne True si le module est déjà présent dans registry['installed']."""
    return name in registry.get("installed", {})


def prepare_module_installation(
    manifest: ModuleManifest,
    source_path: str | Path,
) -> dict[str, Any]:
    """Prépare l'entrée de registre pour un module.

    Refuse les URL et les traversées '..' .
    Tente de relativiser les chemins absolus depuis le répertoire de travail.
    """
    source_str = str(source_path)

    if _URL_RE.search(source_str):
        raise ModuleRegistryError("source: ne doit pas contenir d'URL")

    source = Path(source_path)
    normalized = source_str.replace("\\", "/")
    if any(part == ".." for part in normalized.split("/")):
        raise ModuleRegistryError("source: ne doit pas contenir '..'")

    if source.is_absolute():
        try:
            source = source.relative_to(Path.cwd())
        except ValueError:
            raise ModuleRegistryError(
                f"source: chemin absolu hors du répertoire de travail non accepté : {source}"
            )

    entry: dict[str, Any] = {
        "name": manifest.name,
        "label": manifest.label,
        "version": manifest.version,
        "description": manifest.description,
        "source": str(source).replace("\\", "/"),
    }
    if manifest.provides:
        entry["provides"] = list(manifest.provides)
    return entry


def install_module_manifest(
    manifest: ModuleManifest,
    source_path: str | Path,
    registry_path: str | Path = MODULE_REGISTRY_FILE,
    dry_run: bool = False,
) -> ModuleInstallResult:
    """Installe déclarativement un module dans le registre.

    En dry_run, simule sans écrire.
    Refuse une double installation.
    """
    registry = load_installed_modules_registry(registry_path)

    if is_module_installed(registry, manifest.name):
        raise ModuleAlreadyInstalledError(
            f"module déjà installé : {manifest.name}"
        )

    entry = prepare_module_installation(manifest, source_path)

    updated: dict[str, Any] = {
        "installed": {**registry["installed"], manifest.name: entry}
    }

    if not dry_run:
        save_installed_modules_registry(updated, registry_path)
        message = f"Module installé : {manifest.name}"
    else:
        message = f"Installation simulée : {manifest.name}"

    return ModuleInstallResult(
        manifest=manifest,
        registry_path=str(registry_path),
        dry_run=dry_run,
        installed=not dry_run,
        message=message,
    )
