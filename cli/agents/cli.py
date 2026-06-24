"""Commande `forge agents:init` — guidance agent IA d'une application (ADR-047).

- sans option : génère la couche guidance (`CLAUDE.md`, `AGENTS.md`, ADR-001) en
  write-if-new (ne réécrit rien d'existant) ;
- `--force` : rafraîchit `CLAUDE.md` et `AGENTS.md` depuis la référence de la
  version de Forge installée, sans toucher l'ADR-001 (propriété du projet) ;
- `--check` : diagnostic en lecture seule (fichiers absents ou briefing divergé).
"""
from __future__ import annotations

from pathlib import Path

from cli.agents.briefing import render_app_briefing
from cli.agents.emit import emit_app_agent_files

__all__ = ["main"]

_BRIEFING_FILES = ("CLAUDE.md", "AGENTS.md")
_SEED_ADR = "docs/adr/001-adopter-forge.md"


def _check(root: Path) -> int:
    briefing = render_app_briefing()
    problems: list[str] = []
    for name in _BRIEFING_FILES:
        path = root / name
        if not path.exists():
            problems.append(f"{name} absent")
        elif path.read_text(encoding="utf-8") != briefing:
            problems.append(f"{name} a divergé de la référence Forge installée")
    if not (root / _SEED_ADR).exists():
        problems.append(f"{_SEED_ADR} absent")
    if problems:
        for problem in problems:
            print(f"[WARN] {problem}")
        print()
        print("Conseil : forge agents:init (créer) ou forge agents:init --force (rafraîchir le briefing).")
        return 1
    print("[OK] guidance agent à jour.")
    return 0


def _force(root: Path) -> int:
    briefing = render_app_briefing()
    for name in _BRIEFING_FILES:
        (root / name).write_text(briefing, encoding="utf-8")
        print(f"[OK] {name} rafraîchi.")
    for name in emit_app_agent_files(root):
        if name not in _BRIEFING_FILES:
            print(f"[OK] créé : {name}")
    print()
    print(f"Note : {_SEED_ADR} n'est jamais écrasé (il appartient au projet).")
    return 0


def _init(root: Path) -> int:
    created = emit_app_agent_files(root)
    if created:
        for name in created:
            print(f"[OK] créé : {name}")
    else:
        print("[OK] guidance déjà présente (rien à créer).")
    return 0


def main(args: list[str] | None = None) -> int:
    """Point d'entrée appelé par `forge.py` pour `forge agents:init`."""
    args = args or []
    root = Path.cwd()
    if "--check" in args:
        return _check(root)
    if "--force" in args:
        return _force(root)
    return _init(root)
