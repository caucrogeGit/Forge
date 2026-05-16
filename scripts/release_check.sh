#!/usr/bin/env bash
# Validation release locale reproductible — Forge.
#
# Usage :
#   bash scripts/release_check.sh           Mode standard
#   bash scripts/release_check.sh --full    Mode complet (+ build wheel + twine check)
#   bash scripts/release_check.sh --help    Aide
#
# Ce script ne publie rien, ne crée aucun tag, ne modifie pas la version.
# Ticket : RELEASE-CHECK-SCRIPT-001
set -euo pipefail

# ── Constantes ────────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

ERRORS=0
WARNS=0
FULL=false

# ── Helpers ───────────────────────────────────────────────────────────────────

_ok()   { printf "[OK]   %s\n" "$1"; }
_fail() { printf "[FAIL] %s\n" "$1"; ERRORS=$((ERRORS+1)); }
_warn() { printf "[WARN] %s\n" "$1"; WARNS=$((WARNS+1)); }
_skip() { printf "[SKIP] %s\n" "$1"; }
_step() { printf "\n=== %s ===\n" "$1"; }

# ── Arguments ─────────────────────────────────────────────────────────────────

for arg in "$@"; do
    case "$arg" in
        --help|-h)
            cat <<'EOF'
scripts/release_check.sh — Validation release locale Forge

USAGE
    bash scripts/release_check.sh           Mode standard
    bash scripts/release_check.sh --full    Mode complet
    bash scripts/release_check.sh --help    Aide

MODE STANDARD
    Exécute la chaîne de validation source sans build :
      - pytest                     Suite de tests complète
      - python -m compileall -q .  Intégrité des imports Python
      - mkdocs build --strict      Documentation sans avertissement
      - git diff --check           Aucun problème de whitespace
      - git status                 Affichage de l'état du dépôt

MODE --full
    Exécute le mode standard puis la validation packaging locale :
      - rm -rf dist build *.egg-info  Nettoyage des artefacts précédents
      - python -m build               Construction wheel + sdist
      - twine check dist/*            Validation des métadonnées PyPI

    Les artefacts dist/, build/ et *.egg-info/ sont générés localement.
    Ils sont exclus de Git et ne sont pas publiés.

CE QUE CE SCRIPT NE FAIT PAS
    - Il ne publie rien sur PyPI.
    - Il ne crée aucun tag.
    - Il ne modifie pas la version.
    - La publication relève du ticket BETA-2-RELEASE-001.

SCRIPT COMPLÉMENTAIRE
    Pour la vérification de cohérence de version et CHANGELOG :
      bash tools/release-validate.sh <VERSION>

EOF
            exit 0
            ;;
        --full)
            FULL=true
            ;;
        *)
            printf "[ERREUR] Argument inconnu : %s\n" "$arg"
            printf "Usage : bash scripts/release_check.sh [--full] [--help]\n"
            exit 1
            ;;
    esac
done

# ── Positionnement racine ────────────────────────────────────────────────────

cd "$REPO_ROOT"
printf "=== Validation release Forge — %s ===\n" "$(date '+%Y-%m-%d %H:%M:%S')"
printf "Répertoire : %s\n" "$REPO_ROOT"
if $FULL; then
    printf "Mode       : complet (--full)\n"
else
    printf "Mode       : standard\n"
fi
printf "Ce script ne publie rien et ne crée aucun tag.\n"

# ── 1. Tests ──────────────────────────────────────────────────────────────────

_step "1. Tests (pytest)"
if python -m pytest -x -q 2>&1; then
    _ok "pytest : OK"
else
    _fail "pytest : échec"
fi

# ── 2. Compilation Python ─────────────────────────────────────────────────────

_step "2. Compilation Python"
COMPILE_OUT=$(python -m compileall -q . 2>&1 || true)
if [ -z "$COMPILE_OUT" ]; then
    _ok "compileall : OK"
else
    _fail "compileall : erreurs de syntaxe"
    printf "%s\n" "$COMPILE_OUT"
fi

# ── 3. Documentation MkDocs ───────────────────────────────────────────────────

_step "3. Documentation (mkdocs build --strict)"
if mkdocs build --strict --quiet 2>&1; then
    _ok "mkdocs build --strict : OK"
else
    _fail "mkdocs build --strict : erreurs ou avertissements"
fi

# ── 4. Whitespace ─────────────────────────────────────────────────────────────

_step "4. Whitespace (git diff --check)"
WS_OUT=$(git diff --check 2>&1 || true)
if [ -z "$WS_OUT" ]; then
    _ok "git diff --check : OK"
else
    _warn "git diff --check : problèmes de whitespace"
    printf "%s\n" "$WS_OUT"
fi

# ── 5. État Git ───────────────────────────────────────────────────────────────

_step "5. État Git (git status)"
git status --short
DIRTY=$(git status --porcelain 2>/dev/null | grep -v "^??" || true)
if [ -z "$DIRTY" ]; then
    _ok "git status : répertoire propre (hors fichiers non suivis)"
else
    _warn "git status : modifications non commitées"
fi

# ── 6. Synchronisation de version (optionnel) ─────────────────────────────────

_step "6. Synchronisation de version"
if [ -f "tools/check_version_sync.py" ]; then
    if python tools/check_version_sync.py 2>&1; then
        _ok "check_version_sync.py : OK"
    else
        _fail "check_version_sync.py : incohérence de version"
    fi
else
    _skip "tools/check_version_sync.py absent — vérification manuelle via tools/release-validate.sh"
fi

# ── Mode --full : validation packaging ───────────────────────────────────────

if $FULL; then
    _step "7. Packaging (python -m build)"
    rm -rf dist build ./*.egg-info
    if python -m build 2>&1; then
        _ok "python -m build : OK"
    else
        _fail "python -m build : échec"
    fi

    _step "8. Vérification métadonnées (twine check)"
    if twine check dist/* 2>&1; then
        _ok "twine check : OK"
    else
        _fail "twine check : échec"
    fi

    printf "\nNote : les artefacts dist/, build/ et *.egg-info/ sont générés\n"
    printf "localement et exclus de Git. Ils ne sont pas publiés ici.\n"
fi

# ── Résumé ────────────────────────────────────────────────────────────────────

printf "\n=== Résumé : %d erreur(s), %d avertissement(s) ===\n" "$ERRORS" "$WARNS"
if [ "$ERRORS" -gt 0 ]; then
    printf "RÉSULTAT : ÉCHEC — corriger les [FAIL] avant de releaser.\n"
    exit 1
else
    printf "RÉSULTAT : OK\n"
    exit 0
fi
