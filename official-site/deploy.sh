#!/usr/bin/env bash
# official-site/deploy.sh — publication de forgemvc.com (ADR-045)
#
# Build le site MkDocs canonique de Forge (mkdocs build --strict) et le déploie
# sur la VM forge-web. Le site est servi DIRECTEMENT à la racine du domaine :
# la landing (docs/index.html, ADR-044) est l'accueil, les pages de doc sont à
# /install/, /reference/, etc. Il n'y a plus d'import ni d'assemblage : la
# source est docs/ de ce dépôt.
#
# SÉCURITÉ (anti-incident beta12) :
#   - DRY_RUN=1 PAR DÉFAUT : aucune écriture sur la VM sans action explicite ;
#   - le mode réel exige DRY_RUN=0 ET une confirmation interactive « DEPLOY » ;
#   - backup distant daté avant toute bascule ; bascule via staging vérifié.
#
# Usage :
#   bash official-site/deploy.sh                 # dry-run (défaut) : build + plan
#   DRY_RUN=0 bash official-site/deploy.sh        # déploiement réel (avec confirmation)
#
# Variables surchargeables :
#   REMOTE_HOST, REMOTE_CURRENT, REMOTE_BACKUPS, REMOTE_STAGE
#   FORGE_DEPLOY_YES=1  pour sauter la confirmation interactive (CI).

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REMOTE_HOST="${REMOTE_HOST:-roger@192.168.1.98}"
REMOTE_CURRENT="${REMOTE_CURRENT:-/srv/forge-web/current}"
REMOTE_BACKUPS="${REMOTE_BACKUPS:-/srv/forge-web/backups}"
REMOTE_STAGE="${REMOTE_STAGE:-/tmp/forge-web-deploy-staging}"
DRY_RUN="${DRY_RUN:-1}"
FORGE_DEPLOY_YES="${FORGE_DEPLOY_YES:-0}"

LOCK_FILE="/tmp/forge-web-deploy.lock"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
REMOTE_BACKUP_PATH="${REMOTE_BACKUPS}/current-${TIMESTAMP}"

# Pages garanties par MkDocs (vérifiées dans staging puis current).
KEY_PAGES=(
  "index.html"
  "sitemap.xml"
  "search/search_index.json"
  "reference/cli-commands/index.html"
)

cd "${REPO_ROOT}"

# ── Lock anti-concurrence ─────────────────────────────────────────────────────

cleanup_lock() {
  if [[ -f "${LOCK_FILE}" ]] && [[ "$(cat "${LOCK_FILE}" 2>/dev/null || true)" == "$$" ]]; then
    rm -f "${LOCK_FILE}"
  fi
}
trap cleanup_lock EXIT INT TERM

if [[ -f "${LOCK_FILE}" ]]; then
  echo "ERREUR : lock présent (${LOCK_FILE}). Un déploiement est déjà en cours." >&2
  exit 1
fi
echo "$$" > "${LOCK_FILE}"

# ── Bandeau ───────────────────────────────────────────────────────────────────

echo "============================================================"
echo "Publication forgemvc.com (ADR-045)"
echo "============================================================"
echo "Dépôt            : ${REPO_ROOT}"
echo "Cible SSH        : ${REMOTE_HOST}"
echo "Current distant  : ${REMOTE_CURRENT}"
echo "Backups distants : ${REMOTE_BACKUPS}"
echo "Staging distant  : ${REMOTE_STAGE}"
echo "Mode             : $([[ "${DRY_RUN}" == "1" ]] && echo "DRY-RUN" || echo "DÉPLOIEMENT RÉEL")"
echo "Timestamp        : ${TIMESTAMP}"
echo

# ── [1] Pré-vol : dépôt propre sur main ───────────────────────────────────────

echo "[1/8] Vérification du dépôt"
BRANCH="$(git -C "${REPO_ROOT}" branch --show-current)"
if [[ "${BRANCH}" != "main" ]]; then
  echo "ERREUR : le dépôt n'est pas sur main (branche : ${BRANCH})." >&2
  exit 1
fi
if [[ -n "$(git -C "${REPO_ROOT}" status --porcelain)" ]]; then
  echo "ERREUR : le dépôt contient des modifications non committées." >&2
  exit 1
fi
COMMIT="$(git -C "${REPO_ROOT}" rev-parse HEAD)"
echo "  OK main, propre, commit ${COMMIT:0:12}"

# ── [2] Build MkDocs strict ───────────────────────────────────────────────────

echo "[2/8] Build du site (mkdocs build --strict)"
mkdocs build --strict
if [[ ! -f site/index.html ]]; then
  echo "ERREUR : site/index.html absent après build." >&2
  exit 1
