"""Garde-fou : chaque module-bibliothèque public d'un opt-in est documenté (ADR-038).

Pour chaque paquet ``packages/forge-mvc-*``, vérifie que tout module ``.py``
public « bibliothèque » (hors CLI, hors plomberie) est mentionné dans la doc
embarquée du paquet (``docs/*.md``), par son nom de fichier **ou** l'un de ses
symboles publics (fonction/classe top-level sans underscore).

Ne couvre pas :
- les commandes CLI (``cli/*.py``), documentées par leur nom de commande et
  couvertes par les garde-fous d'aide CLI ;
- la plomberie (``__init__``, ``commands``) et les modules privés (``_*``) ;
- les shims de ré-export listés dans ``EXCLUSIONS``.

But : attraper un module de bibliothèque réellement absent de la doc, sans
imposer une fiche par fichier (ADR-038 n'exige qu'une doc embarquée par paquet).
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
PACKAGES = PROJECT_ROOT / "packages"

# Modules exclus : shims de ré-export sans surface publique propre à documenter.
EXCLUSIONS: set[str] = {
    # Ré-export du cœur (cli.project.views_namespace), canonique documenté côté
    # cœur ; l'opt-in ne fait que le ré-exporter (ADR-073).
    "packages/forge-mvc-entities/forge_mvc_entities/crud/views_namespace.py",
}

_PLUMBING = {"__init__", "commands", "conftest"}


def _import_dir(pkg: Path) -> "Path | None":
    return next(
        (
            d
            for d in pkg.iterdir()
            if d.is_dir()
            and d.name.startswith("forge_mvc_")
            and not d.name.endswith(".egg-info")
            and (d / "__init__.py").exists()
        ),
        None,
    )


def _public_symbols(pyfile: Path) -> set[str]:
    try:
        tree = ast.parse(pyfile.read_text(encoding="utf-8"))
    except SyntaxError:
        return set()
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and not node.name.startswith("_")
    }


def _library_modules(imp: Path) -> list[Path]:
    modules: list[Path] = []
    for path in imp.rglob("*.py"):
        parts = path.relative_to(imp).parts
        if "cli" in parts or "tests" in parts or "build" in parts:
            continue
        if path.stem in _PLUMBING or path.stem.startswith("_"):
            continue
        modules.append(path)
    return modules


def _opt_in_packages() -> list[Path]:
    return sorted(
        p
        for p in PACKAGES.iterdir()
        if (p / "pyproject.toml").is_file() and _import_dir(p) is not None
    )


@pytest.mark.parametrize("pkg", _opt_in_packages(), ids=lambda p: p.name)
def test_library_modules_are_documented(pkg: Path) -> None:
    imp = _import_dir(pkg)
    assert imp is not None
    docs = pkg / "docs"
    doctext = (
        "\n".join(m.read_text(encoding="utf-8") for m in docs.rglob("*.md"))
        if docs.is_dir()
        else ""
    )

    missing: list[str] = []
    for mod in _library_modules(imp):
        if mod.relative_to(PROJECT_ROOT).as_posix() in EXCLUSIONS:
            continue
        symbols = _public_symbols(mod)
        if mod.stem in doctext or any(sym in doctext for sym in symbols):
            continue
        listed = ", ".join(sorted(symbols)[:4]) or "aucun symbole public"
        missing.append(f"{mod.relative_to(imp).as_posix()} ({listed})")

    assert not missing, (
        f"{pkg.name} : module(s) de bibliothèque public(s) absent(s) de docs/ :\n  "
        + "\n  ".join(missing)
        + "\n\nAjoutez une mention (nom de fichier ou symbole public) dans le "
        "reference.md du paquet, ou classez le module dans EXCLUSIONS avec justification."
    )
