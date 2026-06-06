#!/usr/bin/env bash
# Validation pré-release Forge.
# Usage : bash tools/release-validate.sh [VERSION]
# Ex.   : bash tools/release-validate.sh 1.0.0-beta.9
#         bash tools/release-validate.sh 1.0.0b9
#
# Forge utilise deux formats équivalents pour la même release :
#   - SemVer public : 1.0.0-beta.9 (CHANGELOG, tags git, package.json, docs)
#   - PEP 440       : 1.0.0b9      (pyproject.toml, core/__init__.py, forge.py)
# Le script accepte l'un ou l'autre en entrée et normalise vers le format
# attendu de chaque source.
#
# Mode utilitaire (testabilité) :
#   bash tools/release-validate.sh --convert pep440   1.0.0-beta.9
#   bash tools/release-validate.sh --convert semver   1.0.0b9
#   bash tools/release-validate.sh --convert validate 1.0.0-beta.9
set -euo pipefail

# ── Helpers de conversion / validation de version ───────────────────────────
# Définis tôt pour être utilisables en mode --convert (test méta).

to_pep440() {
    # SemVer public -> PEP 440. Stable inchangé.
    #   1.0.0-alpha.N -> 1.0.0aN
    #   1.0.0-beta.N  -> 1.0.0bN
    #   1.0.0-rc.N    -> 1.0.0rcN
    printf '%s\n' "$1" \
        | sed -E 's/-alpha\.([0-9]+)$/a\1/; s/-beta\.([0-9]+)$/b\1/; s/-rc\.([0-9]+)$/rc\1/'
}

to_semver_public() {
    # PEP 440 -> SemVer public. Stable inchangé.
    # Ordre : `rc` traité avant `b` (sinon `b` matcherait la fin de `rc`).
    printf '%s\n' "$1" \
        | sed -E 's/rc([0-9]+)$/-rc.\1/; s/a([0-9]+)$/-alpha.\1/; s/b([0-9]+)$/-beta.\1/'
}

is_valid_version() {
    # Accepte SemVer public OU PEP 440 (sous-ensemble Forge).
    #   stable      : 1.0.0
    #   pre-release : 1.0.0-{alpha,beta,rc}.N (SemVer) ou 1.0.0{a,b,rc}N (PEP 440)
    local v="${1:-}"
    if [[ "$v" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-(alpha|beta|rc)\.[0-9]+)?$ ]]; then
        return 0
    fi
    if [[ "$v" =~ ^[0-9]+\.[0-9]+\.[0-9]+((a|b|rc)[0-9]+)?$ ]]; then
        return 0
    fi
    return 1
}

# ── Mode utilitaire --convert (testabilité, n'exécute pas la validation) ────
if [ "${1:-}" = "--convert" ]; then
    case "${2:-}" in
        pep440)   to_pep440 "${3:-}"; exit 0 ;;
        semver)   to_semver_public "${3:-}"; exit 0 ;;
        validate) is_valid_version "${3:-}" && exit 0 || exit 1 ;;
        *) echo "Usage: $0 --convert {pep440|semver|validate} VERSION" >&2 ; exit 2 ;;
    esac
fi

# RELEASE-VALIDATE-PACKAGES-001 — `--with-packages` (opt-in) ajoute le build
# de toutes les distributions (core + opt-ins) + twine check. Hors flag,
# comportement inchangé (on ne rallonge pas chaque run ; la CI build aussi).
WITH_PACKAGES=false
_ARGS=()
for _arg in "$@"; do
    case "$_arg" in
        --with-packages) WITH_PACKAGES=true ;;
        *) _ARGS+=("$_arg") ;;
    esac
done
VERSION="${_ARGS[0]:-}"
PUBLIC_VERSION=""
PEP440_VERSION=""
ERRORS=0
WARNS=0

_ok()   { printf "[OK]    %s\n" "$1"; }
_warn() { printf "[WARN]  %s\n" "$1"; WARNS=$((WARNS+1)); }
_fail() { printf "[FAIL]  %s\n" "$1"; ERRORS=$((ERRORS+1)); }

# ── Interpréteur Python — RELEASE-VALIDATE-PATH-ROBUSTNESS-001 ───────────────
# Tous les appels Python du script (pytest, compileall, ruff, mkdocs,
# pip-audit) passent par "$PYTHON_BIN" -m … plutôt que par les binaires
# du PATH. Ainsi, lancer le script sans venv activé donne une erreur
# explicite « Python introuvable », plutôt qu'un cascadé `command not found`
# sur chaque outil. Configurable via la variable d'environnement
# `PYTHON=/chemin/vers/python`.
PYTHON_BIN="${PYTHON:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    printf "[FAIL]  Python introuvable : %s\n" "$PYTHON_BIN" >&2
    printf "         Définissez PYTHON=/chemin/vers/python ou activez votre environnement Python.\n" >&2
    exit 1
