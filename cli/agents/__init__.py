# pyright: strict
"""Guidance agent IA pour les applications Forge (ADR-047).

Ce sous-paquet porte le briefing canonique distillé de l'expérience Forge,
destiné aux agents IA (Claude Code, Codex) qui travaillent sur une **application**
générée par `forge new` — pas sur le framework lui-même.

`forge new` écrit ce briefing en `CLAUDE.md` et `AGENTS.md` (write-if-new), et
`forge agents:init` le (re)génère depuis la version installée.
"""
from cli.agents.briefing import render_app_briefing
from cli.agents.emit import emit_app_agent_files
from cli.agents.seed_adr import render_seed_adr
from cli.agents.settings import render_app_settings

__all__ = [
    "render_app_briefing",
    "render_seed_adr",
    "render_app_settings",
    "emit_app_agent_files",
]
