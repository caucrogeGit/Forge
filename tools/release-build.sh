#!/usr/bin/env bash
#
# Build des 13 paquets Forge (forge-mvc + les 12 opt-ins) dans ./dist/,
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

# 4. Récapitulatif (13 wheels + 13 sdists attendus)
n="$(ls -1 "$DIST" | wc -l | tr -d ' ')"
echo "-- $n artefacts dans dist/ --"
ls -1 "$DIST"

# 5. Upload (uniquement si demandé explicitement)
if [ "$MODE" = "--upload" ]; then
    echo "-- twine upload (PyPI) — publication des 13 paquets --"
    twine upload "$DIST"/*
    echo "Upload terminé."
else
    cat <<EOF

Build + twine check OK. RIEN n'a été publié.

Étapes de publication (manuelles, dans l'ordre) :

  # 1) Publier les 13 paquets sur PyPI
  bash tools/release-build.sh --upload      # (ou : twine upload dist/*)

  # 2) Taguer la release
  git tag -a v$SEMVER -m "Forge $SEMVER"

  # 3) Pousser branche + tag
  git push origin main
  git push origin v$SEMVER

EOF
fi
