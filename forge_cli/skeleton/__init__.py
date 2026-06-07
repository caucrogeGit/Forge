"""Squelette de projet Forge matérialisé par `forge new` (ADR-024).

`forge new` ne clone plus le dépôt : il copie cet arbre curé
(`forge_cli/skeleton/data/`) dans le projet de l'utilisateur. Le `core` du
projet provient ensuite du paquet installé `forge-mvc` (voir
`data/requirements.txt`), pas d'un `core/` local.

API publique :
- ``DATA_DIR`` : racine de l'arbre squelette ;
- ``iter_skeleton_files()`` : itère les fichiers source (hors bytecode) ;
- ``materialize(dest)`` : copie l'arbre dans ``dest`` et retourne les fichiers
  écrits.

Le câblage de `forge new` sur ``materialize`` est l'objet du ticket
``NEW-MATERIALIZE-001``.
"""

from __future__ import annotations

import shutil
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"


def _is_distributable(path: Path) -> bool:
    """Vrai pour un fichier du squelette à recopier (exclut le bytecode)."""
    return (
        path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix not in {".pyc", ".pyo"}
    )


def iter_skeleton_files() -> list[Path]:
    """Liste triée des fichiers source du squelette (dotfiles compris)."""
    return sorted(p for p in DATA_DIR.rglob("*") if _is_distributable(p))


def materialize(dest: Path | str) -> list[Path]:
    """Copie l'arbre squelette dans ``dest`` (créé au besoin).

    Ne supprime rien. Préserve l'arborescence et les dotfiles
    (.gitignore, .gitkeep). Retourne la liste des fichiers écrits.
    """
    root = Path(dest)
    written: list[Path] = []
    for src in iter_skeleton_files():
        target = root / src.relative_to(DATA_DIR)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, target)
        written.append(target)
    return written
