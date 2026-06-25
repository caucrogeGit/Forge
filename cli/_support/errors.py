# pyright: strict
"""Helpers standardisés pour les erreurs CLI Forge.

Convention :
    Erreur : <message>
    Conseil : <suggestion>   (optionnel)

Les erreurs CLI vont sur stderr.
Le code de sortie est 1 par défaut (erreur utilisateur).
"""

from __future__ import annotations

import sys
from typing import NoReturn


def cli_error(message: str, hint: str = "") -> None:
    """Affiche une erreur CLI sur stderr sans terminer le processus."""
    print(f"Erreur : {message}", file=sys.stderr)
    if hint:
        print(f"Conseil : {hint}", file=sys.stderr)


def cli_fail(message: str, hint: str = "", code: int = 1) -> NoReturn:
    """Affiche une erreur CLI sur stderr et termine le processus."""
    cli_error(message, hint)
    sys.exit(code)
