# pyright: strict
"""Squelette de projet Forge matérialisé par `forge new` (ADR-024).

`forge new` ne clone plus le dépôt : il copie cet arbre curé
(`cli/skeleton/data/`) dans le projet de l'utilisateur. Le `core` du
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


# Apparat qualité livré par défaut (ADR-063) : typage, tests, documentation, CI
# et hygiène de dépôt. `forge new --bare` produit le squelette sans cet apparat,
# pour un usage avancé (dépôt déjà outillé, démonstration). Les marqueurs
# `# pyright: strict` des fichiers éditables restent (un commentaire inoffensif).
_QUALITY_FILES = frozenset({
    "pyproject.toml",
    "pytest.ini",
    "requirements-dev.txt",
    "requirements-docs.txt",
    "mkdocs.yml",
    "Makefile",
    ".editorconfig",
    "CHANGELOG.md",
})
_QUALITY_DIRS = frozenset({"tests", "docs", ".github"})


def _is_quality_apparatus(rel: Path) -> bool:
    """Vrai pour un fichier de l'apparat qualité (ADR-063), omis en ``bare``."""
    return rel.as_posix() in _QUALITY_FILES or rel.parts[0] in _QUALITY_DIRS


def iter_skeleton_files(*, bare: bool = False) -> list[Path]:
    """Liste triée des fichiers source du squelette (dotfiles compris).

    ``bare=True`` omet l'apparat qualité (ADR-063) : config, tests, doc, CI,
    hygiène de dépôt. Le squelette applicatif minimal reste inchangé.
    """
    files = [p for p in DATA_DIR.rglob("*") if _is_distributable(p)]
    if bare:
        files = [p for p in files if not _is_quality_apparatus(p.relative_to(DATA_DIR))]
    return sorted(files)


def materialize(dest: Path | str, *, bare: bool = False) -> list[Path]:
    """Copie l'arbre squelette dans ``dest`` (créé au besoin).

    Ne supprime rien. Préserve l'arborescence et les dotfiles
    (.gitignore, .gitkeep). ``bare=True`` omet l'apparat qualité (ADR-063).
    Retourne la liste des fichiers écrits.
    """
    root = Path(dest)
    written: list[Path] = []
    for src in iter_skeleton_files(bare=bare):
        target = root / src.relative_to(DATA_DIR)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, target)
        written.append(target)
    return written
