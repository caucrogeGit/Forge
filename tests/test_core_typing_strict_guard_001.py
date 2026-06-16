"""Garde-fou CORE-TYPING-STRICT-GUARD-001 : le cœur reste en pyright strict.

Le cliquet ADR-036 a fait passer l'intégralité de ``core/`` en
``# pyright: strict`` (12 paquets, ``pyright core/`` à 0 erreur). Ce test
verrouille l'acquis : tout fichier ``.py`` **non vide** de ``core/`` doit porter
le marqueur, à la seule exception documentée de ``core/http/debug_dumper.py``
(introspection d'objets arbitraires, ``Any`` par nature).

But : empêcher une régression silencieuse — un nouveau fichier du cœur ajouté
sans marqueur, ou la disparition de l'exemption, fait échouer ce test.
"""
from __future__ import annotations

from pathlib import Path

import core

CORE_ROOT = Path(core.__file__).resolve().parent
MARKER = "# pyright: strict"

# Seule exemption : introspection d'objets arbitraires, hors strict à dessein.
EXEMPT = {"http/debug_dumper.py"}


def _has_code(text: str) -> bool:
    """Vrai si le fichier contient au moins une ligne non vide.

    Les ``__init__.py`` vides (re-exports absents) n'ont pas besoin du marqueur.
    """
    return any(line.strip() for line in text.splitlines())


def test_tout_le_coeur_non_vide_est_pyright_strict():
    missing: list[str] = []
    for path in sorted(CORE_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        if not _has_code(text):
            continue
        if MARKER not in text:
            missing.append(path.relative_to(CORE_ROOT).as_posix())

    assert missing == sorted(EXEMPT), (
        f"Fichiers de core/ sans `{MARKER}` : {missing} "
        f"(attendu exactement : {sorted(EXEMPT)}). "
        "Tout nouveau fichier du cœur doit être strict (cliquet ADR-036)."
    )


def test_exemption_debug_dumper_reste_volontaire():
    """``debug_dumper.py`` est volontairement hors strict : il doit exister et
    ne PAS porter le marqueur, sinon l'exemption n'a plus de raison d'être."""
    dumper = CORE_ROOT / "http" / "debug_dumper.py"
    assert dumper.exists(), "core/http/debug_dumper.py attendu (exemption du cliquet)."
    assert MARKER not in dumper.read_text(encoding="utf-8"), (
        "debug_dumper.py porte le marqueur strict : soit le rendre strict et le "
        "retirer de EXEMPT, soit retirer le marqueur."
    )
