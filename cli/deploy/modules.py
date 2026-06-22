"""forge module:* — gestion des modules Forge locaux."""

from __future__ import annotations

import argparse
from pathlib import Path

from core.modules import (
    MODULE_REGISTRY_FILE,
    ModuleAlreadyInstalledError,
    ModuleFileConflictError,
    ModuleFileInstallError,
    ModuleNotInstalledError,
    ModuleRegistryError,
    ModuleRemoveError,
    discover_module_manifests,
    install_module_files,
    generate_module_routes,
    install_module_manifest,
    load_module_manifest,
    remove_module,
)
from core.modules.routes import ModuleRouteInjectionError, ModuleRoutesAlreadyGeneratedError
from core.modules.manifest import ModuleManifestError


_DEFAULT_MODULES_DIR = "modules"


def cmd_module_list(args: list[str]) -> None:
    if "--help" in args:
        print("Usage : forge module:list [--path <dossier>]")
        print()
        print("Affiche les modules Forge disponibles dans le dossier de modules.")
        print()
        print("Options :")
        print("  --path <dossier>   dossier de modules (défaut : modules/)")
        raise SystemExit(0)

    parser = argparse.ArgumentParser(prog="forge module:list", add_help=False)
    parser.add_argument("--path", default=None)
    parsed, unknown = parser.parse_known_args(args)

    if unknown:
        print(f"Arguments inconnus : {' '.join(unknown)}")
        raise SystemExit(1)

    modules_path = Path(parsed.path) if parsed.path else Path(_DEFAULT_MODULES_DIR)

    if not modules_path.is_dir():
        print(f"Aucun dossier de modules trouvé : {modules_path}")
        return

    valid, invalid = discover_module_manifests(modules_path)

    if not valid and not invalid:
        print("Aucun module Forge trouvé.")
        return

    if valid:
        print("\nModules Forge disponibles :\n")
        for m in valid:
            print(f"  - {m.name} {m.version} — {m.label}")

    if invalid:
        print("\nModules invalides :\n")
        for name, reason in invalid:
            print(f"  - {name} — {reason}")

    if not valid:
        print("\nAucun module Forge valide trouvé.")


def cmd_module_install(args: list[str]) -> None:
    if "--help" in args:
        print("Usage : forge module:install <nom> [--path <dossier>] [--dry-run]")
        print()
        print("Installe un module Forge dans le registre du projet.")
        print()
        print("Arguments :")
        print("  <nom>   nom du module à installer")
        print()
        print("Options :")
        print("  --path <dossier>   dossier de modules (défaut : modules/)")
        print("  --dry-run          simule l'installation sans rien modifier")
        raise SystemExit(0)

    parser = argparse.ArgumentParser(prog="forge module:install", add_help=False)
    parser.add_argument("name")
    parser.add_argument("--path", default=None)
    parser.add_argument("--dry-run", action="store_true", dest="dry_run")
    parsed, unknown = parser.parse_known_args(args)

    if unknown:
        print(f"Arguments inconnus : {' '.join(unknown)}")
        raise SystemExit(1)

    modules_path = Path(parsed.path) if parsed.path else Path(_DEFAULT_MODULES_DIR)
    module_dir = modules_path / parsed.name

    if not module_dir.is_dir():
        print(f"Module introuvable : {parsed.name}")
        print(f"Dossier de recherche : {modules_path}")
        raise SystemExit(1)

    manifest_path = module_dir / "module.json"
    if not manifest_path.exists():
        print(f"Module introuvable : {parsed.name}")
        print(f"Fichier module.json absent dans : {module_dir}")
        raise SystemExit(1)

    try:
        manifest = load_module_manifest(manifest_path)
    except ModuleManifestError as exc:
        print(f"Module invalide : {parsed.name}")
        print(f"Erreur : {exc}")
        raise SystemExit(1)

    try:
        result = install_module_manifest(
            manifest=manifest,
            source_path=module_dir,
            registry_path=MODULE_REGISTRY_FILE,
            dry_run=parsed.dry_run,
        )
    except ModuleAlreadyInstalledError:
        print(f"Module déjà installé : {parsed.name}")
        raise SystemExit(1)
    except ModuleRegistryError as exc:
        print(f"Erreur lors de l'installation : {exc}")
        raise SystemExit(1)

    if result.dry_run:
        print("\nInstallation simulée du module Forge :\n")
        print(f"  - {manifest.name} {manifest.version} — {manifest.label}")
        print("\nAucun fichier modifié.")
    else:
        print("\nModule Forge installé :\n")
        print(f"  - {manifest.name} {manifest.version} — {manifest.label}")
        print(f"\nRegistre mis à jour : {result.registry_path}")


