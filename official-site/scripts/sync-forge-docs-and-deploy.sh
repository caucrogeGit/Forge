#!/usr/bin/env bash
# sync-forge-docs-and-deploy.sh — OFFICIAL-SITE-DOCS-SYNC-DEPLOY-SCRIPT-001
#
# Pipeline manuel unique : importe la documentation Forge canonique,
# reconstruit le site officiel, lance les validations, puis (en mode réel)
# pousse le site vers la VM forge-web.
#
# Le commit/push automatique et le déclenchement par timer systemd seront
# traités dans des tickets séparés. Ce script reste strictement manuel.
#
# Usage :
#   bash scripts/sync-forge-docs-and-deploy.sh             # dry-run (défaut)
#   DRY_RUN=0 bash scripts/sync-forge-docs-and-deploy.sh   # déploiement réel

set -euo pipefail

# ── Variables configurables ──────────────────────────────────────────────────

# ADR-045 : official-site/ vit dans le dépôt Forge. La racine Forge est le
# parent de official-site/ (deux niveaux au-dessus de ce script).
FORGE_ROOT="${FORGE_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
REMOTE_HOST="${REMOTE_HOST:-roger@192.168.1.98}"
REMOTE_CURRENT="${REMOTE_CURRENT:-/srv/forge-web/current}"
REMOTE_BACKUPS="${REMOTE_BACKUPS:-/srv/forge-web/backups}"
REMOTE_STAGE="${REMOTE_STAGE:-/tmp/forge-web-deploy-staging}"
DRY_RUN="${DRY_RUN:-1}"

LOCK_FILE="/tmp/forge-official-site-sync-deploy.lock"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
REMOTE_BACKUP_PATH="${REMOTE_BACKUPS}/current-${TIMESTAMP}"

# Pages clés à vérifier dans staging puis dans current.
KEY_PAGES=(
  "index.html"
  "docs/index.html"
  "docs/forge/index.html"
  "docs/forge/starters/welcome-forge/debutant/query-params/index.html"
  "docs/forge/starters/welcome-forge/debutant/server-validation/index.html"
  "docs/forge/entities/slugs/index.html"
)

# ── Lock anti-concurrence ─────────────────────────────────────────────────────

cleanup_lock() {
  if [[ -f "${LOCK_FILE}" ]]; then
    local owner
    owner="$(cat "${LOCK_FILE}" 2>/dev/null || true)"
    if [[ "${owner}" == "$$" ]]; then
      rm -f "${LOCK_FILE}"
    fi
  fi
}

trap cleanup_lock EXIT INT TERM

if [[ -f "${LOCK_FILE}" ]]; then
  echo "ERREUR : lock présent (${LOCK_FILE})." >&2
  echo "Une autre exécution est en cours ou un précédent run s'est interrompu." >&2
  exit 1
fi
echo "$$" > "${LOCK_FILE}"

# ── En-tête ───────────────────────────────────────────────────────────────────

# Se positionner à la racine de Forge-official-site.
cd "$(dirname "$0")/.."
FORGEWEB_ROOT="$(pwd)"

echo "============================================================"
echo "Forge docs sync & deploy"
echo "============================================================"
echo "Forge source     : ${FORGE_ROOT}"
echo "Forge-web local  : ${FORGEWEB_ROOT}"
echo "Cible SSH        : ${REMOTE_HOST}"
echo "Staging distant  : ${REMOTE_STAGE}"
echo "Current distant  : ${REMOTE_CURRENT}"
echo "Backups distants : ${REMOTE_BACKUPS}"
echo "Mode             : $([[ "${DRY_RUN}" == "1" ]] && echo "DRY-RUN" || echo "DEPLOY REEL")"
echo "Timestamp        : ${TIMESTAMP}"
echo

# ── Étape 1 — Vérifier le dépôt Forge source ─────────────────────────────────

echo "[1/12] Vérification du dépôt Forge source"

