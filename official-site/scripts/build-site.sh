#!/usr/bin/env bash
# build-site.sh — assemble le site forge-web (ADR-045).
#
# official-site est un TUYAU : il ne porte plus de mkdocs.yml ni de nav propre.
# Il construit le site avec le mkdocs.yml CANONIQUE de Forge (qui agrège déjà
# docs/ + les docs « par module » d'ADR-043 via !include, et passe --strict),
# puis assemble :
#
#   dist/
#   ├── index.html      (landing canonique docs/index.html, servie à /)
#   ├── static/         (assets de la landing, depuis docs/static/)
#   ├── robots.txt      (SEO propre au site)
#   ├── sitemap.xml
#   └── docs/forge/     (site MkDocs de Forge, servi sous /docs/forge/)
#
# Aucune duplication : la doc et la landing ont une source unique (docs/).

set -euo pipefail

OS_DIR="$(cd "$(dirname "$0")/.." && pwd)"   # official-site/
FORGE_ROOT="$(cd "$OS_DIR/.." && pwd)"        # racine du dépôt Forge
DIST="$OS_DIR/dist"
FORGE_SITE="$OS_DIR/site"                     # sortie mkdocs intermédiaire (gitignorée)

# venv local de Forge s'il existe (mkdocs + mkdocs-monorepo pour les !include).
if [ -f "$FORGE_ROOT/.venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  . "$FORGE_ROOT/.venv/bin/activate"
fi
if ! command -v mkdocs >/dev/null 2>&1; then
  echo "erreur: mkdocs introuvable (activez le venv ou installez requirements-docs.txt)." >&2
  exit 1
fi

echo "==> Build du site MkDocs de Forge (mkdocs.yml canonique, --strict)"
# Build depuis la racine Forge : les !include (core/*/mkdocs.yml, etc.) y sont relatifs.
( cd "$FORGE_ROOT" && mkdocs build --strict --site-dir "$FORGE_SITE" )

if [ ! -f "$FORGE_SITE/index.html" ]; then
  echo "erreur: build MkDocs sans index.html." >&2
  exit 1
fi

echo "==> Assemblage dist/ (landing à /, doc Forge sous /docs/forge/)"
rm -rf "$DIST"
mkdir -p "$DIST/docs/forge" "$DIST/static"

# Landing canonique (ADR-044) servie à la racine.
cp "$FORGE_ROOT/docs/index.html" "$DIST/index.html"
cp -a "$FORGE_ROOT/docs/static/." "$DIST/static/"

# Documentation Forge sous /docs/forge/.
cp -a "$FORGE_SITE/." "$DIST/docs/forge/"
rm -rf "$FORGE_SITE"

# SEO propre au site.
cp "$OS_DIR/public/robots.txt" "$OS_DIR/public/sitemap.xml" "$DIST/" 2>/dev/null || true

echo
echo "==> Bilan"
echo "  Fichiers totaux : $(find "$DIST" -type f | wc -l)"
for p in "$DIST/index.html" "$DIST/docs/forge/index.html" "$DIST/docs/forge/reference/cli-commands/index.html"; do
  if [ -f "$p" ]; then echo "    ok  ${p#"$DIST"/}"; else echo "    ko  ${p#"$DIST"/} (manquant)"; fi
done
echo
echo "OK — tester : python3 -m http.server 8080 -d $DIST"
echo "  http://127.0.0.1:8080/        → landing"
echo "  http://127.0.0.1:8080/docs/forge/ → documentation"
