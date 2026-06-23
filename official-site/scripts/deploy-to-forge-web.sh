#!/usr/bin/env bash
set -euo pipefail

REMOTE_HOST="${REMOTE_HOST:-roger@192.168.1.98}"
REMOTE_STAGE="${REMOTE_STAGE:-/tmp/forge-web-deploy-staging}"
DRY_RUN="${DRY_RUN:-1}"

if [[ ! -f dist/index.html ]]; then
  echo "ERREUR: dist/index.html absent. Lance d'abord scripts/build-site.sh."
  exit 1
fi

if [[ ! -f dist/docs/index.html ]]; then
  echo "ERREUR: dist/docs/index.html absent. Lance d'abord scripts/build-site.sh."
  exit 1
fi

echo "Cible SSH        : ${REMOTE_HOST}"
echo "Staging distant  : ${REMOTE_STAGE}"
echo "Source locale    : dist/"
echo "Dry-run          : ${DRY_RUN}"

ssh "${REMOTE_HOST}" "rm -rf '${REMOTE_STAGE}' && mkdir -p '${REMOTE_STAGE}'"

if [[ "${DRY_RUN}" == "1" ]]; then
  echo
  echo "Mode dry-run actif : aucun fichier n'est réellement copié."
  rsync -avzn --delete dist/ "${REMOTE_HOST}:${REMOTE_STAGE}/"
else
  echo
  echo "Mode réel : copie vers le staging distant."
  rsync -avz --delete dist/ "${REMOTE_HOST}:${REMOTE_STAGE}/"
fi

echo
echo "Ce script ne remplace pas /srv/forge-web/current."
echo "Le remplacement contrôlé sera fait dans FW-DEPLOY-GO-001."
