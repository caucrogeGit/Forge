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
    present = optin_dir.exists() or any((project_root / rel).exists() for rel, _ in files)
    if not present:
        print(f"{STATUS_OK} opt-in {name} déjà débranché (aucune couche optins/{name}/).")
        return 0

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

    _unbranch_routes(project_root / _ROUTES_REL, apply=apply)

    if apply:
        for d in (optin_dir / "migrations", optin_dir, project_root / "optins"):
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