if [[ ! -d "${FORGE_ROOT}/.git" ]]; then
  echo "ERREUR : ${FORGE_ROOT} n'est pas un dépôt git." >&2
  exit 1
fi

FORGE_BRANCH="$(git -C "${FORGE_ROOT}" branch --show-current)"
if [[ "${FORGE_BRANCH}" != "main" ]]; then
  echo "ERREUR : ${FORGE_ROOT} n'est pas sur main (branche actuelle : ${FORGE_BRANCH})." >&2
  exit 1
fi

if [[ -n "$(git -C "${FORGE_ROOT}" status --porcelain)" ]]; then
  echo "ERREUR : ${FORGE_ROOT} contient des modifications non committées." >&2
  git -C "${FORGE_ROOT}" status --short >&2
  exit 1
fi

FORGE_COMMIT="$(git -C "${FORGE_ROOT}" rev-parse HEAD)"
echo "  OK ${FORGE_ROOT} sur main, propre, commit ${FORGE_COMMIT:0:12}"

# ── Étape 2 — Vérifier le dépôt Forge-official-site ──────────────────────────

echo "[2/12] Vérification du dépôt Forge-official-site"

FORGEWEB_BRANCH="$(git branch --show-current)"
if [[ "${FORGEWEB_BRANCH}" != "main" ]]; then
  echo "ERREUR : ${FORGEWEB_ROOT} n'est pas sur main (branche actuelle : ${FORGEWEB_BRANCH})." >&2
  exit 1
fi

FORGEWEB_DIRTY="$(
  git status --porcelain | awk '{print $NF}' \
    | grep -Ev '^(docs/forge/|scripts/sync-forge-docs-and-deploy\.sh$)' \
    || true
)"
if [[ -n "${FORGEWEB_DIRTY}" ]]; then
  echo "ERREUR : ${FORGEWEB_ROOT} contient des modifications non attendues." >&2
  echo "Le pré-vol tolère uniquement docs/forge/ (produit par l'import) et" >&2
  echo "scripts/sync-forge-docs-and-deploy.sh (le script lui-même)." >&2
  echo "Fichiers hors tolérance :" >&2
  echo "${FORGEWEB_DIRTY}" | sed 's/^/  /' >&2
  exit 1
fi

FORGEWEB_COMMIT="$(git rev-parse HEAD)"
echo "  OK ${FORGEWEB_ROOT} sur main, propre, commit ${FORGEWEB_COMMIT:0:12}"

# ── Étape 3 — Import de la documentation Forge ───────────────────────────────

echo "[3/12] Import de la documentation Forge"
python scripts/import_forge_docs.py
echo "  OK import terminé."

# ── Étape 4 — Vérification de la complétude de l'import ──────────────────────

echo "[4/12] Vérification de la complétude de l'import"
python - "${FORGE_ROOT}/docs" "${FORGEWEB_ROOT}/docs/forge" <<'PYCHECK'
import sys
from pathlib import Path

# Source unique de vérité pour les dossiers réellement importés : la whitelist
# de l'import. Les dossiers canoniques NON whitelistés (assets internes type
# docs/logos/, hors nav et non publiés) ne sont pas mirrorés — il ne faut donc
# pas les compter comme « manquants » ici, sinon le contrôle échoue à tort.
# cwd = racine du dépôt (le script y fait cd avant cette étape).
sys.path.insert(0, "scripts")
from import_forge_docs import WHITELISTED_SUBDIRS

source = Path(sys.argv[1])
dest = Path(sys.argv[2])

if not source.is_dir():
    print(f"ERREUR : source absente : {source}", file=sys.stderr)
    sys.exit(2)
if not dest.is_dir():
    print(f"ERREUR : destination absente : {dest}", file=sys.stderr)
    sys.exit(2)

def in_whitelist(rel: Path) -> bool:
    return len(rel.parts) > 1 and rel.parts[0] in WHITELISTED_SUBDIRS