fi

echo "=== Validation pré-release Forge ${VERSION:-<version non fournie>} ==="
if $WITH_PACKAGES; then
    echo "Mode : --with-packages (build des distributions core + opt-ins + twine check)"
fi
echo ""

# ── 1. Version fournie ────────────────────────────────────────────────────────
if [ -z "$VERSION" ]; then
    _warn "Aucune version fournie en argument (ex : bash tools/release-validate.sh 1.0.0-beta.9)"
elif ! is_valid_version "$VERSION"; then
    _fail "Version '$VERSION' invalide. Formats acceptés :"
    _fail "  - SemVer public : 1.0.0, 1.0.0-alpha.N, 1.0.0-beta.N, 1.0.0-rc.N"
    _fail "  - PEP 440       : 1.0.0, 1.0.0aN, 1.0.0bN, 1.0.0rcN"
else
    PUBLIC_VERSION=$(to_semver_public "$VERSION")
    PEP440_VERSION=$(to_pep440 "$VERSION")
    if [ "$PUBLIC_VERSION" = "$PEP440_VERSION" ]; then
        _ok "Version cible : $VERSION (stable, même format SemVer/PEP 440)"
    else
        _ok "Version cible : $PUBLIC_VERSION (SemVer) ≡ $PEP440_VERSION (PEP 440)"
    fi
fi

