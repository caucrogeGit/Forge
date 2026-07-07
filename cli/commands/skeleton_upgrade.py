# pyright: strict
"""`forge skeleton:upgrade` — ajoute au projet les fichiers du squelette manquants (FORGE-9).

`forge new` crée un projet à partir du squelette, mais rien ne le **met à jour**
quand Forge évolue et enrichit le squelette (nouvel outillage, config qualité…).
`skeleton:upgrade` matérialise, en **write-if-new**, les fichiers du squelette qui
manquent au projet courant : il n'écrase jamais un fichier existant (donc aucune
édition utilisateur perdue), et `--check` liste ce qui serait ajouté sans écrire.

Les fichiers substitués à la création (`env/*`, nom applicatif) préexistent dans
tout projet et sont donc préservés : `skeleton:upgrade` n'a rien à substituer.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from skeleton import DATA_DIR, iter_skeleton_files


def plan_upgrade(root: Path, *, bare: bool = False) -> tuple[list[str], list[str]]:
    """Retourne `(à_ajouter, déjà_présents)` en chemins relatifs POSIX, triés."""
    to_add: list[str] = []
    present: list[str] = []
    for src in iter_skeleton_files(bare=bare):
        rel = src.relative_to(DATA_DIR).as_posix()
        (to_add if not (root / rel).exists() else present).append(rel)
    return sorted(to_add), sorted(present)


def apply_upgrade(root: Path, *, bare: bool = False) -> list[str]:
    """Écrit les fichiers manquants (write-if-new). Retourne les chemins ajoutés."""
    added: list[str] = []
    for src in iter_skeleton_files(bare=bare):
        rel = src.relative_to(DATA_DIR)
        target = root / rel
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, target)
        added.append(rel.as_posix())
    return sorted(added)


def _looks_like_forge_project(root: Path) -> bool:
    return (root / "config.py").exists() or (root / "mvc").is_dir()


def main(argv: list[str] | None = None) -> None:
    import sys

    args = list(sys.argv[1:] if argv is None else argv)
    check = "--check" in args
    bare = "--bare" in args
    # Le dispatcher retire déjà le nom de commande : seuls les flags subsistent.
    positional = [a for a in args if a not in ("--check", "--bare")]
    if positional:
        print("Usage : forge skeleton:upgrade [--check] [--bare]")
        raise SystemExit(1)

    root = Path.cwd()
    if not _looks_like_forge_project(root):
        print("[ERREUR] Répertoire courant : aucun projet Forge détecté (config.py / mvc/ absents).")
        raise SystemExit(1)

    if check:
        to_add, _ = plan_upgrade(root, bare=bare)
        if not to_add:
            print("[OK] Squelette à jour : aucun fichier à ajouter.")
            return
        print(f"[CHECK] {len(to_add)} fichier(s) du squelette manquent (ajoutés par forge skeleton:upgrade) :")
        for path in to_add:
            print(f"  + {path}")
        return

    added = apply_upgrade(root, bare=bare)
    if not added:
        print("[OK] Squelette déjà à jour : rien à ajouter.")
        return
    print(f"[OK] {len(added)} fichier(s) ajouté(s) (write-if-new, aucun fichier existant modifié) :")
    for path in added:
        print(f"  [CREE] {path}")
