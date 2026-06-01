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

from forge_cli.optins.enable import (
    STATUS_DRYRUN,
    STATUS_ERROR,
    STATUS_INFO,
    STATUS_OK,
    STATUS_WARN,
    SUPPORTED_OPTINS,
    _OPTINS_INIT,
    _REGISTRY,
    _REGISTRY_REL,
    _registry_call_line,
    _registry_has_registrations,
    _registry_import_line,
    _unregister_from_registry,
)

_ROUTES_REL = "mvc/routes.py"
_ROUTES_IMPORT = "from optins.registry import register_optins"
_ROUTES_CALL = "register_optins(router)"


def _unbranch_routes(routes_path: Path, *, apply: bool) -> None:
    """Retire l'import et l'appel ``register_optins`` injectés par ``enable``.

    Ne touche **que** ces deux lignes (jamais d'autre code utilisateur).
    """
    if not routes_path.exists():
        return
    content = routes_path.read_text(encoding="utf-8")
    if _ROUTES_CALL not in content and _ROUTES_IMPORT not in content:
        return
    kept = [
        line for line in content.splitlines(keepends=True)
        if line.strip() not in (_ROUTES_IMPORT, _ROUTES_CALL)
    ]
    if apply:
        routes_path.write_text("".join(kept), encoding="utf-8")
        print(f"{STATUS_OK} {_ROUTES_REL} débranché (import + {_ROUTES_CALL} retirés)")
    else:
        print(f"{STATUS_DRYRUN} {_ROUTES_REL} serait débranché")


def disable_optin(name: str, *, apply: bool, project_root: Path) -> int:
    spec = SUPPORTED_OPTINS.get(name)
    if spec is None:
        print(f"{STATUS_ERROR} opt-in non débranchable : {name}")
        print(f"Opt-ins câblables (kind route) : {', '.join(sorted(SUPPORTED_OPTINS))}")
        return 2

    files = list(spec["files"])
    optin_dir = project_root / "optins" / name
    registry_path = project_root / _REGISTRY_REL
    registry_content = (
        registry_path.read_text(encoding="utf-8") if registry_path.exists() else ""
    )
    is_registered = (
        _registry_import_line(name) in registry_content
        or _registry_call_line(name) in registry_content
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

    # 2. Dé-référencer l'opt-in de la registry partagée.
    new_registry = (
        _unregister_from_registry(registry_content, name) if registry_content else ""
    )
    others_remain = _registry_has_registrations(new_registry)
    # Démontage complet seulement si plus aucun opt-in ET registry générique
    # (un fichier modifié à la main n'est pas démonté agressivement).
    full_teardown = (
        registry_content != "" and not others_remain and new_registry == _REGISTRY
    )

    if registry_content and new_registry != registry_content:
        if full_teardown:
            if apply:
                registry_path.unlink()
                print(f"{STATUS_OK} {_REGISTRY_REL} supprimé (plus d'opt-in branché)")
            else:
                print(f"{STATUS_DRYRUN} {_REGISTRY_REL} serait supprimé")
        else:
            if apply:
                registry_path.write_text(new_registry, encoding="utf-8")
                print(f"{STATUS_OK} {_REGISTRY_REL} : {name} débranché")
            else:
                print(f"{STATUS_DRYRUN} {name} serait débranché de {_REGISTRY_REL}")

    # 3. Câblage partagé (optins/__init__.py + mvc/routes.py) : retiré seulement
    #    en démontage complet ; sinon conservé pour les autres opt-ins.
    if full_teardown:
        init_path = project_root / "optins" / "__init__.py"
        if init_path.exists() and init_path.read_text(encoding="utf-8") == _OPTINS_INIT:
            if apply:
                init_path.unlink()
                print(f"{STATUS_OK} optins/__init__.py supprimé")
            else:
                print(f"{STATUS_DRYRUN} optins/__init__.py serait supprimé")
        _unbranch_routes(project_root / _ROUTES_REL, apply=apply)
    elif others_remain:
        print(f"{STATUS_INFO} D'autres opt-ins restent branchés — "
              f"{_REGISTRY_REL} et {_ROUTES_REL} conservés.")

    # 4. Répertoires vides.
    if apply:
        dirs = [optin_dir / "migrations", optin_dir]
        if full_teardown:
            dirs.append(project_root / "optins")
        for d in dirs:
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
    from forge_cli.optins.catalog import (
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

    from forge_cli.optins.guidance import disable_guidance
    print(disable_guidance(optin))
    return 0
