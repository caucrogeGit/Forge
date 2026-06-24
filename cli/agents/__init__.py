"""Guidance agent IA pour les applications Forge (ADR-047).

Ce sous-paquet porte le briefing canonique distillé de l'expérience Forge,
destiné aux agents IA (Claude Code, Codex) qui travaillent sur une **application**
générée par `forge new` — pas sur le framework lui-même.

`forge new` écrit ce briefing en `CLAUDE.md` et `AGENTS.md` (write-if-new), et
`forge agents:init` le (re)génère depuis la version installée.
"""
from cli.agents.briefing import render_app_briefing

__all__ = ["render_app_briefing"]
