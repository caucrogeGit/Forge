#!/usr/bin/env bash
# forge-write-if-new.sh — Hook PreToolUse Forge
# §4 — Préserver le code utilisateur (write-if-new : starters, examples)
# §9 — Pas d'écriture invisible dans le code utilisateur (fichiers structurants)
#
# Exit 0  → autoriser l'outil
# Exit 2  → bloquer l'outil (message stderr visible par Claude Code)

set -uo pipefail

# ── Lecture du payload stdin ──────────────────────────────────────────────────

PAYLOAD=$(cat)
FILE_PATH=$(printf '%s' "$PAYLOAD" | jq -r '.tool_input.file_path // empty' 2>/dev/null || true)

# Outil sans file_path (ex. Bash, Read) → pas de vérification à faire
[[ -z "${FILE_PATH:-}" ]] && exit 0

# ── Règle 1 — write-if-new : fichier inexistant → toujours autorisé ──────────

[[ ! -e "$FILE_PATH" ]] && exit 0

# ── Règle 2 — fichier régénérable (_base.py) → toujours autorisé ─────────────

BASENAME=$(basename "$FILE_PATH")
[[ "$BASENAME" == *_base.py ]] && exit 0

# ── Calcul du chemin relatif depuis la racine du dépôt ───────────────────────

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo "")
if [[ -n "$REPO_ROOT" && "$FILE_PATH" == "$REPO_ROOT/"* ]]; then
  REL_PATH="${FILE_PATH#"$REPO_ROOT/"}"
else
  REL_PATH="$FILE_PATH"
fi

# ── Fonctions de blocage ──────────────────────────────────────────────────────

block_structural() {
  echo "FORGE §9 — fichier structurant protégé : '$REL_PATH'" >&2
  echo "Règle : charte Forge v2 §9 « Pas d'écriture invisible dans le code utilisateur »." >&2
  echo "Action : proposer la modification à l'humain ou créer un ticket dédié." >&2
  exit 2
}

block_user_zone() {
  echo "FORGE §4 — write-if-new : '$REL_PATH' existe déjà dans la zone code-utilisateur." >&2
  echo "Règle : charte Forge v2 §4 « Préserver le code utilisateur »." >&2
  echo "Action : créer un nouveau fichier ou proposer la modification à l'humain." >&2
  exit 2
}

# ── Règle 3 — toujours bloqué : fichiers structurants du dépôt ───────────────

case "$REL_PATH" in
  "charte_philosophique_forge_v2.md"|\
  "CLAUDE.md"|\
  ".claude/settings.json"|\
  ".claude/hooks/"*|\
  "pyproject.toml"|\
  "CHANGELOG.md"|\
  ".env"|".env."*|\
  *"/.env"|*"/.env."*)
    block_structural
    ;;
esac

# ── Règle 4 — bloqué dans la zone code-utilisateur (starters, examples) ──────

case "$REL_PATH" in
  "starters/"*|"examples/"*)
    block_user_zone
    ;;
esac

# ── Règle 5 — autorisation par défaut ────────────────────────────────────────

exit 0