def cmd_module_routes(args: list[str]) -> None:
    if "--help" in args:
        print("Usage : forge module:routes <nom> [--dry-run]")
        print()
        print("Génère le fichier de routes d'un module Forge installé.")
        print()
        print("Arguments :")
        print("  <nom>   nom du module")
        print()
        print("Options :")
        print("  --dry-run   simule la génération sans rien écrire")
        raise SystemExit(0)

    parser = argparse.ArgumentParser(prog="forge module:routes", add_help=False)
    parser.add_argument("name")
    parser.add_argument("--dry-run", action="store_true", dest="dry_run")
    parsed, unknown = parser.parse_known_args(args)

    if unknown:
        print(f"Arguments inconnus : {' '.join(unknown)}")
        raise SystemExit(1)

    try:
        result = generate_module_routes(parsed.name, dry_run=parsed.dry_run)
    except ModuleRoutesAlreadyGeneratedError as exc:
        print(str(exc))
        raise SystemExit(1)
    except ModuleRouteInjectionError as exc:
        print(str(exc))
        raise SystemExit(1)
    except ModuleRegistryError as exc:
        print(f"Erreur lors de la lecture du registre : {exc}")
        raise SystemExit(1)

    if result.dry_run:
        print(f"\nGénération simulée pour le module : {result.manifest.name}\n")
        print(f"  Fichier qui serait créé : {result.target_path}")
        print("\nAucun fichier modifié.")
    else:
        print(f"\nFichier de routes généré : {result.target_path}\n")

    print("\nPour activer ces routes, ajoutez les lignes suivantes dans mvc/routes.py :\n")
    for line in result.lines_to_add.splitlines():
        print(f"    {line}")
    print()


def cmd_module_files(args: list[str]) -> None:
    if "--help" in args:
        print("Usage : forge module:files <nom> [--dry-run]")
        print()
        print("Installe les fichiers d'un module Forge dans le projet.")
        print()
        print("Arguments :")
        print("  <nom>   nom du module")
        print()
        print("Options :")
        print("  --dry-run   simule l'installation sans rien copier")
        raise SystemExit(0)

    parser = argparse.ArgumentParser(prog="forge module:files", add_help=False)
    parser.add_argument("name")
    parser.add_argument("--dry-run", action="store_true", dest="dry_run")
    parsed, unknown = parser.parse_known_args(args)

    if unknown:
        print(f"Arguments inconnus : {' '.join(unknown)}")
        raise SystemExit(1)

    try:
        result = install_module_files(parsed.name, dry_run=parsed.dry_run)
    except ModuleFileConflictError as exc:
        print("\nInstallation refusée.\n")
        print("Le fichier existe déjà :")
        for path in exc.conflicts:
            print(f"  - {path}")
        print("\nAucun fichier n’a été modifié.")
        raise SystemExit(1)
    except ModuleFileInstallError as exc:
        print(str(exc))
        raise SystemExit(1)
    except ModuleRegistryError as exc:
        print(f"Erreur lors de la lecture du registre : {exc}")
        raise SystemExit(1)

    if result.dry_run:
        print("\nInstallation simulée des fichiers du module :\n")
    else:
        print("\nFichiers du module installés :\n")
    print(f"Module : {result.manifest.name} {result.manifest.version} — {result.manifest.label}")
    if result.dry_run:
        print("\nCopies prévues :")
        for source, target in result.planned_files:
            print(f"  - {source} -> {target}")
        print("\nAucun fichier modifié.")
    else:
        print("\nFichiers copiés :")
        for target in result.copied_files:
            print(f"  - {target}")


def cmd_module_remove(args: list[str]) -> None:
    if "--help" in args:
        print("Usage : forge module:remove <nom> [--dry-run]")
        print()
        print("Désinstalle un module Forge du projet.")
        print()
        print("Arguments :")
        print("  <nom>   nom du module à désinstaller")
        print()
        print("Options :")
        print("  --dry-run   simule la suppression sans rien modifier")
        raise SystemExit(0)

    parser = argparse.ArgumentParser(prog="forge module:remove", add_help=False)
    parser.add_argument("name")
    parser.add_argument("--dry-run", action="store_true", dest="dry_run")
    parsed, unknown = parser.parse_known_args(args)

    if unknown:
        print(f"Arguments inconnus : {' '.join(unknown)}")
        raise SystemExit(1)

    try:
        result = remove_module(parsed.name, dry_run=parsed.dry_run)
    except ModuleNotInstalledError:
        print(f"Module non installé : {parsed.name}")
        raise SystemExit(1)
    except ModuleRemoveError as exc:
        print(f"Erreur lors de la suppression : {exc}")
        raise SystemExit(1)
    except ModuleRegistryError as exc:
        print(f"Erreur lors de la lecture du registre : {exc}")
        raise SystemExit(1)

    if result.dry_run:
        print(f"\nSuppression simulée du module : {result.module_name}\n")
    else:
        print(f"\nModule supprimé : {result.module_name}\n")

    if result.files_deleted:
        label = "Fichiers qui seraient supprimés :" if result.dry_run else "Fichiers supprimés :"
        print(label)
        for path in result.files_deleted:
            print(f"  - {path}")

    if result.files_kept:
        label = "Fichiers conservés :" if result.dry_run else "Fichiers conservés (non supprimés) :"
        print(label)
        for decision in result.files_kept:
            print(f"  - {decision.path} ({decision.reason})")

    print(f"\nRoutes : {result.routes_note}")

    if result.dry_run:
        print("\nAucun fichier modifié.")
    else:
        print(f"\nRegistre mis à jour : {MODULE_REGISTRY_FILE}")


def main(args: list[str]) -> None:
    if not args:
        print(
            "Usage : forge module:list | forge module:install <nom> | "
            "forge module:files <nom> | forge module:routes <nom> | "
            "forge module:remove <nom>"
        )
        raise SystemExit(1)

    command = args[0]

    if command == "module:list":
        cmd_module_list(args[1:])
    elif command == "module:install":
        cmd_module_install(args[1:])
    elif command == "module:files":
        cmd_module_files(args[1:])
    elif command == "module:routes":
        cmd_module_routes(args[1:])
    elif command == "module:remove":
        cmd_module_remove(args[1:])
    else:
        print(f"Commande inconnue : {command!r}")
        raise SystemExit(1)
