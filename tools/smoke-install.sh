#!/usr/bin/env bash
# SMOKE-INSTALL-VIERGE-001 — Preuve d'installation en environnement vierge.
#
# Prouve que le parcours réel d'un nouvel utilisateur aboutit :
#
#     forge new <projet>  ->  pip install -r requirements.txt  ->  forge utilisable
#
# Les paquets Forge sont résolus depuis des WHEELS CONSTRUITES LOCALEMENT
# (--find-links sur un wheelhouse temporaire), donc le smoke est INDÉPENDANT
# de la publication PyPI des paquets Forge. C'est le garde-fou qui aurait
# attrapé l'absence de forge-mvc-mariadb sur PyPI (audit RC1).
#
# Réseau : requis uniquement pour les dépendances tierces (Jinja2, argon2,
# jsonschema, connecteur de base de données...), jamais pour les paquets Forge.
#
# Usage :
#     bash tools/smoke-install.sh [--keep]
#
#   --keep   conserve le dossier de travail temporaire (débogage).
#
# Code de sortie : 0 si le parcours complet aboutit, non nul sinon.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
KEEP=0
[ "${1:-}" = "--keep" ] && KEEP=1

WORK="$(mktemp -d)"
WHEELHOUSE="$WORK/wheelhouse"
mkdir -p "$WHEELHOUSE"
cleanup() { [ "$KEEP" -eq 1 ] || rm -rf "$WORK"; }
trap cleanup EXIT

log()  { printf '\n\033[1m== %s ==\033[0m\n' "$*"; }
fail() { printf '\n\033[31mSMOKE INSTALL ÉCHEC : %s\033[0m\n' "$*" >&2; exit 1; }

cd "$REPO_ROOT"

VERSION="$("$PYTHON_BIN" - <<'PY'
import tomllib, pathlib
print(tomllib.loads(pathlib.Path("pyproject.toml").read_text())["project"]["version"])
PY
)"
log "Cible : forge-mvc == $VERSION"

# ── 1. Construire les wheels Forge nécessaires au squelette ──────────────────
# RELEASE-SMOKE-INSTALL-PATH-001 : le squelette vit à la racine depuis
# l'ADR-065. Le chemin `cli/skeleton/` d'avant n'existait plus, et le script
# échouait donc dès sa première vérification, sans jamais rien fumer.
SKEL_REQ="skeleton/data/requirements.txt"
[ -f "$SKEL_REQ" ] || fail "squelette introuvable : $SKEL_REQ"

