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
# On NE s'arrête PAS au premier échec : un 429 sur un NOUVEAU projet ne doit pas
# empêcher de publier les paquets existants (mise à jour de version, sans 429)
# situés plus loin. Les échecs sont tracés et rejoués au prochain lancement
# (--skip-existing).
i=0
FAILED=""
for name in $ORDRE; do
    i=$((i + 1))
    pref="$(_distprefix "$name")"
    files=("$DIST/${pref}-${VERSION}"*.whl "$DIST/${pref}-${VERSION}"*.tar.gz)
    if $UPLOAD; then
        echo "== [$i] upload $name =="
        if ! twine upload --skip-existing "${files[@]}"; then
            echo ">>> Échec sur $name (probablement 429 : limite de création de nouveaux projets PyPI). On continue."
            FAILED="$FAILED $name"
        fi
    else
        echo "[$i] twine upload --skip-existing dist/${pref}-${VERSION}*"
    fi
done

echo ""
if ! $UPLOAD; then
    echo "DRY-RUN terminé : $i distributions dans l'ordre ci-dessus. Lancez --upload pour publier."
elif [ -n "$FAILED" ]; then
    echo "Publication partielle. Échecs (probable 429 sur nouveaux projets) :$FAILED"
    echo "Attendez (~20-30 min, la fenêtre de création de projets PyPI se réinitialise) puis"
    echo "RELANCEZ 'bash tools/publish.sh --upload' : --skip-existing saute les publiés et reprend les restants."
    exit 2
else
    echo "Publication terminée : $i distributions traitées, aucune en échec."
    # « twine n'a pas protesté » n'est pas « PyPI sert la version ». Le garde
    # de complétude tranche en interrogeant PyPI, distribution par distribution.
    # Sans cet appel, la vérification dépendait de la mémoire de qui publie :
    # aucune documentation ne porte la séquence
    # (RELEASE-PUBLISH-RESUME-GENERALIZE-001).
    echo ""
    echo "-- Vérification : PyPI sert-il bien $VERSION partout ? --"
    _VERIFIE=false
    for _essai in 1 2 3; do
        if python3 "$ROOT/tools/check_pypi_completeness.py" --version "$VERSION"; then
            _VERIFIE=true
            break
        fi
        # L'index met parfois quelques secondes à refléter un envoi : conclure
        # au premier refus ferait douter de son propre travail celui qui vient
        # de publier.
        [ "$_essai" -lt 3 ] && { echo "   (nouvel essai dans 15 s)"; sleep 15; }
    done
    if ! $_VERIFIE; then
        echo ""
        echo "PUBLICATION INCOMPLÈTE : PyPI ne sert pas $VERSION pour toutes les distributions."
        echo "Relancez 'bash tools/publish.sh --upload' (--skip-existing saute les publiés),"
        echo "ou posez la reprise automatique : bash tools/publish-resume.sh en cron."
        exit 3
    fi
fi
