#!/usr/bin/env bash
# SMOKE-INSTALL-VIERGE-001 — Preuve d'installation en environnement vierge.
#
# Prouve que le parcours réel d'un nouvel utilisateur aboutit :
#
#     forge new <projet>  ->  pip install -r requirements.txt  ->  forge utilisable
#
# Les paquets Forge sont résolus depuis des WHEELS CONSTRUITES LOCALEMENT
# (--find-links sur un wheelhouse temporaire), donc le smoke est INDÉPENDANT
# de la publication PyPI des paquets Forge. C'est le garde-fou qui aurait
# attrapé l'absence de forge-mvc-mariadb sur PyPI (audit RC1).
#
# Réseau : requis uniquement pour les dépendances tierces (Jinja2, argon2,
# jsonschema, connecteur de base de données...), jamais pour les paquets Forge.
#
# Usage :
#     bash tools/smoke-install.sh [--keep]
#
#   --keep   conserve le dossier de travail temporaire (débogage).
#
# Code de sortie : 0 si le parcours complet aboutit, non nul sinon.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
KEEP=0
[ "${1:-}" = "--keep" ] && KEEP=1

WORK="$(mktemp -d)"
WHEELHOUSE="$WORK/wheelhouse"
mkdir -p "$WHEELHOUSE"
cleanup() { [ "$KEEP" -eq 1 ] || rm -rf "$WORK"; }
trap cleanup EXIT

log()  { printf '\n\033[1m== %s ==\033[0m\n' "$*"; }
fail() { printf '\n\033[31mSMOKE INSTALL ÉCHEC : %s\033[0m\n' "$*" >&2; exit 1; }

cd "$REPO_ROOT"

VERSION="$("$PYTHON_BIN" - <<'PY'
import tomllib, pathlib
print(tomllib.loads(pathlib.Path("pyproject.toml").read_text())["project"]["version"])
PY
)"
log "Cible : forge-mvc == $VERSION"

# ── 1. Construire les wheels Forge nécessaires au squelette ──────────────────
SKEL_REQ="cli/skeleton/data/requirements.txt"
[ -f "$SKEL_REQ" ] || fail "squelette introuvable : $SKEL_REQ"

log "Construction des wheels (cœur + paquets épinglés par le squelette)"
"$PYTHON_BIN" -m build --wheel --no-isolation -o "$WHEELHOUSE" . >/dev/null \
    || fail "build de la wheel cœur (forge-mvc) a échoué"

mapfile -t SKEL_PKGS < <(grep -oE '^forge-mvc-[a-z0-9-]+' "$SKEL_REQ" || true)
for pkg in "${SKEL_PKGS[@]}"; do
    dir="packages/$pkg"
    [ -f "$dir/pyproject.toml" ] \
        || fail "le squelette épingle '$pkg' mais packages/$pkg/pyproject.toml est absent"
    "$PYTHON_BIN" -m build --wheel --no-isolation -o "$WHEELHOUSE" "$dir" >/dev/null \
        || fail "build de la wheel $pkg a échoué"
done
log "Wheels construites : $(find "$WHEELHOUSE" -name '*.whl' | wc -l)"

# ── 2. Environnement vierge + installation du CLI depuis le wheelhouse ───────
VENV="$WORK/venv"
"$PYTHON_BIN" -m venv "$VENV"
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q --find-links "$WHEELHOUSE" "forge-mvc==$VERSION" \
    || fail "installation de forge-mvc==$VERSION depuis le wheelhouse a échoué"
"$VENV/bin/forge" --version >/dev/null \
    || fail "la commande 'forge' est indisponible après installation"
log "CLI installé : $("$VENV/bin/forge" --version 2>&1 | head -1)"

# ── 3. forge new en dossier vierge, dépendances résolues via le wheelhouse ───
PROJ_DIR="$WORK/projects"
mkdir -p "$PROJ_DIR"
# PIP_FIND_LINKS est hérité par le `pip install -r requirements.txt` que
# `forge new` lance dans le venv du projet : c'est l'étape qui casse si un
# paquet épinglé n'est pas résolvable.
export PIP_FIND_LINKS="$WHEELHOUSE"
log "forge new SmokeDemo (pip du projet résolu via le wheelhouse local)"
( cd "$PROJ_DIR" && "$VENV/bin/forge" new SmokeDemo --profile minimal ) \
    || fail "forge new a échoué (installation des dépendances du projet généré)"

# ── 4. Smoke du projet généré ────────────────────────────────────────────────
PROJ="$PROJ_DIR/SmokeDemo"
[ -d "$PROJ/.venv" ] || fail "le projet généré n'a pas de venv (.venv)"
[ -f "$PROJ/app.py" ] || fail "le projet généré n'a pas de point d'entrée app.py"
"$PROJ/.venv/bin/forge" --version >/dev/null \
    || fail "'forge' indisponible dans le venv du projet généré"
log "Projet généré opérationnel : $("$PROJ/.venv/bin/forge" --version 2>&1 | head -1)"

printf '\n\033[32mSMOKE INSTALL OK\033[0m — forge new s'"'"'installe et démarre depuis les wheels locales.\n'
