"""Émission des fichiers de guidance agent dans une application Forge (ADR-047).

Écrit `CLAUDE.md`, `AGENTS.md` (même briefing) et `docs/adr/001-adopter-forge.md`
en write-if-new : un fichier déjà présent n'est jamais écrasé (charte principe 9).
Utilisé par `forge new` et par `forge agents:init`.
"""
from __future__ import annotations

from datetime import date as _date
from pathlib import Path

from cli.agents.briefing import render_app_briefing
from cli.agents.seed_adr import render_seed_adr
from cli.agents.settings import render_app_settings

__all__ = ["emit_app_agent_files"]


def _write_if_new(path: Path, content: str, created: list[str], root: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    created.append(path.relative_to(root).as_posix())


def emit_app_agent_files(
    project_root: Path,
    *,
    date: str | None = None,
    with_settings: bool = False,
) -> list[str]:
    """Écrit la couche guidance agent dans `project_root` (write-if-new).

    Fichiers : `CLAUDE.md`, `AGENTS.md`, `docs/adr/001-adopter-forge.md`, et,
    si `with_settings`, `.claude/settings.json` (commandes pré-autorisées).
    `date` (ISO) tamponne l'ADR-001 ; par défaut, la date du jour.
    Retourne la liste des chemins créés (relatifs au projet) ; un fichier déjà
    présent n'est pas listé (ni écrasé).
    """
    stamp = date or _date.today().isoformat()
    briefing = render_app_briefing()
    created: list[str] = []
    _write_if_new(project_root / "CLAUDE.md", briefing, created, project_root)
    _write_if_new(project_root / "AGENTS.md", briefing, created, project_root)
    _write_if_new(
        project_root / "docs" / "adr" / "001-adopter-forge.md",
        render_seed_adr(date=stamp),
        created,
        project_root,
    )
    if with_settings:
        _write_if_new(
            project_root / ".claude" / "settings.json",
            render_app_settings(),
            created,
            project_root,
        )
    return created