fi
SITE_FILES="$(find site -type f | wc -l)"
SITE_SIZE="$(du -sh site | cut -f1)"
echo "  OK site construit (${SITE_FILES} fichiers, ${SITE_SIZE})."

# ── [3] Pages clés présentes localement ───────────────────────────────────────

echo "[3/8] Vérification des pages clés locales"
for p in "${KEY_PAGES[@]}"; do
  [[ -f "site/${p}" ]] && echo "  OK site/${p}" || { echo "  KO site/${p} (manquant)" >&2; exit 1; }
done

# ── [4] Bascule dry-run / réel ────────────────────────────────────────────────

if [[ "${DRY_RUN}" == "1" ]]; then
  echo
  echo "============================================================"
  echo "DRY-RUN : aucune écriture sur la VM."
  echo "En mode réel (DRY_RUN=0), le script ferait :"
  echo "  - backup distant      : ${REMOTE_BACKUP_PATH}"
  echo "  - rsync site/ -> staging ${REMOTE_HOST}:${REMOTE_STAGE}"
  echo "  - vérification des pages clés dans staging"
  echo "  - bascule staging -> ${REMOTE_CURRENT}"
  echo "  - vérification des pages clés dans current"
  echo
  echo "Pour déployer réellement :"
  echo "  DRY_RUN=0 bash official-site/deploy.sh"
  echo "============================================================"
  exit 0
fi

# ── Confirmation explicite (anti-footgun) ─────────────────────────────────────

if [[ "${FORGE_DEPLOY_YES}" != "1" ]]; then
  echo
  echo "ATTENTION : déploiement RÉEL vers ${REMOTE_HOST}:${REMOTE_CURRENT}."
  read -r -p "Tape exactement DEPLOY pour confirmer : " answer
  if [[ "${answer}" != "DEPLOY" ]]; then
    echo "Annulé (confirmation absente)." >&2
    exit 1
  fi
fi

# ── [5] Backup distant ────────────────────────────────────────────────────────

echo "[5/8] Backup distant de l'état courant"
ssh "${REMOTE_HOST}" "mkdir -p '${REMOTE_BACKUPS}'"
if ssh "${REMOTE_HOST}" "[ -d '${REMOTE_CURRENT}' ]"; then
  ssh "${REMOTE_HOST}" "cp -a '${REMOTE_CURRENT}' '${REMOTE_BACKUP_PATH}'"
  echo "  OK backup : ${REMOTE_BACKUP_PATH}"
else
  echo "  Note : ${REMOTE_CURRENT} inexistant (premier déploiement)."
  REMOTE_BACKUP_PATH="(aucun, premier déploiement)"
fi

# ── [6] Copie vers staging ────────────────────────────────────────────────────

echo "[6/8] Copie vers le staging distant"
ssh "${REMOTE_HOST}" "rm -rf '${REMOTE_STAGE}' && mkdir -p '${REMOTE_STAGE}'"
rsync -avz --delete site/ "${REMOTE_HOST}:${REMOTE_STAGE}/"
echo "  OK staging peuplé."

# ── [7] Vérification staging puis bascule ─────────────────────────────────────

echo "[7/8] Vérification des pages clés dans staging"
for p in "${KEY_PAGES[@]}"; do
  ssh "${REMOTE_HOST}" "[ -f '${REMOTE_STAGE}/${p}' ]" \
    && echo "  OK ${p}" \
    || { echo "  KO ${REMOTE_STAGE}/${p} absent — bascule annulée." >&2; exit 1; }
done
ssh "${REMOTE_HOST}" "mkdir -p '${REMOTE_CURRENT}' && rsync -a --delete '${REMOTE_STAGE}/' '${REMOTE_CURRENT}/'"
echo "  OK bascule staging -> current."

# ── [8] Vérification finale dans current ──────────────────────────────────────

echo "[8/8] Vérification des pages clés dans current"
for p in "${KEY_PAGES[@]}"; do
  ssh "${REMOTE_HOST}" "[ -f '${REMOTE_CURRENT}/${p}' ]" \
    && echo "  OK ${p}" \
    || { echo "  KO ${REMOTE_CURRENT}/${p} absent après bascule." >&2; exit 1; }
done

echo
echo "============================================================"
echo "Déploiement terminé — commit ${COMMIT:0:12}"
echo "  Backup  : ${REMOTE_BACKUP_PATH}"
echo "  Current : ${REMOTE_HOST}:${REMOTE_CURRENT}"
echo "============================================================"
