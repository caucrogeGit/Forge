#!/usr/bin/env bash
# tools/publish.sh — publication PyPI ORDONNÉE et REPRENABLE de Forge.
#
# Publie le cœur `forge-mvc` d'abord (les opt-ins en dépendent), puis les
# opt-ins un par un. Chaque upload passe `--skip-existing` : le script est
# IDEMPOTENT et REPRENABLE. Utile car PyPI limite la CRÉATION de nouveaux
# projets (erreur 429) : si un nouveau paquet échoue en 429, on attend puis on
# relance ce script, il saute les déjà-publiés et reprend les restants.
#
# Sécurité : DRY-RUN par défaut (affiche la séquence, ne publie rien).
# N'upload réellement qu'avec `--upload`.
#
# Prérequis pour --upload : `~/.pypirc` configuré (jeton PyPI) et les
# distributions construites dans dist/ (ce script les (re)construit via
# tools/release-build.sh).
#
# Usage :
#   bash tools/publish.sh            # DRY-RUN : build + affiche l'ordre, ne publie rien
#   bash tools/publish.sh --upload   # build + twine check + publication réelle
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST="$ROOT/dist"
UPLOAD=false
[ "${1:-}" = "--upload" ] && UPLOAD=true

VERSION="$(python3 - <<'PY'
import tomllib, pathlib
print(tomllib.loads(pathlib.Path("pyproject.toml").read_text())["project"]["version"])
PY
)"

# Ordre de publication.
#  1. cœur (forge-mvc) : impératif en premier, les opt-ins déclarent
#     `forge-mvc>=<version>`.
#  2. backends de base de données, mariadb en tête (le squelette l'épingle par
#     défaut : sans lui, `forge new` casse).
#  3. tous les autres opt-ins, un par un.
CORE="forge-mvc"
BACKENDS_PRIORITAIRES="forge-mvc-mariadb forge-mvc-sqlite forge-mvc-postgres forge-mvc-mssql"

# Distributions restantes = tous les paquets sauf le cœur et les backends.
AUTRES=""
for d in "$ROOT"/packages/forge-mvc-*/; do
    name="$(basename "$d")"
    case " $BACKENDS_PRIORITAIRES " in *" $name "*) continue ;; esac
    AUTRES="$AUTRES $name"
done

ORDRE="$CORE $BACKENDS_PRIORITAIRES $AUTRES"

# nom PyPI (forge-mvc-x) -> préfixe de fichier wheel/sdist (forge_mvc_x)
_distprefix() { echo "$1" | tr '-' '_'; }

echo "=== Publication PyPI Forge $VERSION ==="
$UPLOAD && echo "Mode : --upload (PUBLICATION RÉELLE)" || echo "Mode : DRY-RUN (aucune publication ; relancer avec --upload)"
echo ""

# ── Build (cœur + tous les opt-ins) + twine check, seulement pour --upload ───
if $UPLOAD; then
    echo "-- Build des distributions (tools/release-build.sh) --"
    bash "$ROOT/tools/release-build.sh" >/tmp/publish_build.log 2>&1 || {
        echo "ÉCHEC du build (voir /tmp/publish_build.log)"; tail -15 /tmp/publish_build.log; exit 1;
    }
    echo "   dist/ : $(find "$DIST" -name '*.whl' | wc -l) wheels, $(find "$DIST" -name '*.tar.gz' | wc -l) sdists ; twine check OK"
    echo ""
fi

# ── Séquence d'upload ────────────────────────────────────────────────────────
i=0
for name in $ORDRE; do
    i=$((i + 1))
    pref="$(_distprefix "$name")"
    files=("$DIST/${pref}-${VERSION}"*.whl "$DIST/${pref}-${VERSION}"*.tar.gz)
    if $UPLOAD; then
        echo "== [$i] upload $name =="
        if ! twine upload --skip-existing "${files[@]}"; then
            echo ""
            echo ">>> Échec sur $name (probablement 429 : limite de création de nouveaux projets PyPI)."
            echo ">>> Attendez puis RELANCEZ 'bash tools/publish.sh --upload' : --skip-existing"
            echo ">>> sautera les paquets déjà publiés et reprendra à partir de $name."
            exit 2
        fi
    else
        echo "[$i] twine upload --skip-existing dist/${pref}-${VERSION}*"
    fi
done

echo ""
$UPLOAD && echo "Publication terminée : $i distributions traitées." \
        || echo "DRY-RUN terminé : $i distributions dans l'ordre ci-dessus. Lancez --upload pour publier."
