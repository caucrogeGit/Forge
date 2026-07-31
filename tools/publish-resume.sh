#!/usr/bin/env bash
# tools/publish-resume.sh — reprise AUTOMATIQUE d'une publication PyPI de Forge.
#
# PyPI limite la CRÉATION de nouveaux projets. Une release qui en introduit
# plusieurs se heurte donc à un 429 en cours de route, et il faut relancer
# `publish.sh --upload` toutes les demi-heures jusqu'à ce que tout passe.
# Ce script fait ce guet à la place de l'humain, posé en cron.
#
# `publish.sh` est idempotent (`twine upload --skip-existing`) : relancer ne
# renvoie jamais ce qui est déjà publié. Quand la version du dépôt est servie
# par TOUTES les distributions, ce script retire lui-même sa ligne de cron.
#
# La version n'est écrite nulle part ici : elle est lue dans `pyproject.toml`,
# seule source de vérité. Le script sert donc toutes les releases à venir, sans
# édition. Sa version rc2 nommait la sienne dans son propre nom, son journal et
# ses messages (RELEASE-PUBLISH-RESUME-GENERALIZE-001).
#
# Pose en cron, toutes les 30 minutes :
#   ( crontab -l 2>/dev/null; \
#     echo "*/30 * * * * bash /home/roger/Projets/Forge/tools/publish-resume.sh" ) | crontab -
#
# Journal : /tmp/forge-publish-resume.log
# Retrait manuel : crontab -l | grep -v publish-resume.sh | crontab -
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG="/tmp/forge-publish-resume.log"
cd "$REPO" || { echo "$(date -Iseconds) : dépôt introuvable" >>"$LOG"; exit 1; }

# cron a un PATH minimal : activer le venv du projet (twine, python, build...).
if [ -f "$REPO/.venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source "$REPO/.venv/bin/activate"
fi
PYTHON_BIN="$REPO/.venv/bin/python"
[ -x "$PYTHON_BIN" ] || PYTHON_BIN="python3"

VERSION="$("$PYTHON_BIN" - <<'PY'
import pathlib
import tomllib

print(tomllib.loads(pathlib.Path("pyproject.toml").read_text())["project"]["version"])
PY
)"

if [ -z "$VERSION" ]; then
    echo "$(date -Iseconds) : version illisible dans pyproject.toml, abandon." >>"$LOG"
    exit 1
fi

echo "===== $(date -Iseconds) : reprise publication $VERSION =====" >>"$LOG"
bash tools/publish.sh --upload >>"$LOG" 2>&1

# Le verdict vient du garde de complétude, pas d'une seconde lecture de PyPI
# écrite ici : ce script en portait une, forcément divergente (elle comptait une
# version retirée comme publiée, et déduisait les noms de distribution des noms
# de dossier). Une règle recopiée finit incomplète (CRUD-CSV-ESCAPE-CORE-001).
if "$PYTHON_BIN" tools/check_pypi_completeness.py --version "$VERSION" >>"$LOG" 2>&1; then
    echo "$(date -Iseconds) : TOUT PUBLIÉ en $VERSION -> retrait du cron de reprise." >>"$LOG"
    crontab -l 2>/dev/null | grep -v 'publish-resume.sh' | crontab -
else
    echo "$(date -Iseconds) : publication encore incomplète (détail ci-dessus) ; nouvelle tentative à la prochaine occurrence cron." >>"$LOG"
fi
