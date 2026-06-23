#!/usr/bin/env bash
# Assemble la landing publique (public/) et la documentation MkDocs (site/)
# dans un dossier de sortie unique (dist/) prêt à servir statiquement.
#
# Structure produite :
#   dist/
#   ├── index.html      (landing servie à /)
#   ├── static/         (assets de la landing)
#   └── docs/           (site MkDocs, servi à /docs/)
#       ├── index.html
#       ├── forge/
#       ├── search/
#       └── ...

set -euo pipefail

# Se positionner à la racine du dépôt.
cd "$(dirname "$0")/.."

DIST="dist"
SITE="site"

# Activer le venv local s'il existe.
if [ -f ".venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  . .venv/bin/activate
fi

if ! command -v mkdocs >/dev/null 2>&1; then
  echo "erreur: mkdocs introuvable." >&2
  echo "       Activez le venv (.venv/bin/activate) ou installez :" >&2
  echo "       python -m pip install -r requirements-docs.txt" >&2
  exit 1
fi

echo "==> Nettoyage de $DIST et $SITE"
rm -rf "$DIST" "$SITE"
mkdir -p "$DIST"

echo "==> Copie de la landing depuis public/"
cp -a public/. "$DIST/"

echo "==> Génération MkDocs (mkdocs build --strict)"
mkdocs build --strict

echo "==> Intégration du site MkDocs sous $DIST/docs/"
mkdir -p "$DIST/docs"
cp -a "$SITE/." "$DIST/docs/"

echo
echo "==> Bilan"
echo "  Fichiers totaux : $(find "$DIST" -type f | wc -l)"
echo "  Pages cibles :"
for p in "$DIST/index.html" "$DIST/docs/index.html" "$DIST/docs/forge/index.html"; do
  if [ -f "$p" ]; then echo "    ok  $p"; else echo "    ko  $p (manquant)"; fi
done

echo
echo "OK — pour tester localement :"
echo "  python3 -m http.server 8080 -d $DIST"
echo "  http://127.0.0.1:8080/        → landing"
echo "  http://127.0.0.1:8080/docs/   → documentation"
