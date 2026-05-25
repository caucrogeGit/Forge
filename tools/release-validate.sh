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

VERSION="${1:-}"
PUBLIC_VERSION=""
PEP440_VERSION=""
ERRORS=0
WARNS=0

_ok()   { printf "[OK]    %s\n" "$1"; }
_warn() { printf "[WARN]  %s\n" "$1"; WARNS=$((WARNS+1)); }
_fail() { printf "[FAIL]  %s\n" "$1"; ERRORS=$((ERRORS+1)); }

echo "=== Validation pré-release Forge ${VERSION:-<version non fournie>} ==="
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
    PYPROJECT_VER=$(python3 -c "
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

    CORE_VER=$(python3 -c "
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

    FORGE_VER=$(python3 -c "
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
PYTEST_OUT=$(python -m pytest -x -q 2>&1 || true)
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
RUFF_OUT=$(ruff check . --quiet 2>&1 || true)
if [ -z "$RUFF_OUT" ]; then
    _ok "Ruff : aucune violation"
else
    _fail "Ruff : violations détectées"
    echo "$RUFF_OUT" | head -10 | sed 's/^/         /'
fi

# ── 6. Compilation Python ─────────────────────────────────────────────────────
COMPILE_OUT=$(python -m compileall -q . 2>&1 || true)
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
MKDOCS_OUT=$(mkdocs build --strict --quiet 2>&1); MKDOCS_EXIT=$?; true
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
if ! command -v pip-audit >/dev/null 2>&1; then
    _fail "pip-audit non installé — requis pour la validation release."
    echo "         Installer : python -m pip install 'pip-audit>=2.0'"
else
    PIP_AUDIT_RT_OUT=$(pip-audit -r requirements.txt 2>&1); PIP_AUDIT_RT_EXIT=$?; true
    if [ $PIP_AUDIT_RT_EXIT -eq 0 ]; then
        _ok "pip-audit (requirements.txt) : aucune vulnérabilité"
    else
        _fail "pip-audit (requirements.txt) : vulnérabilités détectées"
        echo "$PIP_AUDIT_RT_OUT" | head -20 | sed 's/^/         /'
    fi
    PIP_AUDIT_DEV_OUT=$(pip-audit -r requirements-dev.txt 2>&1); PIP_AUDIT_DEV_EXIT=$?; true
    if [ $PIP_AUDIT_DEV_EXIT -eq 0 ]; then
        _ok "pip-audit (requirements-dev.txt) : aucune vulnérabilité"
    else
        _fail "pip-audit (requirements-dev.txt) : vulnérabilités détectées"
        echo "$PIP_AUDIT_DEV_OUT" | head -20 | sed 's/^/         /'
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
    NPM_AUDIT_OUT=$(npm audit --omit=dev 2>&1); NPM_AUDIT_EXIT=$?; true
    if [ $NPM_AUDIT_EXIT -eq 0 ]; then
        _ok "npm audit (--omit=dev) : aucune vulnérabilité"
    else
        _fail "npm audit (--omit=dev) : vulnérabilités détectées"
        echo "$NPM_AUDIT_OUT" | head -20 | sed 's/^/         /'
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