# ── 2. Cohérence des versions (format PEP 440) ───────────────────────────────
if [ -n "$PEP440_VERSION" ]; then
    PYPROJECT_VER=$("$PYTHON_BIN" -c "
import tomllib, sys
with open('pyproject.toml', 'rb') as f:
    d = tomllib.load(f)
print(d['project']['version'])
" 2>/dev/null || echo "ERREUR")

    if [ "$PYPROJECT_VER" = "$PEP440_VERSION" ]; then
        _ok "pyproject.toml version = $PEP440_VERSION (PEP 440)"
    else
        _fail "pyproject.toml version = '$PYPROJECT_VER' (attendu : '$PEP440_VERSION' au format PEP 440)"
    fi

    CORE_VER=$("$PYTHON_BIN" -c "
import ast, sys
tree = ast.parse(open('core/__init__.py').read())
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id == '__version__':
                print(ast.literal_eval(node.value))
                sys.exit(0)
print('INTROUVABLE')
" 2>/dev/null || echo "ERREUR")

    if [ "$CORE_VER" = "$PEP440_VERSION" ]; then
        _ok "core/__init__.py __version__ = $PEP440_VERSION (PEP 440)"
    else
        _fail "core/__init__.py __version__ = '$CORE_VER' (attendu : '$PEP440_VERSION' au format PEP 440)"
    fi

    FORGE_VER=$("$PYTHON_BIN" -c "
import ast, sys
tree = ast.parse(open('forge.py').read())
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id == '_FORGE_VERSION':
                print(ast.literal_eval(node.value))
                sys.exit(0)
print('INTROUVABLE')
" 2>/dev/null || echo "ERREUR")

    if [ "$FORGE_VER" = "$PEP440_VERSION" ]; then
        _ok "forge.py _FORGE_VERSION = $PEP440_VERSION (PEP 440)"
    else
        _fail "forge.py _FORGE_VERSION = '$FORGE_VER' (attendu : '$PEP440_VERSION' au format PEP 440)"
    fi
fi

# ── 3. CHANGELOG (format SemVer public) ──────────────────────────────────────
if [ -n "$PUBLIC_VERSION" ]; then
    if grep -qF "## [$PUBLIC_VERSION]" CHANGELOG.md 2>/dev/null; then
        _ok "CHANGELOG.md contient ## [$PUBLIC_VERSION] (SemVer)"
    else
        _fail "CHANGELOG.md ne contient pas ## [$PUBLIC_VERSION] (SemVer)"
    fi
fi

# ── 4. Tests ──────────────────────────────────────────────────────────────────
echo ""
echo "--- Exécution des tests (pytest -x -q) ---"
PYTEST_OUT=$("$PYTHON_BIN" -m pytest -x -q 2>&1 || true)
echo "$PYTEST_OUT" | tail -5
if echo "$PYTEST_OUT" | grep -qE "passed|no tests ran"; then
    if ! echo "$PYTEST_OUT" | grep -qE "^(FAILED|ERROR)"; then
        _ok "Tests : OK"
    else
        _fail "Tests : échec"
    fi
else
    _fail "Tests : échec (voir sortie ci-dessus)"
fi

# ── 5. Qualité de code ────────────────────────────────────────────────────────
echo ""
echo "--- Ruff ---"
RUFF_OUT=$("$PYTHON_BIN" -m ruff check . --quiet 2>&1 || true)
if [ -z "$RUFF_OUT" ]; then
    _ok "Ruff : aucune violation"
else
    _fail "Ruff : violations détectées"
    echo "$RUFF_OUT" | head -10 | sed 's/^/         /'
fi

# ── 6. Compilation Python ─────────────────────────────────────────────────────
COMPILE_OUT=$("$PYTHON_BIN" -m compileall -q . 2>&1 || true)
SYNTAX_ERRORS=$(echo "$COMPILE_OUT" | grep -v "^Listing" || true)
if [ -z "$SYNTAX_ERRORS" ]; then
    _ok "compileall : OK"
else
    _fail "compileall : erreurs de syntaxe"
    echo "$SYNTAX_ERRORS" | head -5 | sed 's/^/         /'
fi

# ── 7. MkDocs strict ─────────────────────────────────────────────────────────
echo ""
echo "--- MkDocs --strict ---"
MKDOCS_OUT=$("$PYTHON_BIN" -m mkdocs build --strict --quiet 2>&1); MKDOCS_EXIT=$?; true
if [ $MKDOCS_EXIT -eq 0 ]; then
    _ok "MkDocs build --strict : OK"
else
    _fail "MkDocs build --strict : erreurs"
    echo "$MKDOCS_OUT" | grep -v "Material for MkDocs" | head -10 | sed 's/^/         /'
fi

# ── 8. Audit dépendances Python (pip-audit) — bloquant release ───────────────
# DEPENDENCY-AUDIT-RELEASE-GUARD-001 : `.github/workflows/dependency-audit.yml`
# reste informatif (continue-on-error: true) pour la surveillance hebdo ; ici
# en validation release, toute CVE ouverte sur les requirements bloque.
echo ""
echo "--- Audit dépendances Python (pip-audit) ---"
if ! "$PYTHON_BIN" -m pip_audit --version >/dev/null 2>&1; then
    _fail "pip-audit non installé dans $PYTHON_BIN — requis pour la validation release."
    echo "         Installer : $PYTHON_BIN -m pip install 'pip-audit>=2.0'"
else
    # RELEASE-VALIDATE-SETE-FIX-001 : la command-substitution est placée
    # DANS la condition du `if` (exemptée de `set -e`). L'ancien motif
    # `VAR=$(cmd); EXIT=$?; true` ne protégeait PAS l'assignation : un
    # pip-audit en échec tuait le script avant d'afficher le _fail.
    if PIP_AUDIT_RT_OUT=$("$PYTHON_BIN" -m pip_audit -r requirements.txt 2>&1); then
        _ok "pip-audit (requirements.txt) : aucune vulnérabilité"
    else
        _fail "pip-audit (requirements.txt) : vulnérabilités détectées"
        printf '%s\n' "$PIP_AUDIT_RT_OUT" | head -20 | sed 's/^/         /' || true
    fi
    if PIP_AUDIT_DEV_OUT=$("$PYTHON_BIN" -m pip_audit -r requirements-dev.txt 2>&1); then
        _ok "pip-audit (requirements-dev.txt) : aucune vulnérabilité"
    elif printf '%s' "$PIP_AUDIT_DEV_OUT" | grep -qiE 'No matching distribution found for forge-mvc|Could not find a version that satisfies the requirement forge-mvc'; then
        # Œuf-poule pré-release : requirements-dev.txt installe les opt-ins
        # locaux en éditable, qui dépendent de forge-mvc>=<version> pas encore
        # publié sur PyPI. La résolution échoue — ce n'est PAS une CVE.
        # L'audit dev redevient effectif après publication de forge-mvc.
        _warn "pip-audit (requirements-dev.txt) : différé — opt-ins locaux exigent forge-mvc non encore publié (œuf-poule pré-release) ; relancer après publication PyPI"
    else
        _fail "pip-audit (requirements-dev.txt) : vulnérabilités détectées"
        printf '%s\n' "$PIP_AUDIT_DEV_OUT" | head -20 | sed 's/^/         /' || true
    fi
fi

# ── 9. Audit dépendances Node (npm audit) — bloquant release ─────────────────
# `--omit=dev` : ne contrôle que les dépendances de production déclarées dans
# `package.json` (devDependencies non vérifiées ici).
echo ""
echo "--- Audit dépendances Node (npm audit --omit=dev) ---"
if [ ! -f package.json ]; then
    _ok "npm audit : aucun package.json — étape sans objet."
elif ! command -v npm >/dev/null 2>&1; then
    _fail "npm non installé — requis pour la validation release Node."
    echo "         Installer Node.js / npm puis relancer."
else
    if NPM_AUDIT_OUT=$(npm audit --omit=dev 2>&1); then
        _ok "npm audit (--omit=dev) : aucune vulnérabilité"
    else
        _fail "npm audit (--omit=dev) : vulnérabilités détectées"
        printf '%s\n' "$NPM_AUDIT_OUT" | head -20 | sed 's/^/         /' || true
    fi
fi

# ── 10. État git propre ──────────────────────────────────────────────────────
DIRTY=$(git status --porcelain 2>/dev/null | grep -v "^??" || true)
if [ -z "$DIRTY" ]; then
    _ok "Git : répertoire de travail propre"
else
    _fail "Git : modifications non commitées :"
    echo "$DIRTY" | head -10 | sed 's/^/         /'
fi

# ── 11. Whitespace ───────────────────────────────────────────────────────────
WS=$(git diff --check HEAD 2>/dev/null || true)
if [ -z "$WS" ]; then
    _ok "git diff --check : aucun problème de whitespace"
else
    _warn "Whitespace : $WS"
fi

# ── 12. Tag absent (pré-release) — format SemVer public ─────────────────────
if [ -n "$PUBLIC_VERSION" ]; then
    if git tag --list "v$PUBLIC_VERSION" | grep -q "v$PUBLIC_VERSION"; then
        _warn "Tag v$PUBLIC_VERSION existe déjà (re-release ?)"
    else
        _ok "Tag v$PUBLIC_VERSION absent — prêt à créer"
    fi
fi

# ── 13. Build & twine des distributions (opt-in : --with-packages) ───────────
# RELEASE-VALIDATE-PACKAGES-001 — preuve LOCALE que le core + tous les opt-ins
# se construisent et passent twine check (pas seulement « la CI le fait »).
# La liste des opt-ins est dérivée de packages/*/ (pas de liste codée en dur :
# tout nouvel opt-in est couvert automatiquement).
# Exécuté après le contrôle git propre : les artefacts dist/ sont gitignorés.
if $WITH_PACKAGES; then
    echo ""
    echo "--- Build des distributions (core + opt-ins) ---"
    rm -rf dist build ./*.egg-info
    for _p in packages/*/; do rm -rf "${_p}dist" "${_p}build" "${_p}"*.egg-info; done 2>/dev/null || true
    BUILD_OK=true
    _dist_count=1
    if ! "$PYTHON_BIN" -m build --no-isolation >/tmp/relval_build_core.log 2>&1; then
        _fail "build core : échec"
        tail -8 /tmp/relval_build_core.log | sed 's/^/         /' || true
        BUILD_OK=false
    fi
    for _pkg in packages/*/; do
        [ -f "${_pkg}pyproject.toml" ] || continue
        if ! "$PYTHON_BIN" -m build --no-isolation "$_pkg" >/tmp/relval_build_pkg.log 2>&1; then
            _fail "build ${_pkg%/} : échec"
            tail -8 /tmp/relval_build_pkg.log | sed 's/^/         /' || true
            BUILD_OK=false
        else
            _dist_count=$((_dist_count + 1))
        fi
    done
    if $BUILD_OK; then
        _ok "Build : ${_dist_count} distributions construites (core + opt-ins)"
        echo "--- twine check des artefacts ---"
        if "$PYTHON_BIN" -m twine check dist/* packages/*/dist/* >/tmp/relval_twine.log 2>&1; then
            _ok "twine check : tous les artefacts valides"
        else
            _fail "twine check : artefact(s) invalide(s)"
            tail -20 /tmp/relval_twine.log | sed 's/^/         /' || true
        fi
    fi
fi

# ── Résumé ────────────────────────────────────────────────────────────────────
echo ""
echo "=== Résumé : $ERRORS erreur(s), $WARNS avertissement(s) ==="
if [ "$ERRORS" -gt 0 ]; then
    echo "RÉSULTAT : ÉCHEC — corriger les [FAIL] avant de releaser."
    exit 1
else
    echo "RÉSULTAT : OK — prêt à releaser."
    exit 0
fi
