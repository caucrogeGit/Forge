"""Garde-fou — CORE-MVC-VALIDATOR-REMOVE-001 : la classe Validator legacy est retirée.

`core/mvc/model/validator.py` portait une classe `Validator` chaînée
(`required`/`max_length`/`add_error`), supplantée par `core/forms` (Form/Field)
et par la validation générée du moteur d'entités (`core/validation`). Elle
n'avait aucun consommateur de production (seul son propre test l'importait).
Retrait pré-1.0, sans alias déprécié (convention pré-1.0). Ce garde interdit sa
réapparition silencieuse.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent


def test_validator_module_absent():
    assert not (PROJECT_ROOT / "core" / "mvc" / "model" / "validator.py").exists(), (
        "core/mvc/model/validator.py doit rester supprimé (CORE-MVC-VALIDATOR-REMOVE-001)."
    )


def test_validator_non_importable():
    import importlib

    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("core.mvc.model.validator")


def test_aucune_reference_au_module_validator():
    # Aucune source ne doit réimporter le module retiré.
    offenders: list[str] = []
    for root in ("core", "cli", "integrations", "packages", "skeleton"):
        base = PROJECT_ROOT / root
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if "__pycache__" in path.parts or "/build/" in path.as_posix():
                continue
            text = path.read_text(encoding="utf-8")
            if "core.mvc.model.validator" in text or "from core.mvc.model import validator" in text:
                offenders.append(str(path.relative_to(PROJECT_ROOT)))
    assert not offenders, f"Références résiduelles au module validator retiré : {offenders}"
