# pyright: strict
"""Commande ``forge opt-in:disable <name>`` — OPTIN-CLI-ENGINE-001 (ADR-016, 3b).

Axe **activation** (−) : inverse exact d'``opt-in:enable``. Retire la couche de
câblage ``optins/<name>/`` créée par ``enable`` et débranche
``register_optins`` de ``mvc/routes.py``. Laisse le **package installé**
(présence) : pour désinstaller, voir ``opt-in:remove``.

dry-run par défaut, ``--apply`` pour écrire. Garde §9 : un fichier modifié
manuellement par l'utilisateur est **conservé**, jamais supprimé en silence.

Limité à ``iot`` jusqu'à l'adaptateur 3-formes (ticket 4), qui généralise le
câblage aux six opt-ins.
"""
from __future__ import annotations

from pathlib import Path

from cli.optins.enable import (
    STATUS_DRYRUN,
    STATUS_ERROR,
    STATUS_INFO,
    STATUS_OK,
    STATUS_WARN,
    SUPPORTED_OPTINS,
    REGISTRY_REL,
    registry_call_line,
    registry_import_line,
    unregister_from_registry,
)
from cli.optins.registry_format import read_enabled_optins, remove_optin_entry

_ROUTES_REL = "mvc/routes.py"


def disable_optin(name: str, *, apply: bool, project_root: Path) -> int:
    spec = SUPPORTED_OPTINS.get(name)
    if spec is None:
        print(f"{STATUS_ERROR} opt-in non débranchable : {name}")
        print(f"Opt-ins câblables (kind route) : {', '.join(sorted(SUPPORTED_OPTINS))}")
        return 2

    files = list(spec["files"])
    optin_dir = project_root / "optins" / name
    registry_path = project_root / REGISTRY_REL
    registry_content = (
        registry_path.read_text(encoding="utf-8") if registry_path.exists() else ""
    )
    is_registered = (
        registry_import_line(name) in registry_content
        or registry_call_line(name) in registry_content
        or name in read_enabled_optins(registry_content)
    )
    present = (
        optin_dir.exists()
        or is_registered
        or any((project_root / rel).exists() for rel, _ in files)
    )
    if not present:
        print(f"{STATUS_OK} opt-in {name} déjà débranché (aucune couche optins/{name}/).")
        return 0

    # 1. Fichiers propres à l'opt-in (write-if-new : un fichier modifié à la
    #    main est conservé, jamais supprimé en silence).
    for rel, expected in files:
        target = project_root / rel
        if not target.exists():
            continue
        if target.read_text(encoding="utf-8") != expected:
            print(f"{STATUS_WARN} {rel} modifié manuellement — conservé (suppression à faire à la main).")
            continue
        if apply:
            target.unlink()
            print(f"{STATUS_OK} {rel} supprimé")
        else:
            print(f"{STATUS_DRYRUN} {rel} serait supprimé")

    # 2. Retirer l'opt-in du registre partagé : entrée ENABLED_OPTINS + câblage
    #    de route. Le registre (optins/registry.py, optins/__init__.py) et le
    #    câblage de mvc/routes.py restent des fichiers permanents du squelette
    #    (ADR-061) : jamais supprimés, même quand plus aucun opt-in n'est inscrit.
    new_registry = registry_content
    if registry_content:
        new_registry = unregister_from_registry(new_registry, name)
        new_registry = remove_optin_entry(new_registry, name)
    if registry_content and new_registry != registry_content:
        if apply:
            registry_path.write_text(new_registry, encoding="utf-8")
            print(f"{STATUS_OK} {REGISTRY_REL} : {name} retiré")
        else:
            print(f"{STATUS_DRYRUN} {name} serait retiré de {REGISTRY_REL}")

    # 3. Répertoire propre à l'opt-in (optins/<name>/), retiré s'il est vide.
    if apply:
        for d in (optin_dir / "migrations", optin_dir):
            if d.is_dir() and not any(d.iterdir()):
                d.rmdir()
                print(f"{STATUS_OK} {d.relative_to(project_root)}/ retiré (vide)")
        print(f"{STATUS_INFO} Package {spec['package_dist']} conservé "
              "(utilise `forge opt-in:remove` pour le désinstaller).")
    else:
        print(f"{STATUS_INFO} Aucune modification écrite. Relance avec --apply pour appliquer.")
    return 0


def main(args: list[str] | None = None) -> int:
    """Kind-aware (OPTIN-KIND-ADAPTER-001) : kind ``route`` (iot) → débranchement
    réel ; ``library`` / ``crosscutting`` → conseil de retrait (rien à écrire).
    """
    from cli.optins.catalog import (
        KIND_ROUTE,
        LOCAL_MODULE_HINT,
        OFFICIAL_OPTINS,
        optin_names,
    )

    if args is None:
        args = []
    apply = "--apply" in args
    positionals = [a for a in args if not a.startswith("-")]
    if not positionals:
        print(f"{STATUS_ERROR} nom d'opt-in manquant.")
        print("Usage : forge opt-in:disable <name> [--apply]")
        print(f"Opt-ins officiels : {', '.join(optin_names())}")
        return 2

    name = positionals[0]
    optin = OFFICIAL_OPTINS.get(name)
    if optin is None:
        print(f"{STATUS_ERROR} opt-in inconnu : {name}")
        print(f"Opt-ins officiels : {', '.join(optin_names())}")
        print(LOCAL_MODULE_HINT)
        return 2

    if optin.kind == KIND_ROUTE:
        return disable_optin(name, apply=apply, project_root=Path.cwd())

    # ADR-061 : retirer l'entrée ENABLED_OPTINS de l'opt-in non-route, puis
    # afficher le conseil de retrait. Le registre n'est jamais supprimé.
    _remove_registry_entry(Path.cwd(), name, apply=apply)
    print("")
    from cli.optins.guidance import disable_guidance
    print(disable_guidance(optin))
    return 0


def _remove_registry_entry(project_root: Path, name: str, *, apply: bool) -> None:
    """Retire l'entrée ENABLED_OPTINS de ``name`` du registre (idempotent)."""
    registry_path = project_root / REGISTRY_REL
    if not registry_path.exists():
        return
    content = registry_path.read_text(encoding="utf-8")
    new_content = remove_optin_entry(content, name)
    if new_content == content:
        print(f"{STATUS_OK} {REGISTRY_REL} : {name} déjà retiré")
        return
    if apply:
        registry_path.write_text(new_content, encoding="utf-8")
        print(f"{STATUS_OK} {REGISTRY_REL} : {name} retiré")
    else:
        print(f"{STATUS_DRYRUN} {name} serait retiré de {REGISTRY_REL}")
