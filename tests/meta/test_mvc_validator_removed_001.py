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
    # Aucune source NI DOC ne doit référencer le module retiré. On balaie les
    # .py mais aussi les .md/.yml : une doc embarquée qui importe le module
    # supprimé casse test_embedded_docs_imports_001 et mkdocs --strict (leçon de
    # ce ticket — un retrait n'est complet que quand ses docs le sont).
    offenders: list[str] = []
    needles = ("core.mvc.model.validator", "from core.mvc.model import validator", "model/validator.py")
    for root in ("core", "cli", "integrations", "packages", "skeleton", "docs"):
        base = PROJECT_ROOT / root
        if not base.exists():
            continue
        for pattern in ("*.py", "*.md", "*.yml"):
            for path in base.rglob(pattern):
                if "__pycache__" in path.parts or "/build/" in path.as_posix():
                    continue
                text = path.read_text(encoding="utf-8", errors="replace")
                if any(needle in text for needle in needles):
                    offenders.append(str(path.relative_to(PROJECT_ROOT)))
    assert not offenders, f"Références résiduelles au module validator retiré : {offenders}"
