"""Réglages Claude Code optionnels pour une application Forge (ADR-047).

`.claude/settings.json` pré-autorise les commandes usuelles du développement
Forge (forge, pytest, ruff, mkdocs, git en lecture) et refuse les commandes
destructrices. Volontairement minimal : seulement des permissions, pas de
`defaultMode` ni de hooks (on ne change pas le comportement d'édition de
l'utilisateur, on évite seulement des invites répétitives).

Opt-in : généré uniquement via `forge agents:init --settings`, jamais par
`forge new` par défaut (pré-autoriser des commandes est un choix de sécurité).
"""
from __future__ import annotations

import json

APP_CLAUDE_SETTINGS = {
    "permissions": {
        "allow": [
            "Bash(forge:*)",
            "Bash(pytest)",
            "Bash(pytest:*)",
            "Bash(python -m pytest:*)",
            "Bash(python -m compileall:*)",
            "Bash(ruff check:*)",
            "Bash(ruff format:*)",
            "Bash(mkdocs build:*)",
            "Bash(mkdocs serve:*)",
            "Bash(git status)",
            "Bash(git status:*)",
            "Bash(git diff:*)",
            "Bash(git log:*)",
            "Bash(git show:*)",
            "Bash(git branch:*)",
            "Bash(git add:*)",
        ],
        "deny": [
            "Bash(git push --force:*)",
            "Bash(git push -f:*)",
            "Bash(git reset --hard:*)",
            "Bash(git tag -d:*)",
            "Bash(git push --delete:*)",
            "Bash(rm -rf:*)",
            "Bash(rm -fr:*)",
        ],
    },
}


def render_app_settings() -> str:
    """Retourne le contenu JSON de `.claude/settings.json` pour une app Forge."""
    return json.dumps(APP_CLAUDE_SETTINGS, indent=2, ensure_ascii=False) + "\n"
