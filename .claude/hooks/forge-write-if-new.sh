#!/usr/bin/env bash
# forge-write-if-new.sh — Hook PreToolUse Forge
# §4 — Préserver le code utilisateur (write-if-new : starters, examples)
# §9 — Pas d'écriture invisible dans le code utilisateur (fichiers structurants)
#
# Exit 0  → autoriser l'outil
# Exit 2  → bloquer l'outil (message stderr visible par Claude Code)

set -uo pipefail

# ── Lecture du payload stdin ──────────────────────────────────────────────────
#
# Le hook DOIT être fail-closed (HOOK-JQ-FALLBACK-001) : si l'on ne peut
# pas extraire le chemin cible du JSON envoyé par PreToolUse, on REFUSE
# l'écriture plutôt que de l'autoriser silencieusement.
#
# Stratégie d'extraction :
#   1. tenter `jq` (rapide, standard sur les machines CI Forge) ;
#   2. retomber sur `python3` (toujours présent — exigence ADR-006
#      Python 3.12+) si `jq` est absent ;
#   3. si ni `jq` ni `python3` ne sont disponibles, ou si le JSON est
#      invalide, exit 2 (fail-closed).
#
# La distinction `FILE_PATH vide après parsing OK` (cas légitime
# Bash/Read sans file_path) vs `parser en échec` est portée par le RC
# de la fonction.

extract_file_path() {
  local payload="$1"

  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$payload" | jq -r '.tool_input.file_path // empty'
    return $?
  fi

  if command -v python3 >/dev/null 2>&1; then
    # Passer le payload via argv[1] (pas via stdin) pour éviter tout
    # conflit avec un heredoc / pipe et garder un parsing robuste de
    # la chaîne complète, espaces et quotes inclus.
    python3 -c '
import json
import sys

try:
    data = json.loads(sys.argv[1])
except Exception:
    sys.exit(1)

value = ""
if isinstance(data, dict):
    tool_input = data.get("tool_input")
    if isinstance(tool_input, dict):
        candidate = tool_input.get("file_path")
        if isinstance(candidate, str):
            value = candidate

sys.stdout.write(value)
' "$payload"
    return $?
  fi

  # Ni jq ni python3 disponibles : impossible de parser sans risque.
  return 127
}

PAYLOAD=$(cat)
PARSER_OUTPUT=$(extract_file_path "$PAYLOAD")
PARSER_RC=$?

if (( PARSER_RC != 0 )); then
  echo "[forge-hook] Impossible de lire le fichier cible depuis l'entrée PreToolUse." >&2
  if (( PARSER_RC == 127 )); then
    echo "[forge-hook] Ni 'jq' ni 'python3' disponibles pour parser le JSON." >&2
  else
    echo "[forge-hook] Payload JSON invalide ou parser en échec (RC=$PARSER_RC)." >&2
  fi
  echo "[forge-hook] Écriture refusée par sécurité (fail-closed)." >&2
  exit 2
fi

FILE_PATH="$PARSER_OUTPUT"

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
#
# Note (AGENTS-CHANGELOG-WRITE-ALLOW-001) : CHANGELOG.md a été retiré
# de cette liste. C'est un fichier projet normal qui fait partie du
# flux normal de release et d'audit Forge, et il doit pouvoir être mis
# à jour par les agents (Claude Code, Codex, etc.) lorsqu'un ticket
# le demande explicitement.
#
# Note (HOOK-CLAUDE-MD-UNBLOCK-001) : CLAUDE.md a été retiré de cette
# liste. Le briefing agent fait partie du flux normal de resync et de
# gouvernance Forge, et les agents doivent pouvoir le mettre à jour
# lorsqu'un ticket le demande explicitement. Les autres entrées
# (charte, settings du hook, pyproject racine, fichiers .env) restent
# protégées.

case "$REL_PATH" in
  "CHARTE_DOC.md"|\
  ".claude/settings.json"|\
  ".claude/hooks/"*|\
  "pyproject.toml"|\
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
