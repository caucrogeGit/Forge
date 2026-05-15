"""Préparation et génération explicite des routes de modules Forge."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .manifest import ModuleManifest, ModuleManifestError, load_module_manifest
from .registry import MODULE_REGISTRY_FILE, load_installed_modules_registry


MODULE_ROUTES_FILE = Path("mvc/module_routes.py")
_URL_RE = re.compile(r"https?://|ftp://", re.IGNORECASE)


class ModuleRouteInjectionError(ValueError):
    """Erreur lors de la préparation ou génération des routes d'un module."""


class ModuleRoutesAlreadyInjectedError(ModuleRouteInjectionError):
    """Les routes du module sont déjà présentes dans le fichier cible (ancien format)."""


class ModuleRoutesAlreadyGeneratedError(ModuleRouteInjectionError):
    """Un fichier de routes dédié existe déjà pour ce module."""


@dataclass(frozen=True)
class ModuleRouteInjectionResult:
    module_name: str
    source_routes_path: str
    target_routes_path: str
    dry_run: bool
    injected: bool
    message: str
    manifest: ModuleManifest
    injection_block: str


@dataclass(frozen=True)
class ModuleRouteGenerationResult:
    module_name: str
    target_path: str
    dry_run: bool
    generated: bool
    lines_to_add: str
    manifest: ModuleManifest


def _safe_registry_source(source: str) -> Path:
    if _URL_RE.search(source):
        raise ModuleRouteInjectionError("source: ne doit pas contenir d'URL")
    normalized = source.replace("\\", "/")
    if any(part == ".." for part in normalized.split("/")):
        raise ModuleRouteInjectionError("source: ne doit pas contenir '..'")
    path = Path(source)
    if path.is_absolute():
        raise ModuleRouteInjectionError("source: ne doit pas être un chemin absolu")
    return path


def _safe_routes_path(manifest: ModuleManifest) -> str:
    if "routes" not in manifest.provides:
        raise ModuleRouteInjectionError(
            f"Le module {manifest.name} ne déclare pas de routes."
        )
    routes_path = manifest.paths.get("routes")
    if not routes_path:
        raise ModuleRouteInjectionError(
            f"paths.routes manquant pour le module : {manifest.name}"
        )
    if _URL_RE.search(routes_path):
        raise ModuleRouteInjectionError("paths.routes: ne doit pas contenir d'URL")
    normalized = routes_path.replace("\\", "/")
    if any(part == ".." for part in normalized.split("/")):
        raise ModuleRouteInjectionError("paths.routes: ne doit pas contenir '..'")
    path = Path(routes_path)
    if path.is_absolute():
        raise ModuleRouteInjectionError("paths.routes: ne doit pas être un chemin absolu")
    return normalized


def _module_import_path(source_dir: Path, routes_path: str) -> str:
    route_file = (source_dir / routes_path).with_suffix("")
    return ".".join(route_file.parts)


def _module_marker(name: str) -> tuple[str, str]:
    return (
        f"    # forge-module-routes:{name}:start\n",
        f"    # forge-module-routes:{name}:end\n",
    )


def _build_injection_block(manifest: ModuleManifest, source_dir: Path, routes_path: str) -> str:
    start, end = _module_marker(manifest.name)
    import_path = _module_import_path(source_dir, routes_path)
    alias = f"register_{manifest.name}_routes"
    return (
        start +
        f"    from {import_path} import register_routes as {alias}\n"
        f"    {alias}(router)\n"
        f"{end}"
    )


def _format_lines_to_add(module_name: str) -> str:
    """Retourne les lignes à copier dans mvc/routes.py pour activer le module."""
    alias = f"register_{module_name}_routes"
    return (
        f"from mvc.routes_{module_name} import {alias}\n"
        f"{alias}(router)\n"
    )


def _module_routes_file_content(module_name: str, import_path: str, alias: str) -> str:
    """Contenu du fichier mvc/routes_<module>.py généré."""
    return (
        f'"""Routes du module Forge "{module_name}".\n'
        f"\n"
        f"Fichier genere par `forge module:routes {module_name}`. Regenerable.\n"
        f"Pour activer ces routes, ajoutez dans mvc/routes.py :\n"
        f"\n"
        f"    from mvc.routes_{module_name} import {alias}\n"
        f"    {alias}(router)\n"
        f'"""\n'
        f"from {import_path} import register_routes as {alias}\n"
        f"\n"
        f'__all__ = ["{alias}"]\n'
    )


