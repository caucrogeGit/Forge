"""Garde-fou EMBEDDED-DOCS-IMPORTS-001.

Vérifie que tous les exemples Python des docs embarquées du dépôt
(`core/*/docs/**`, `cli/*/docs/**` et `packages/*/docs/**` : références ET
welcomes) ont des imports du cœur, du CLI et des opt-ins qui **résolvent
réellement** (module importable + symbole présent).

Complète `test_docs_imports_validity_sweep_001` qui ne couvre que `docs/` et les
`README.md` des paquets, pas les docs embarquées par sous-paquet. Détecte une doc
qui référence du code déplacé/renommé (ex. un symbole importé depuis le mauvais
module).
"""
from __future__ import annotations

import ast
import importlib
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Racines de docs embarquées (un sous-paquet = un dossier docs/).
_DOC_GLOBS = ("core/*/docs/**/*.md", "cli/*/docs/**/*.md", "packages/*/docs/**/*.md")

# Racines de projet utilisateur : présentes dans un projet généré, pas dans le
# dépôt framework. On ne les vérifie pas.
_USER_ROOTS = frozenset({"mvc", "config", "optins", "app", "wsgi", "conftest", "tests"})

_CODE_BLOCK = re.compile(r"```python\n(.*?)```", re.DOTALL)


def _root(module: str) -> str:
    return module.split(".")[0]


def _is_framework(module: str) -> bool:
    if module.startswith("forge_mvc_"):
        return True
    return _root(module) in {"core", "cli", "forge", "integrations"}


def _is_user(module: str) -> bool:
    return _root(module) in _USER_ROOTS


def _iter_imports(code: str):
    """(module, [noms]) pour chaque import d'un bloc, robuste aux snippets."""
    trees: list[ast.AST] = []
    try:
        trees.append(ast.parse(code))
    except SyntaxError:
        for line in code.splitlines():
            stripped = line.strip()
            if stripped.startswith(("import ", "from ")):
                try:
                    trees.append(ast.parse(stripped))
                except SyntaxError:
                    pass
    for tree in trees:
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    yield alias.name, []
            elif isinstance(node, ast.ImportFrom):
                if node.level or node.module is None:
                    continue
                yield node.module, [a.name for a in node.names]


def _check(module: str, names: list[str], where: str, failures: list[str]) -> None:
    if _is_user(module) or not _is_framework(module):
        return
    try:
        mod = importlib.import_module(module)
    except Exception as exc:  # noqa: BLE001
        failures.append(f"{where}: import `{module}` échoue ({type(exc).__name__}: {exc})")
        return
    for name in names:
        if name == "*":
            continue
        if hasattr(mod, name):
            continue
        try:
            importlib.import_module(f"{module}.{name}")
        except Exception:  # noqa: BLE001
            failures.append(f"{where}: `{module}` n'a pas le symbole `{name}`")


def _doc_files() -> list[Path]:
    files: list[Path] = []
    for pattern in _DOC_GLOBS:
        files.extend(PROJECT_ROOT.glob(pattern))
    return sorted(files)


def test_embedded_docs_imports_resolvent():
    failures: list[str] = []
    md_files = _doc_files()
    assert md_files, "Aucune doc embarquée trouvée (core/cli/packages */docs)."
    for md in md_files:
        where = str(md.relative_to(PROJECT_ROOT))
        for block in _CODE_BLOCK.findall(md.read_text(encoding="utf-8")):
            for module, names in _iter_imports(block):
                _check(module, names, where, failures)
    assert not failures, (
        "Imports cœur/cli/opt-in invalides dans des docs embarquées "
        f"({len(failures)}) :\n" + "\n".join(f"  - {f}" for f in failures)
    )
