#!/usr/bin/env bash
# Validation pré-release Forge.
# Usage : bash tools/release-validate.sh [VERSION]
# Ex.   : bash tools/release-validate.sh 3.0.2
set -euo pipefail

VERSION="${1:-}"
ERRORS=0
WARNS=0

_ok()   { printf "[OK]    %s\n" "$1"; }
_warn() { printf "[WARN]  %s\n" "$1"; WARNS=$((WARNS+1)); }
_fail() { printf "[FAIL]  %s\n" "$1"; ERRORS=$((ERRORS+1)); }

echo "=== Validation pré-release Forge ${VERSION:-<version non fournie>} ==="
echo ""

# ── 1. Version fournie ────────────────────────────────────────────────────────
if [ -z "$VERSION" ]; then
    _warn "Aucune version fournie en argument (ex : bash tools/release-validate.sh 3.0.2)"
else
    _ok "Version cible : $VERSION"
fi

# ── 2. Cohérence des versions ─────────────────────────────────────────────────
if [ -n "$VERSION" ]; then
    PYPROJECT_VER=$(python3 -c "
import tomllib, sys
with open('pyproject.toml', 'rb') as f:
    d = tomllib.load(f)
print(d['project']['version'])
" 2>/dev/null || echo "ERREUR")

    if [ "$PYPROJECT_VER" = "$VERSION" ]; then
        _ok "pyproject.toml version = $VERSION"
    else
        _fail "pyproject.toml version = '$PYPROJECT_VER' (attendu : '$VERSION')"
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

    if [ "$CORE_VER" = "$VERSION" ]; then
        _ok "core/__init__.py __version__ = $VERSION"
    else
        _fail "core/__init__.py __version__ = '$CORE_VER' (attendu : '$VERSION')"
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

    if [ "$FORGE_VER" = "$VERSION" ]; then
        _ok "forge.py _FORGE_VERSION = $VERSION"
    else
        _fail "forge.py _FORGE_VERSION = '$FORGE_VER' (attendu : '$VERSION')"
    fi
fi

# ── 3. CHANGELOG ─────────────────────────────────────────────────────────────
if [ -n "$VERSION" ]; then
    if grep -qF "## [$VERSION]" CHANGELOG.md 2>/dev/null; then
        _ok "CHANGELOG.md contient ## [$VERSION]"
    else
        _fail "CHANGELOG.md ne contient pas ## [$VERSION]"
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

# ── 8. État git propre ────────────────────────────────────────────────────────
DIRTY=$(git status --porcelain 2>/dev/null | grep -v "^??" || true)
if [ -z "$DIRTY" ]; then
    _ok "Git : répertoire de travail propre"
else
    _fail "Git : modifications non commitées :"
    echo "$DIRTY" | head -10 | sed 's/^/         /'
fi

# ── 9. Whitespace ─────────────────────────────────────────────────────────────
WS=$(git diff --check HEAD 2>/dev/null || true)
if [ -z "$WS" ]; then
    _ok "git diff --check : aucun problème de whitespace"
else
    _warn "Whitespace : $WS"
fi

# ── 10. Tag absent (pré-release) ──────────────────────────────────────────────
if [ -n "$VERSION" ]; then
    if git tag --list "v$VERSION" | grep -q "v$VERSION"; then
        _warn "Tag v$VERSION existe déjà (re-release ?)"
    else
        _ok "Tag v$VERSION absent — prêt à créer"
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
