"""Garde-fou IMAGES-TYPING-STRICT-GUARD-001 : forge-mvc-images reste strict + typé.

Deuxième opt-in passé en pyright strict (suite du cliquet ADR-036, après le
cœur et ``forge-mvc-files``). Ce test verrouille deux acquis :

1. tout fichier ``.py`` **non vide** du paquet porte le marqueur
   ``# pyright: strict`` ;
2. le paquet expose ``py.typed`` (PEP 561).

But : empêcher une régression silencieuse — un nouveau module ajouté sans
marqueur, ou la disparition de ``py.typed``, fait échouer ce test.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_images")

import forge_mvc_images

PKG_ROOT = Path(forge_mvc_images.__file__).resolve().parent
MARKER = "# pyright: strict"


def _has_code(text: str) -> bool:
    """Vrai si le fichier contient au moins une ligne non vide."""
    return any(line.strip() for line in text.splitlines())


def test_tout_forge_mvc_images_est_pyright_strict():
    missing: list[str] = []
    for path in sorted(PKG_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        if not _has_code(text):
            continue
        if MARKER not in text:
            missing.append(path.relative_to(PKG_ROOT).as_posix())

    assert missing == [], (
        f"Fichiers de forge_mvc_images/ sans `{MARKER}` : {missing}. "
        "Tout module du paquet doit être strict (cliquet typage opt-ins)."
    )


def test_forge_mvc_images_expose_py_typed():
    marker = PKG_ROOT / "py.typed"
    assert marker.exists(), (
        "forge_mvc_images/py.typed attendu (PEP 561) : sans lui, le paquet est "
        "vu comme non typé par pyright/mypy même installé."
    )
