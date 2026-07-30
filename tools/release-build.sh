#!/usr/bin/env bash
#
# Build de toutes les distributions Forge (forge-mvc + les opt-ins de
# packages/) dans ./dist/. Le compte n'est PAS écrit en dur : il a valu 13,
# puis 25, puis 28, et un nombre figé dans un commentaire ne prévient de
# rien quand un paquet neuf n'est pas publié (RELEASE-PYPI-COMPLETENESS-GUARD-001).
# puis `twine check`. N'UPLOADE RIEN par défaut.
#
# Usage :
#   bash tools/release-build.sh            # build + twine check (aucune publication)
#   bash tools/release-build.sh --upload   # build + twine check + twine upload dist/*
#
# La version est lue dans pyproject.toml (clé [project].version, PEP 440).
# Le tag/push restent MANUELS (politique : ne pas pousser sans accord) ; les
# commandes exactes sont affichées en fin de build.
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$(pwd)"
DIST="$ROOT/dist"
MODE="${1:-}"

VERSION="$(grep -m1 '^version' pyproject.toml | cut -d'"' -f2)"          # ex : 1.0.0b17 (PEP 440)
SEMVER="$(printf '%s' "$VERSION" | sed -E 's/a([0-9]+)$/-alpha.\1/; s/rc([0-9]+)$/-rc.\1/; s/b([0-9]+)$/-beta.\1/')"  # ex : 1.0.0-beta.17

echo "============================================================"
echo " Forge — build release  |  version $VERSION  (tag v$SEMVER)"
echo "============================================================"

# 1. Nettoyage des artefacts de build (reproductibilité)
echo "-- nettoyage dist/ build/ *.egg-info --"
rm -rf "$DIST" "$ROOT/build" "$ROOT"/*.egg-info
find packages -maxdepth 2 -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true

# PKG-WHEEL-NO-CACHE-001 — purge des caches d'outillage avant build. Le squelette
# porte sa propre config ruff (`skeleton/data/pyproject.toml`), donc `ruff check .`
# crée `skeleton/data/.ruff_cache` ; avec `include-package-data = true`, les globs
# package-data l'embarqueraient dans la wheel (ni exclude-package-data ni le prune
# MANIFEST ne le filtrent pour la wheel). On le supprime du disque en amont.
echo "-- purge caches d'outillage (.ruff_cache/.pytest_cache/.mypy_cache) --"
find "$ROOT" -type d \( -name .ruff_cache -o -name .pytest_cache -o -name .mypy_cache \) \
    -exec rm -rf {} + 2>/dev/null || true

# 2. Build du cœur forge-mvc (racine) puis des 12 opt-ins, vers un dist/ partagé
echo "-- build forge-mvc (racine) --"
python -m build "$ROOT" --outdir "$DIST"

for pkg in packages/forge-mvc-*/; do
    name="$(basename "$pkg")"
    echo "-- build $name --"
    python -m build "$pkg" --outdir "$DIST"
done

# 3. Validation packaging
echo "-- twine check --"
twine check "$DIST"/*

# 4. Récapitulatif (une wheel et une sdist par distribution du dépôt)
n="$(ls -1 "$DIST" | wc -l | tr -d ' ')"
echo "-- $n artefacts dans dist/ --"
ls -1 "$DIST"

# 5. Upload (uniquement si demandé explicitement)
if [ "$MODE" = "--upload" ]; then
    echo "-- twine upload (PyPI) — publication de toutes les distributions --"
    twine upload "$DIST"/*
    echo "Upload terminé."
else
    cat <<EOF

Build + twine check OK. RIEN n'a été publié.

Étapes de publication (manuelles, dans l'ordre) :

  # 1) Publier toutes les distributions sur PyPI
  bash tools/release-build.sh --upload      # (ou : twine upload dist/*)

  # 2) Taguer la release
  git tag -a v$SEMVER -m "Forge $SEMVER"

  # 3) Pousser branche + tag
  git push origin main
  git push origin v$SEMVER

EOF
fi