def _load_and_validate_module(
    module_name: str,
    registry_path: str | Path,
) -> tuple[ModuleManifest, Path, str]:
    """Valide le registre, charge le manifeste, vérifie le fichier de routes.

    Retourne (manifest, source_dir, routes_path).
    """
    registry = load_installed_modules_registry(registry_path)
    installed = registry.get("installed", {})
    if module_name not in installed:
        raise ModuleRouteInjectionError(
            f"Module non installé : {module_name}\n"
            f"Lance d'abord : forge module:install {module_name}"
        )

    entry = installed[module_name]
    source_dir = _safe_registry_source(entry.get("source", ""))
    manifest_path = source_dir / "module.json"
    try:
        manifest = load_module_manifest(manifest_path)
    except ModuleManifestError as exc:
        raise ModuleRouteInjectionError(str(exc)) from exc
    if manifest.name != module_name:
        raise ModuleRouteInjectionError(
            f"module.json incohérent : attendu {module_name}, obtenu {manifest.name}"
        )

    routes_path = _safe_routes_path(manifest)
    source_routes_path = source_dir / routes_path
    if not source_routes_path.exists():
        raise ModuleRouteInjectionError(
            f"Fichier de routes introuvable : {source_routes_path.as_posix()}"
        )

    return manifest, source_dir, routes_path


def prepare_module_route_injection(
    module_name: str,
    *,
    registry_path: str | Path = MODULE_REGISTRY_FILE,
    target_routes_path: str | Path = MODULE_ROUTES_FILE,
    app_routes_path: str | Path = "mvc/routes.py",
) -> ModuleRouteInjectionResult:
    manifest, source_dir, routes_path = _load_and_validate_module(
        module_name, registry_path
    )
    source_routes_path = source_dir / routes_path

    target = Path(target_routes_path)
    target_content = target.read_text(encoding="utf-8") if target.exists() else ""
    start_marker, _ = _module_marker(module_name)
    if start_marker.strip() in target_content:
        raise ModuleRoutesAlreadyInjectedError(
            f"Routes déjà injectées pour le module : {module_name}"
        )

    block = _build_injection_block(manifest, source_dir, routes_path)
    return ModuleRouteInjectionResult(
        module_name=manifest.name,
        source_routes_path=source_routes_path.as_posix(),
        target_routes_path=target.as_posix(),
        dry_run=False,
        injected=False,
        message=f"Préparation prête : {manifest.name}",
        manifest=manifest,
        injection_block=block,
    )


def generate_module_routes(
    module_name: str,
    *,
    registry_path: str | Path = MODULE_REGISTRY_FILE,
    dry_run: bool = False,
) -> ModuleRouteGenerationResult:
    """Génère un fichier de routes dédié mvc/routes_<module>.py.

    Ne modifie jamais mvc/routes.py. Le développeur copie les lignes
    affichées dans son fichier de routes.
    """
    manifest, source_dir, routes_path = _load_and_validate_module(
        module_name, registry_path
    )

    target_file = Path(f"mvc/routes_{module_name}.py")

    if dry_run:
        return ModuleRouteGenerationResult(
            module_name=manifest.name,
            target_path=target_file.as_posix(),
            dry_run=True,
            generated=False,
            lines_to_add=_format_lines_to_add(module_name),
            manifest=manifest,
        )

    if target_file.exists():
        raise ModuleRoutesAlreadyGeneratedError(
            f"Le fichier {target_file} existe déjà. "
            f"Supprimez-le manuellement pour le régénérer."
        )

    import_path = _module_import_path(source_dir, routes_path)
    alias = f"register_{module_name}_routes"
    file_content = _module_routes_file_content(module_name, import_path, alias)

    target_file.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_text(file_content, encoding="utf-8")

    return ModuleRouteGenerationResult(
        module_name=manifest.name,
        target_path=target_file.as_posix(),
        dry_run=False,
        generated=True,
        lines_to_add=_format_lines_to_add(module_name),
        manifest=manifest,
    )
