#!/usr/bin/env bash
# scripts/dev-server.sh — Lanceur du serveur de développement Forge.
#
# Vérifie le port avant de lancer `python app.py`, affiche l'URL à ouvrir,
# rappelle le protocole (HTTP/HTTPS) et l'effet d'APP_HOST=0.0.0.0.
# Ne tue jamais de processus existant.
#
# Ticket : DEV-SERVER-SCRIPT-001
set -euo pipefail

# ── Positionnement à la racine du dépôt ───────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# ── Helpers d'affichage ───────────────────────────────────────────────────────

_log() { printf "[DEV-SERVER] %s\n" "$*"; }
_err() { printf "[DEV-SERVER] %s\n" "$*" >&2; }

# ── Lecture d'une variable depuis un fichier env style dotenv ────────────────

# Ne touche pas à l'environnement courant : extrait juste la valeur trouvée.
# Ignore les lignes commentées (# au début) et les valeurs vides.
_read_env_var() {
    local name="$1"
    local default_value="$2"
    local env_file="$3"
    if [ -f "$env_file" ]; then
        local value
        value=$(grep -E "^[[:space:]]*${name}=" "$env_file" 2>/dev/null \
                | head -n1 \
                | sed -e "s/^[[:space:]]*${name}=//" -e 's/[[:space:]]*$//' \
                || true)
        if [ -n "$value" ]; then
            printf "%s" "$value"
            return
        fi
    fi
    printf "%s" "$default_value"
}

# Normalise un booléen façon python-dotenv Forge : {1,true,yes,on} → true.
_to_bool() {
    local raw="$1"
    local lower
    lower=$(printf "%s" "$raw" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')
    case "$lower" in
        1|true|yes|on) printf "true" ;;
        *)             printf "false" ;;
    esac
}

# ── Garde-fou racine de projet ────────────────────────────────────────────────

if [ ! -f "app.py" ]; then
    _err "ERREUR : app.py introuvable à la racine ($REPO_ROOT)."
    _err "Ce script doit être exécuté depuis un projet Forge."
    exit 1
fi

_log "Projet Forge détecté."

# ── Lecture de la configuration ──────────────────────────────────────────────

# Le défaut SSL « true » reproduit le comportement de config.py en mode dev.
APP_HOST_VALUE=$(_read_env_var "APP_HOST" "127.0.0.1" "env/dev")
APP_PORT_VALUE=$(_read_env_var "APP_PORT" "8000" "env/dev")
APP_SSL_RAW=$(_read_env_var "APP_SSL_ENABLED" "true" "env/dev")
APP_SSL_ENABLED_VALUE=$(_to_bool "$APP_SSL_RAW")

if [ "$APP_SSL_ENABLED_VALUE" = "true" ]; then
    SCHEME="https"
else
    SCHEME="http"
fi

_log "Configuration :"
_log "  APP_HOST=$APP_HOST_VALUE"
_log "  APP_PORT=$APP_PORT_VALUE"
_log "  APP_SSL_ENABLED=$APP_SSL_ENABLED_VALUE"
printf "\n"

# ── Détection du port occupé ─────────────────────────────────────────────────

PROCESS_INFO=""
PORT_OCCUPIED="false"

if command -v ss >/dev/null 2>&1; then
    SS_OUT=$(ss -tulpn 2>/dev/null | grep -E "[:.]${APP_PORT_VALUE}\b" || true)
    if [ -n "$SS_OUT" ]; then
        PORT_OCCUPIED="true"
        PROCESS_INFO="$SS_OUT"
    fi
fi

if [ "$PORT_OCCUPIED" = "false" ] && command -v lsof >/dev/null 2>&1; then
    LSOF_OUT=$(lsof -iTCP:"$APP_PORT_VALUE" -sTCP:LISTEN -P 2>/dev/null || true)
    if [ -n "$LSOF_OUT" ]; then
        PORT_OCCUPIED="true"
        PROCESS_INFO="$LSOF_OUT"
    fi
fi

if ! command -v ss >/dev/null 2>&1 && ! command -v lsof >/dev/null 2>&1; then
    _err "Ni ss ni lsof ne sont disponibles ; impossible de vérifier le port."
    _err "Installez iproute2 (ss) ou lsof, puis relancez."
    exit 1
fi

# ── Cas 2 : port occupé ──────────────────────────────────────────────────────

if [ "$PORT_OCCUPIED" = "true" ]; then
    _err "ERREUR : le port $APP_PORT_VALUE est déjà utilisé."
    printf "\n"
    printf "Processus détecté :\n"
    printf "%s\n" "$PROCESS_INFO"
    printf "\n"
    printf "Commandes utiles :\n"
    printf "  ss -tulpn | grep :%s\n" "$APP_PORT_VALUE"
    printf "  lsof -i :%s\n" "$APP_PORT_VALUE"
    printf "\n"
    printf "Solutions possibles :\n"
    printf "  - arrêter l'ancien serveur Forge ;\n"
    printf "  - changer APP_PORT dans env/dev ;\n"
    printf "  - relancer scripts/dev-server.sh.\n"
    printf "\n"
    printf "Aucun serveur Forge n'a été démarré.\n"
    exit 1
fi

# ── Cas 1 : port libre ───────────────────────────────────────────────────────

_log "Port $APP_PORT_VALUE libre."
printf "\n"

if [ "$APP_HOST_VALUE" = "0.0.0.0" ]; then
    LOCAL_HOST="127.0.0.1"
else
    LOCAL_HOST="$APP_HOST_VALUE"
fi

_log "URL locale :"
_log "  ${SCHEME}://${LOCAL_HOST}:${APP_PORT_VALUE}"
printf "\n"

if [ "$APP_HOST_VALUE" = "0.0.0.0" ]; then
    _log "Accès depuis une autre machine du réseau :"
    _log "  utilisez l'IP réelle de cette machine, par exemple :"
    _log "  ${SCHEME}://<IP_MACHINE>:${APP_PORT_VALUE}"
    printf "\n"
    _log "Rappel : 0.0.0.0 signifie écoute sur toutes les interfaces."
fi

if [ "$APP_SSL_ENABLED_VALUE" = "true" ]; then
    _log "Rappel : HTTPS est activé, utilisez https://."
fi

printf "\n"
_log "Lancement :"
_log "  python app.py"
printf "\n"

exec python app.py
