"""Garde-fou TEST-META-CORE-NO-OPTIN-IMPORT-001.

Le cœur (`core/`) ne doit JAMAIS importer un paquet opt-in `forge_mvc_*` : la
dépendance va toujours de l'opt-in vers le cœur, jamais l'inverse (ADR-004,
ADR-019/021/022/027, principe 8). Le découplage était jusqu'ici verrouillé
seulement par des tests ponctuels (sur `audit.py`, `doctor.py`). Ce garde-fou
le verrouille **globalement** : il balaie tout `core/**/*.py` et refuse le
moindre `import forge_mvc_` / `from forge_mvc_`.

Test documentaire : il lit le code source, il n'exécute aucun service.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
CORE_DIR = PROJECT_ROOT / "core"

# Capture `import forge_mvc_x` et `from forge_mvc_x import ...` en début de ligne
# (après une éventuelle indentation), y compris les imports différés en fonction.
_OPTIN_IMPORT = re.compile(r"^\s*(?:import|from)\s+forge_mvc_\w+", re.MULTILINE)


def _core_py_files() -> list[Path]:
    return sorted(CORE_DIR.rglob("*.py"))


def test_core_has_python_files() -> None:
    """Le périmètre balayé n'est pas vide (sinon le garde-fou ne protège rien)."""
    assert _core_py_files(), "Aucun fichier .py trouvé sous core/"


@pytest.mark.parametrize(
    "module",
    _core_py_files(),
    ids=lambda p: str(p.relative_to(PROJECT_ROOT)),
)
def test_core_module_has_no_optin_import(module: Path) -> None:
    offending = [
        line.strip()
        for line in _OPTIN_IMPORT.findall(module.read_text(encoding="utf-8"))
    ]
    assert not offending, (
        f"{module.relative_to(PROJECT_ROOT)} importe un paquet opt-in "
        "(`forge_mvc_*`), ce qui inverse la dépendance cœur/opt-in (ADR-004, "
        f"principe 8). Imports fautifs : {offending}"
    )
