"""Système de modules Forge — contrat, validation, découverte et registre."""

from .manifest import (
    ALLOWED_PROVIDES,
    ModuleManifest,
    ModuleManifestError,
    load_module_manifest,
    validate_module_manifest,
    validate_module_name,
    validate_module_version,
)
from .discovery import discover_module_manifests, list_module_manifests
from .registry import (
    MODULE_REGISTRY_FILE,
    ModuleAlreadyInstalledError,
    ModuleInstallResult,
    ModuleRegistryError,
    install_module_manifest,
    is_module_installed,
    load_installed_modules_registry,
    prepare_module_installation,
    save_installed_modules_registry,
)
from .routes import (
    ModuleRouteInjectionError,
    ModuleRoutesAlreadyGeneratedError,
    ModuleRouteGenerationResult,
    generate_module_routes,
)
from .files import (
    INSTALLABLE_PROVIDES,
    ModuleFileConflictError,
    ModuleFileInstallError,
    ModuleFileInstallResult,
    install_module_files,
    prepare_module_file_installation,
)
from .remove import (
    FileRemovalDecision,
    ModuleNotInstalledError,
    ModuleRemoveError,
    ModuleRemoveResult,
    remove_module,
)

__all__ = [
    "ModuleManifest",
    "ModuleManifestError",
    "ALLOWED_PROVIDES",
    "validate_module_name",
    "validate_module_version",
    "validate_module_manifest",
    "load_module_manifest",
    "discover_module_manifests",
    "list_module_manifests",
    "MODULE_REGISTRY_FILE",
    "ModuleRegistryError",
    "ModuleAlreadyInstalledError",
    "ModuleInstallResult",
    "load_installed_modules_registry",
    "save_installed_modules_registry",
    "is_module_installed",
    "prepare_module_installation",
    "install_module_manifest",
    "ModuleRouteInjectionError",
    "ModuleRoutesAlreadyGeneratedError",
    "ModuleRouteGenerationResult",
    "generate_module_routes",
    "INSTALLABLE_PROVIDES",
    "ModuleFileInstallError",
    "ModuleFileConflictError",
    "ModuleFileInstallResult",
    "prepare_module_file_installation",
    "install_module_files",
    "FileRemovalDecision",
    "ModuleRemoveError",
    "ModuleNotInstalledError",
    "ModuleRemoveResult",
    "remove_module",
]