# On ne compare que les .md vivant sous un sous-dossier whitelisté.
source_md = {
    p.relative_to(source)
    for p in source.rglob("*.md")
    if in_whitelist(p.relative_to(source))
}
dest_md = {p.relative_to(dest) for p in dest.rglob("*.md")}

missing = sorted(source_md - dest_md)
extras = sorted(dest_md - source_md)
allowed_extras = {Path("index.md")}
unexpected_extras = [p for p in extras if p not in allowed_extras]

print(f"  Source       : {len(source_md)} .md")
print(f"  Destination  : {len(dest_md)} .md")
print(f"  Manquants    : {len(missing)}")
print(f"  Extras       : {len(extras)} (autorisé : index.md)")

if missing:
    print("ERREUR : fichiers .md absents de docs/forge :", file=sys.stderr)
    for p in missing:
        print(f"  - {p}", file=sys.stderr)
    sys.exit(1)
if unexpected_extras:
    print("ERREUR : fichiers .md inattendus dans docs/forge :", file=sys.stderr)
    for p in unexpected_extras:
        print(f"  - {p}", file=sys.stderr)
    sys.exit(1)

print("  OK complétude vérifiée.")
PYCHECK

# ── Étape 5 — Build du site ──────────────────────────────────────────────────

echo "[5/12] Build du site officiel"
bash scripts/build-site.sh

if [[ ! -f dist/index.html ]]; then
  echo "ERREUR : dist/index.html absent après build." >&2
  exit 1
fi

DIST_FILE_COUNT="$(find dist -type f | wc -l)"
DIST_SIZE="$(du -sh dist | cut -f1)"
echo "  OK dist construit (${DIST_FILE_COUNT} fichiers, ${DIST_SIZE})."

# ── Étape 6 — Validations ────────────────────────────────────────────────────

echo "[6/12] Validations locales"

echo "  - check_no_github_pages_docs.py"
python scripts/check_no_github_pages_docs.py --quiet

echo "  - check_local_links.py"
if ! python scripts/check_local_links.py --quiet; then
  echo "ERREUR : liens locaux cassés détectés. Déploiement refusé." >&2
  exit 1
fi

