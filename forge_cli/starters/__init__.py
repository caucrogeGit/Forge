"""forge starter:list et forge starter:build."""

from __future__ import annotations

import sys

from forge_cli.starters._exceptions import StarterBuildError
from forge_cli.starters.registry import all_starters, resolve, StarterNotFound, StarterUnavailable
from forge_cli.starters.builder import build, dry_run


# ── starter:list ──────────────────────────────────────────────────────────────

def cmd_starter_list() -> None:
    starters = all_starters()
    print(f"\nStarter apps Forge\n")
    for s in starters:
        status = "disponible" if s.get("status") == "available" else "à venir"
        name = s["name"]
        number = s.get("number", "?")
        description = s.get("description", "")
        print(f"  {number}  {name:<38}  {status}")
        print(f"     {description}")
        if s.get("doc_url"):
            print(f"     docs : {s['doc_url']}")
        print()


# ── starter:build ─────────────────────────────────────────────────────────────

def cmd_starter_build(args: list[str]) -> None:
    if not args:
        print("Usage : forge starter:build <n|nom> [--dry-run] [--init-db] [--force] [--public]")
        raise SystemExit(1)

    identifier = args[0]
    dry = "--dry-run" in args
    init_db = "--init-db" in args
    force = "--force" in args
    public = "--public" in args

    unknown = [a for a in args[1:] if a not in ("--dry-run", "--init-db", "--force", "--public")]
    if unknown:
        print(f"Arguments inconnus : {' '.join(unknown)}")
        raise SystemExit(1)

    try:
        meta = resolve(identifier)
    except StarterNotFound as exc:
        print(str(exc))
        raise SystemExit(1)

    if meta.get("status") != "available":
        name = meta.get("name", identifier)
        print(f"Le starter « {name} » n'est pas encore disponible.")
        print("Voir : forge starter:list")
        raise SystemExit(1)

    if public and meta.get("supports_public") is False:
        print(
            "--public n'est pas applicable à ce starter : "
            "il contient volontairement des routes publiques et protégées."
        )
        raise SystemExit(1)

    if dry:
        dry_run(meta, public=public)
        return

    try:
        build(meta, init_db=init_db, force=force, public=public)
    except StarterBuildError as exc:
        print(f"\n[ERREUR] {exc}")
        raise SystemExit(1)


# ── Entrée principale ─────────────────────────────────────────────────────────

def main(args: list[str]) -> None:
    if not args:
        print("Usage : forge starter:list | forge starter:build <n>")
        raise SystemExit(1)

    command = args[0]

    if command == "starter:list":
        cmd_starter_list()
    elif command == "starter:build":
        cmd_starter_build(args[1:])
    else:
        print(f"Commande inconnue : {command!r}")
        raise SystemExit(1)
