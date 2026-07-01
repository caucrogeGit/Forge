#!/usr/bin/env bash
# Reprise AUTOMATIQUE de la publication PyPI de Forge 1.0.0-rc.2.
#
# Installé en cron par l'agent (à la demande de l'utilisateur) pour reprendre la
# publication des paquets restants après un 429 (limite de création de nouveaux
# projets PyPI). Relance publish.sh --upload (idempotent, --skip-existing), puis
# vérifie l'état PyPI : quand les 26 distributions sont en 1.0.0rc2, la ligne
# cron s'auto-retire.
#
# Journal : /tmp/forge-rc2-publish-resume.log
# Retrait manuel : crontab -l | grep -v publish-rc2-resume.sh | crontab -
set -uo pipefail

REPO="/home/roger/Projets/Forge"
LOG="/tmp/forge-rc2-publish-resume.log"
cd "$REPO" || { echo "$(date -Iseconds) : repo introuvable" >>"$LOG"; exit 1; }

# cron a un PATH minimal : activer le venv du projet (twine, python, build...).
if [ -f "$REPO/.venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source "$REPO/.venv/bin/activate"
fi

echo "===== $(date -Iseconds) : reprise publication rc2 =====" >>"$LOG"
bash tools/publish.sh --upload >>"$LOG" 2>&1

MISSING="$(python3 - <<'PY'
import json, urllib.request, pathlib, tomllib
version = tomllib.loads(pathlib.Path("pyproject.toml").read_text())["project"]["version"]
names = ["forge-mvc"] + sorted(p.name for p in pathlib.Path("packages").glob("forge-mvc-*"))
missing = []
for n in names:
    try:
        with urllib.request.urlopen(f"https://pypi.org/pypi/{n}/json", timeout=20) as r:
            if version not in json.load(r).get("releases", {}):
                missing.append(n)
    except Exception:
        missing.append(n)
print(" ".join(missing))
PY
)"

if [ -z "$MISSING" ]; then
    echo "$(date -Iseconds) : TOUT PUBLIÉ en 1.0.0rc2 -> retrait du cron de reprise." >>"$LOG"
    crontab -l 2>/dev/null | grep -v 'publish-rc2-resume.sh' | crontab -
else
    echo "$(date -Iseconds) : restent : $MISSING (nouvelle tentative à la prochaine occurrence cron)." >>"$LOG"
fi
