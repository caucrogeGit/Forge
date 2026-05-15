"""Suppression contrôlée des modules Forge."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from .manifest import ModuleManifestError, load_module_manifest
from .registry import (
    MODULE_REGISTRY_FILE,
    load_installed_modules_registry,
    save_installed_modules_registry,
)
from .routes import MODULE_ROUTES_FILE


_URL_RE = re.compile(r"https?://|ftp://", re.IGNORECASE)


class ModuleRemoveError(ValueError):
    """Erreur lors de la désinstallation d'un module."""


class ModuleNotInstalledError(ModuleRemoveError):
    """Le module n'est pas dans le registre."""


@dataclass(frozen=True)
class FileRemovalDecision:
    path: str
    action: str   # "delete" | "keep_modified" | "keep_source_missing" | "already_absent"
    reason: str


@dataclass(frozen=True)
class ModuleRemoveResult:
    module_name: str
    dry_run: bool
    files_deleted: tuple[str, ...]
    files_kept: tuple[FileRemovalDecision, ...]
    routes_removed: bool
    routes_note: str
    registry_updated: bool
    message: str


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_registry_source(source: str) -> Path:
    if _URL_RE.search(source):
        raise ModuleRemoveError("source: ne doit pas contenir d'URL")
    normalized = source.replace("\\", "/")
    if any(part == ".." for part in normalized.split("/")):
        raise ModuleRemoveError("source: ne doit pas contenir '..'")
    path = Path(source)
    if path.is_absolute():
        raise ModuleRemoveError("source: ne doit pas être un chemin absolu")
    return path


def _build_source_map(registry_entry: dict, module_name: str) -> dict[str, str]:
    """
    Reconstruit le mapping {target_path: source_path} depuis le manifeste source.
    Retourne {} si le dossier source est inaccessible ou le manifeste invalide.
    """
    from .files import _planned_file_pairs

    source_str = registry_entry.get("source", "")
    try:
        source_dir = _safe_registry_source(source_str)
    except ModuleRemoveError:
        return {}

    manifest_path = source_dir / "module.json"
    if not manifest_path.exists():
        return {}

    try:
        manifest = load_module_manifest(manifest_path)
    except ModuleManifestError:
        return {}

    if manifest.name != module_name:
        return {}

    try:
        pairs = _planned_file_pairs(manifest, source_dir)
    except Exception:
        return {}

    return {target: source for source, target in pairs}


def _decide_file(target_str: str, source_map: dict[str, str]) -> FileRemovalDecision:
    target = Path(target_str)
    if not target.exists():
        return FileRemovalDecision(target_str, "already_absent", "fichier absent (déjà supprimé ?)")
    source_str = source_map.get(target_str)
    if source_str is None:
        return FileRemovalDecision(target_str, "keep_source_missing", "source introuvable, impossible de vérifier")
    source = Path(source_str)
    if not source.exists():
        return FileRemovalDecision(target_str, "keep_source_missing", "source introuvable, impossible de vérifier")
    if _file_hash(target) == _file_hash(source):
        return FileRemovalDecision(target_str, "delete", "identique à la source")
    return FileRemovalDecision(target_str, "keep_modified", "modifié manuellement, conservé")


def _remove_routes_block(
    module_name: str,
    routes_file: Path,
) -> tuple[str, str, bool]:
    """
    Tente de retirer le bloc de routes d'un module dans le fichier cible.
    Retourne (nouveau_contenu, note, retiré).
    """
    if not routes_file.exists():
        return "", "Fichier de routes absent — aucune route à retirer", False

    content = routes_file.read_text(encoding="utf-8")
    start_marker = f"    # forge-module-routes:{module_name}:start\n"
    end_marker = f"    # forge-module-routes:{module_name}:end\n"

    if start_marker not in content:
        return content, "Routes non injectées ou marqueurs absents — nettoyage manuel requis si nécessaire", False

    if end_marker not in content:
        return content, "Marqueur de fin absent — nettoyage manuel requis", False

    start_idx = content.index(start_marker)
    end_idx = content.index(end_marker, start_idx) + len(end_marker)
    new_content = content[:start_idx] + content[end_idx:]
    return new_content, "Routes retirées", True


def remove_module(
    module_name: str,
    *,
    registry_path: str | Path = MODULE_REGISTRY_FILE,
    routes_file: str | Path = MODULE_ROUTES_FILE,
    dry_run: bool = False,
) -> ModuleRemoveResult:
    """
    Supprime un module installé du registre et de ses fichiers copiés.

    Règle centrale : Forge ne supprime que ce qu'il peut prouver avoir installé sans modification.

    - Les fichiers identiques à leur source sont supprimés.
    - Les fichiers modifiés ou dont la source est introuvable sont conservés.
    - Les routes injectées avec marqueurs reconnus sont retirées.
    - Le registre est mis à jour.
    - En dry_run, aucun fichier n'est modifié.
    """
    registry = load_installed_modules_registry(registry_path)
    installed = registry.get("installed", {})
    if module_name not in installed:
        raise ModuleNotInstalledError(f"Module non installé : {module_name}")

    entry = installed[module_name]
    files_installed: list[str] = entry.get("files_installed", [])

    # Protection path traversal sur les chemins tracés
    for fpath in files_installed:
        normalized = str(fpath).replace("\\", "/")
        if any(part == ".." for part in normalized.split("/")):
            raise ModuleRemoveError(f"Chemin suspect dans forge_modules.json : {fpath}")
        if Path(fpath).is_absolute():
            raise ModuleRemoveError(f"Chemin absolu interdit dans forge_modules.json : {fpath}")

    # Mapping target → source
    source_map = _build_source_map(entry, module_name)

    # Décision par fichier
    decisions: list[FileRemovalDecision] = [
        _decide_file(f, source_map) for f in files_installed
    ]
    files_to_delete = [d.path for d in decisions if d.action == "delete"]
    files_to_keep = tuple(d for d in decisions if d.action != "delete")

    # Routes
    routes_path = Path(routes_file)
    new_routes_content, routes_note, routes_removed = _remove_routes_block(module_name, routes_path)

    if dry_run:
        kept_count = len(files_to_keep)
        msg = f"Suppression simulée : {module_name}"
        if kept_count:
            msg += f" ({kept_count} fichier(s) conservé(s))"
        return ModuleRemoveResult(
            module_name=module_name,
            dry_run=True,
            files_deleted=tuple(files_to_delete),
            files_kept=files_to_keep,
            routes_removed=routes_removed,
            routes_note=routes_note,
            registry_updated=False,
            message=msg,
        )

    # Suppression réelle
    actually_deleted: list[str] = []
    for path_str in files_to_delete:
        path = Path(path_str)
        if path.exists():
            path.unlink()
            actually_deleted.append(path_str)

    if routes_removed:
        routes_path.write_text(new_routes_content, encoding="utf-8")

    new_installed = {k: v for k, v in installed.items() if k != module_name}
    save_installed_modules_registry({"installed": new_installed}, registry_path)

    kept_count = len(files_to_keep)
    msg = f"Module supprimé : {module_name}"
    if kept_count:
        msg += f" ({kept_count} fichier(s) conservé(s) — modifiés ou source introuvable)"

    return ModuleRemoveResult(
        module_name=module_name,
        dry_run=False,
        files_deleted=tuple(actually_deleted),
        files_kept=files_to_keep,
        routes_removed=routes_removed,
        routes_note=routes_note,
        registry_updated=True,
        message=msg,
    )
