# pyright: strict
"""Découverte des modules Forge dans un dossier local."""

from __future__ import annotations

from pathlib import Path

from .manifest import ModuleManifest, ModuleManifestError, load_module_manifest


def discover_module_manifests(
    root_path: str | Path,
) -> tuple[list[ModuleManifest], list[tuple[str, str]]]:
    """Scanne root_path et retourne (modules_valides, modules_invalides).

    modules_invalides est une liste de paires (nom_dossier, raison).
    Seuls les sous-dossiers directs contenant un fichier module.json sont inspectés.
    """
    root = Path(root_path)
    valid: list[ModuleManifest] = []
    invalid: list[tuple[str, str]] = []

    if not root.is_dir():
        return [], []

    for entry in sorted(root.iterdir()):
        if not entry.is_dir():
            continue
        manifest_path = entry / "module.json"
        if not manifest_path.exists():
            continue
        try:
            manifest = load_module_manifest(manifest_path)
            valid.append(manifest)
        except ModuleManifestError as exc:
            invalid.append((entry.name, str(exc)))

    return valid, invalid


def list_module_manifests(root_path: str | Path) -> list[ModuleManifest]:
    """Retourne la liste des ModuleManifest valides trouvés dans root_path."""
    valid, _ = discover_module_manifests(root_path)
    return valid
