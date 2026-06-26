"""Garde-fou SETTINGS-TYPING-STRICT-GUARD-001 : forge-mvc-settings strict + typé.

Verrouille deux acquis du cliquet de typage (ADR-036) :
1. tout fichier `.py` non vide du paquet porte le marqueur `# pyright: strict` ;
2. le paquet expose `py.typed` (PEP 561).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_settings")
import forge_mvc_settings  # noqa: E402

PKG_ROOT = Path(forge_mvc_settings.__file__).resolve().parent
MARKER = "# pyright: strict"


def _has_code(text: str) -> bool:
    return any(line.strip() for line in text.splitlines())


def test_tout_forge_mvc_settings_est_pyright_strict() -> None:
    missing: list[str] = []
    for path in sorted(PKG_ROOT.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        if _has_code(text) and MARKER not in text:
            missing.append(path.name)
    assert not missing, f"fichiers sans '{MARKER}' : {missing}"


def test_py_typed_present() -> None:
    assert (PKG_ROOT / "py.typed").is_file(), "forge_mvc_settings doit embarquer py.typed (PEP 561)"