echo "  - py_compile sur scripts/*.py"
python -m py_compile scripts/*.py

echo "  - bash -n sur scripts/*.sh"
for f in scripts/*.sh; do
  bash -n "${f}"
done

echo "  - git diff --check"
git diff --check

echo "  OK toutes les validations passent."

# ── Étape 7 — Bilan local et bascule dry-run/réel ────────────────────────────

echo "[7/12] Bilan local"
echo "  Forge source commit         : ${FORGE_COMMIT}"
echo "  Forge-official-site commit  : ${FORGEWEB_COMMIT}"
echo "  dist : ${DIST_FILE_COUNT} fichiers, ${DIST_SIZE}"

if [[ "${DRY_RUN}" == "1" ]]; then
  echo
  echo "============================================================"
  echo "Mode DRY-RUN : pas de copie sur la VM."
  echo "Les étapes suivantes seraient exécutées en mode réel :"
  echo "  - backup distant         : ${REMOTE_BACKUP_PATH}"
  echo "  - rsync vers staging     : ${REMOTE_HOST}:${REMOTE_STAGE}"
  echo "  - vérification pages clés dans staging"
  echo "  - bascule staging → ${REMOTE_CURRENT}"
  echo "  - vérification pages clés dans current"
  echo "============================================================"

  echo
  echo "Pages clés présentes localement dans dist/ :"
  for p in "${KEY_PAGES[@]}"; do
    if [[ -f "dist/${p}" ]]; then
      echo "  OK dist/${p}"
    else
      echo "  KO dist/${p} (manquant)"
    fi
  done

  echo
  echo "Pour déployer pour de vrai :"
  echo "  DRY_RUN=0 bash scripts/sync-forge-docs-and-deploy.sh"
  exit 0
fi

# ── À partir d'ici : mode réel ───────────────────────────────────────────────

echo "[8/12] Backup distant de l'état courant"
ssh "${REMOTE_HOST}" "mkdir -p '${REMOTE_BACKUPS}'"
if ssh "${REMOTE_HOST}" "[ -d '${REMOTE_CURRENT}' ]"; then
  ssh "${REMOTE_HOST}" "cp -a '${REMOTE_CURRENT}' '${REMOTE_BACKUP_PATH}'"
  echo "  OK backup créé : ${REMOTE_BACKUP_PATH}"
else
  echo "  Note : ${REMOTE_CURRENT} inexistant, premier déploiement. Pas de backup."
  REMOTE_BACKUP_PATH="(aucun, premier déploiement)"
fi

# ── Étape 9 — Préparation et copie vers staging distant ──────────────────────

echo "[9/12] Préparation du staging distant et copie"
ssh "${REMOTE_HOST}" "rm -rf '${REMOTE_STAGE}' && mkdir -p '${REMOTE_STAGE}'"
rsync -avz --delete dist/ "${REMOTE_HOST}:${REMOTE_STAGE}/"
echo "  OK staging peuplé : ${REMOTE_HOST}:${REMOTE_STAGE}"

# ── Étape 10 — Vérification des pages clés dans le staging ───────────────────

echo "[10/12] Vérification des pages clés dans le staging"
MISSING_KEY=0
for p in "${KEY_PAGES[@]}"; do
  if ssh "${REMOTE_HOST}" "[ -f '${REMOTE_STAGE}/${p}' ]"; then
    echo "  OK ${REMOTE_STAGE}/${p}"
  else
    echo "  KO ${REMOTE_STAGE}/${p} (absent)"
    MISSING_KEY=1
  fi
done
if [[ "${MISSING_KEY}" == "1" ]]; then
  echo "ERREUR : page(s) clé(s) absente(s) du staging. Bascule annulée." >&2
  exit 1
fi

# ── Étape 11 — Bascule staging → current ─────────────────────────────────────

echo "[11/12] Synchronisation staging → current"
ssh "${REMOTE_HOST}" "test -d '${REMOTE_CURRENT}'"
ssh "${REMOTE_HOST}" "rsync -a --delete '${REMOTE_STAGE}/' '${REMOTE_CURRENT}/'"
echo "  OK contenu de ${REMOTE_CURRENT} mis à jour."

# ── Étape 12 — Vérification des pages clés dans current ──────────────────────

echo "[12/12] Vérification des pages clés dans current"
MISSING_CURRENT=0
for p in "${KEY_PAGES[@]}"; do
  if ssh "${REMOTE_HOST}" "[ -f '${REMOTE_CURRENT}/${p}' ]"; then
    echo "  OK ${REMOTE_CURRENT}/${p}"
  else
    echo "  KO ${REMOTE_CURRENT}/${p} (absent)"
    MISSING_CURRENT=1
  fi
done
if [[ "${MISSING_CURRENT}" == "1" ]]; then
  echo "ERREUR : page(s) clé(s) absente(s) de current après bascule." >&2
  exit 1
fi

# ── Résumé final ─────────────────────────────────────────────────────────────

echo
echo "============================================================"
echo "Déploiement terminé"
echo "============================================================"
echo "  Forge source commit         : ${FORGE_COMMIT}"
echo "  Forge-official-site commit  : ${FORGEWEB_COMMIT}"
echo "  dist                        : ${DIST_FILE_COUNT} fichiers, ${DIST_SIZE}"
echo "  Backup distant              : ${REMOTE_BACKUP_PATH}"
echo "  Current                     : ${REMOTE_HOST}:${REMOTE_CURRENT}"
echo "  État                        : OK"
echo "============================================================"
