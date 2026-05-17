"""Garde-fou DOCS-SYMBOL-VALIDATION-001.

Vérifie que chaque bloc ```python``` dans la doc utilisateur active :
1. importe depuis des modules qui existent
2. les symboles cités existent réellement dans ces modules

Différence avec test_docs_no_phantom_modules_001 :
- Le test phantom vérifie le NOM du module (blacklist regex)
- Ce test vérifie chaque SYMBOLE par introspection (importlib + hasattr)

Whitelist : si un bloc importe depuis un module opt-in
(forge_mvc_mfa, forge_mvc_rbac, forge_mvc_workflow, forge_mvc_stats)
et que ce module n'est pas installé, le bloc est ignoré (équivalent
pytest.importorskip implicite). Cela permet de faire passer le test
en environnement core-only.
"""
from __future__ import annotations

import importlib
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"

EXCLUDED_DIRS: set[str] = {"history", "audits"}
EXCLUDED_FILES: set[Path] = set()

# Modules opt-in : leur ABSENCE est tolérée, mais s'ils sont installés,
# leurs symboles sont vérifiés normalement.
OPTIONAL_MODULES = {
    "forge_mvc_mfa",
    "forge_mvc_rbac",
    "forge_mvc_workflow",
    "forge_mvc_stats",
    "forge_mvc_media",
}

# Modules applicatifs : toute vérification est ignorée (import + symboles).
# Leur contenu est généré par les starters et absent du repo framework.
SKIP_ALL_MODULES = {"mvc", "modules"}


def _active_md_files() -> list[Path]:
    files: list[Path] = []
    for md in DOCS_DIR.rglob("*.md"):
        if any(part in EXCLUDED_DIRS for part in md.parts):
            continue
        if md in EXCLUDED_FILES:
            continue
        files.append(md)
    return sorted(files)


def _python_blocks(text: str) -> list[tuple[int, str]]:
    """Retourne [(numéro_ligne_début, contenu_du_bloc), ...]."""
    blocks = []
    pattern = re.compile(r"```python\s*\n(.*?)```", re.DOTALL)
    for m in pattern.finditer(text):
        line_no = text[:m.start()].count("\n") + 1
        blocks.append((line_no, m.group(1)))
    return blocks


def _extract_imports(block: str) -> list[tuple[str, list[str]]]:
    """Extrait les imports d'un bloc python.

    Retourne [(module, [symbole1, symbole2, ...]), ...] :
    - pour `from X import a, b` : (X, [a, b])
    - pour `import X` : (X, [])

    Gère :
    - les imports multilignes entre parenthèses avec commentaires inline
    - les alias `import X as Y` (on garde le nom original)
    """
    results = []
    # Étape 1 : supprimer les commentaires inline (# ...) et les lignes vides
    clean_lines = []
    for line in block.split("\n"):
        code_part = line.split("#")[0].strip()
        if code_part:
            clean_lines.append(code_part)
    clean_block = "\n".join(clean_lines)

    # Étape 2 : normaliser les imports multilignes en parenthèses
    clean_block = re.sub(
        r"\(([^)]*)\)",
        lambda m: "(" + m.group(1).replace("\n", " ") + ")",
        clean_block,
    )
    for line in clean_block.split("\n"):
        line = line.strip()
        if not line:
            continue
        # from X import a, b, c
        m = re.match(r"^from\s+([\w.]+)\s+import\s+(.+)$", line)
        if m:
            mod = m.group(1)
            symbols_raw = m.group(2).rstrip("\\").strip()
            symbols = []
            for s in symbols_raw.replace("(", "").replace(")", "").split(","):
                s = s.strip()
                if not s:
                    continue
                # gère "X as Y" : on vérifie X
                name = s.split(" as ")[0].strip()
                if name and name != "*":
                    symbols.append(name)
            results.append((mod, symbols))
            continue
        # import X
        m = re.match(r"^import\s+([\w.]+)", line)
        if m:
            results.append((m.group(1), []))
    return results


class TestPythonExamplesExecutable:
    """Chaque bloc python de doc active doit être exécutable."""

    def test_at_least_some_python_blocks_found(self):
        total = sum(
            len(_python_blocks(md.read_text(encoding="utf-8")))
            for md in _active_md_files()
        )
        assert total >= 50, (
            f"Trop peu de blocs python détectés ({total}). "
            "Vérifier le regex et EXCLUDED_DIRS."
        )

    def test_all_imports_resolve(self):
        offenders: list[str] = []

        for md_path in _active_md_files():
            text = md_path.read_text(encoding="utf-8")
            for line_no, block in _python_blocks(text):
                for module, symbols in _extract_imports(block):
                    # Ignore les imports relatifs (spécifiques au projet applicatif)
                    if module.startswith("."):
                        continue
                    # Ignore les modules applicatifs générés (mvc.*, modules.*)
                    if module.split(".")[0] in SKIP_ALL_MODULES:
                        continue
                    # Tente l'import du module
                    try:
                        mod = importlib.import_module(module)
                    except ImportError:
                        # Module opt-in absent : tolérer
                        if module.split(".")[0] in OPTIONAL_MODULES:
                            continue
                        offenders.append(
                            f"{md_path.relative_to(PROJECT_ROOT)}:{line_no} "
                            f"→ module '{module}' introuvable"
                        )
                        continue
                    # Vérifie chaque symbole
                    for sym in symbols:
                        if not hasattr(mod, sym):
                            offenders.append(
                                f"{md_path.relative_to(PROJECT_ROOT)}:{line_no} "
                                f"→ `from {module} import {sym}` "
                                f"mais '{sym}' n'existe pas dans {module}"
                            )

        if offenders:
            raise AssertionError(
                f"{len(offenders)} import(s) doc cassé(s) :\n"
                + "\n".join(f"  - {o}" for o in offenders)
                + "\n\nCorriger ces imports ou les modules cités."
            )