# `--no-isolation` réutilise l'arbre `build/` du dépôt, et setuptools n'y
# recopie que ce qui a changé de date : une donnée du squelette supprimée ou
# réécrite y survit. Mesuré, la wheel embarquait ainsi un `requirements.txt`
# de squelette périmé qui épinglait encore un backend BDD, et le projet généré
# naissait donc avec un backend que l'ADR-060 lui interdit. Le smoke validait
# une wheel que personne n'aurait publiée. `release-build.sh` nettoie déjà :
# le smoke doit nettoyer de même, sinon il ne fume pas la même chose.
log "Nettoyage de l'arbre de construction (sinon la wheel embarque du périmé)"
rm -rf "$REPO_ROOT/build" "$REPO_ROOT"/*.egg-info
find packages -maxdepth 2 -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true

log "Construction des wheels (cœur + paquets épinglés et documentés par le squelette)"
"$PYTHON_BIN" -m build --wheel --no-isolation -o "$WHEELHOUSE" . >/dev/null \
    || fail "build de la wheel cœur (forge-mvc) a échoué"

# Les opt-ins que le squelette nomme sont **documentés en commentaire**, pas
# épinglés : depuis l'ADR-060 et l'ADR-070, un projet neuf est livré sans
# backend ni moteur d'entités, et l'utilisateur choisit. Ne lire que les lignes
# épinglées revenait donc à ne fumer que le cœur, alors que le premier geste
# du parcours documenté est justement un `pip install forge-mvc-<...>`.
mapfile -t SKEL_PKGS < <(grep -oE 'forge-mvc-[a-z0-9-]+' "$SKEL_REQ" | sort -u || true)
[ "${#SKEL_PKGS[@]}" -gt 0 ] \
    || fail "aucun opt-in nommé par $SKEL_REQ : le relevé du squelette a changé de forme"
for pkg in "${SKEL_PKGS[@]}"; do
    dir="packages/$pkg"
    [ -f "$dir/pyproject.toml" ] \
        || fail "le squelette nomme '$pkg' mais packages/$pkg/pyproject.toml est absent"
    "$PYTHON_BIN" -m build --wheel --no-isolation -o "$WHEELHOUSE" "$dir" >/dev/null \
        || fail "build de la wheel $pkg a échoué"
done
log "Wheels construites : $(find "$WHEELHOUSE" -name '*.whl' | wc -l) (${#SKEL_PKGS[@]} opt-in(s) du squelette)"

# ── 2. Environnement vierge + installation du CLI depuis le wheelhouse ───────
VENV="$WORK/venv"
"$PYTHON_BIN" -m venv "$VENV"
"$VENV/bin/pip" install -q --upgrade pip
# La wheel est désignée par son CHEMIN, pas par son nom. `--find-links` laissait
# pip choisir entre la wheel locale et celle déjà publiée sur PyPI, qui porte le
# même numéro tant que la version n'est pas bumpée : le smoke fumait alors la
# version publiée le mois précédent au lieu de celle qu'on s'apprête à publier.
CORE_WHL="$(find "$WHEELHOUSE" -maxdepth 1 -name 'forge_mvc-*.whl' | head -1)"
[ -n "$CORE_WHL" ] || fail "wheel du cœur introuvable dans le wheelhouse"
"$VENV/bin/pip" install -q "$CORE_WHL" \
    || fail "installation de $CORE_WHL a échoué"
"$VENV/bin/forge" --version >/dev/null \
    || fail "la commande 'forge' est indisponible après installation"
log "CLI installé : $("$VENV/bin/forge" --version 2>&1 | head -1)"

# ── 3. forge new en dossier vierge, dépendances résolues via le wheelhouse ───
PROJ_DIR="$WORK/projects"
mkdir -p "$PROJ_DIR"
# PIP_FIND_LINKS est hérité par le `pip install -r requirements.txt` que
# `forge new` lance dans le venv du projet : c'est l'étape qui casse si un
# paquet épinglé n'est pas résolvable.
export PIP_FIND_LINKS="$WHEELHOUSE"
log "forge new SmokeDemo (pip du projet résolu via le wheelhouse local)"
( cd "$PROJ_DIR" && "$VENV/bin/forge" new SmokeDemo --profile minimal ) \
    || fail "forge new a échoué (installation des dépendances du projet généré)"

# ── 4. Smoke du projet généré ────────────────────────────────────────────────
PROJ="$PROJ_DIR/SmokeDemo"
# Le projet doit être né du squelette de CE dépôt. Sans ce contrôle, une wheel
# publiée qui se glisse dans la résolution passe inaperçue, et le smoke valide
# un squelette que le dépôt ne contient plus : c'est exactement ce qui est
# arrivé, le projet naissant avec un backend BDD épinglé que l'ADR-060 interdit.
if ! diff -q <(grep -vE '^\s*(#|$)' "$SKEL_REQ") \
             <(grep -vE '^\s*(#|$)' "$PROJ/requirements.txt") >/dev/null; then
    fail "le requirements.txt généré diffère du squelette du dépôt : le projet vient d'une autre version de Forge"
fi
[ -d "$PROJ/.venv" ] || fail "le projet généré n'a pas de venv (.venv)"
[ -f "$PROJ/app.py" ] || fail "le projet généré n'a pas de point d'entrée app.py"
"$PROJ/.venv/bin/forge" --version >/dev/null \
    || fail "'forge' indisponible dans le venv du projet généré"
log "Projet généré opérationnel : $("$PROJ/.venv/bin/forge" --version 2>&1 | head -1)"

# ── 5. Le premier geste du parcours documenté ────────────────────────────────
# Le squelette dit à l'utilisateur d'installer un moteur d'entités et UN
# backend. Construire leurs wheels ne prouve rien ; le parcours se fume en
# installant vraiment.
#
# Un seul backend est installé : l'ADR-054 les veut mutuellement exclusifs, et
# les empiler ferait échouer la résolution que ce smoke est censé prouver. On
# prend SQLite, le seul qui ne demande ni serveur ni bibliothèque système, donc
# le seul dont l'échec désignerait Forge et non la machine.
for pkg in "${SKEL_PKGS[@]}"; do
    # Wheel désignée par son chemin, pour la même raison que le cœur : à
    # numéro égal, `--find-links` peut préférer la version déjà publiée.
    whl="$(find "$WHEELHOUSE" -maxdepth 1 -name "${pkg//-/_}-*.whl" | head -1)"
    [ -n "$whl" ] || fail "wheel de '$pkg' introuvable dans le wheelhouse"
    case "$pkg" in
        forge-mvc-mariadb|forge-mvc-postgres|forge-mvc-mssql)
            # Résolution prouvée sans installer : leurs pilotes exigent des
            # en-têtes système dont l'absence ne dirait rien sur Forge.
            "$PROJ/.venv/bin/pip" install -q --dry-run "$whl" >/dev/null \
                || fail "le squelette documente '$pkg' mais sa wheel ne se résout pas"
            ;;
        *)
            "$PROJ/.venv/bin/pip" install -q "$whl" \
                || fail "le squelette documente '$pkg' mais son installation échoue"
            ;;
    esac
done
"$PROJ/.venv/bin/forge" --version >/dev/null \
    || fail "'forge' est cassé après installation des opt-ins documentés"
# Le backend installé doit être celui que le cœur résout, sans ambiguïté.
"$PROJ/.venv/bin/python" -c "
from core.database.backend import get_backend
assert get_backend().name == 'sqlite', get_backend().name
" || fail "le backend documenté ne se résout pas dans le projet généré"
log "Parcours documenté fumé : moteur d'entités + backend SQLite résolus"

printf '\n\033[32mSMOKE INSTALL OK\033[0m — forge new s'"'"'installe et démarre depuis les wheels locales.\n'
