#!/usr/bin/env bash
# Validation pré-release Forge.
# Usage : bash tools/release-validate.sh [VERSION]
# Ex.   : bash tools/release-validate.sh 1.0.0-beta.9
#         bash tools/release-validate.sh 1.0.0b9
#
# Forge utilise deux formats équivalents pour la même release :
#   - SemVer public : 1.0.0-beta.9 (CHANGELOG, tags git, package.json, docs)
#   - PEP 440       : 1.0.0b9      (pyproject.toml, core/__init__.py, forge.py)
# Le script accepte l'un ou l'autre en entrée et normalise vers le format
# attendu de chaque source.
#
# Mode utilitaire (testabilité) :
#   bash tools/release-validate.sh --convert pep440   1.0.0-beta.9
#   bash tools/release-validate.sh --convert semver   1.0.0b9
#   bash tools/release-validate.sh --convert validate 1.0.0-beta.9
set -euo pipefail

# ── Helpers de conversion / validation de version ───────────────────────────
# Définis tôt pour être utilisables en mode --convert (test méta).

to_pep440() {
    # SemVer public -> PEP 440. Stable inchangé.
    #   1.0.0-alpha.N -> 1.0.0aN
    #   1.0.0-beta.N  -> 1.0.0bN
    #   1.0.0-rc.N    -> 1.0.0rcN
    printf '%s\n' "$1" \
        | sed -E 's/-alpha\.([0-9]+)$/a\1/; s/-beta\.([0-9]+)$/b\1/; s/-rc\.([0-9]+)$/rc\1/'
}

to_semver_public() {
    # PEP 440 -> SemVer public. Stable inchangé.
    # Ordre : `rc` traité avant `b` (sinon `b` matcherait la fin de `rc`).
    printf '%s\n' "$1" \
        | sed -E 's/rc([0-9]+)$/-rc.\1/; s/a([0-9]+)$/-alpha.\1/; s/b([0-9]+)$/-beta.\1/'
}

is_valid_version() {
    # Accepte SemVer public OU PEP 440 (sous-ensemble Forge).
    #   stable      : 1.0.0
    #   pre-release : 1.0.0-{alpha,beta,rc}.N (SemVer) ou 1.0.0{a,b,rc}N (PEP 440)
    local v="${1:-}"
    if [[ "$v" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-(alpha|beta|rc)\.[0-9]+)?$ ]]; then
        return 0
    fi
    if [[ "$v" =~ ^[0-9]+\.[0-9]+\.[0-9]+((a|b|rc)[0-9]+)?$ ]]; then
        return 0
    fi
    return 1
}

# ── Mode utilitaire --convert (testabilité, n'exécute pas la validation) ────
if [ "${1:-}" = "--convert" ]; then
    case "${2:-}" in
        pep440)   to_pep440 "${3:-}"; exit 0 ;;
        semver)   to_semver_public "${3:-}"; exit 0 ;;
        validate) is_valid_version "${3:-}" && exit 0 || exit 1 ;;
        *) echo "Usage: $0 --convert {pep440|semver|validate} VERSION" >&2 ; exit 2 ;;
    esac
fi

# RELEASE-VALIDATE-PACKAGES-001 — `--with-packages` (opt-in) ajoute le build
# de toutes les distributions (core + opt-ins) + twine check. Hors flag,
# comportement inchangé (on ne rallonge pas chaque run ; la CI build aussi).
WITH_PACKAGES=false
# SMOKE-INSTALL-VIERGE-001 — `--with-smoke` (opt-in) ajoute la preuve
# d'installation en environnement vierge (build wheels + forge new + install
# résolu via --find-links). Hors flag, comportement inchangé (le smoke est
# coûteux : venv jetable + forge new complet).
WITH_SMOKE=false
# RELEASE-VALIDATE-SKIPS-SILENCIEUX-001 — `--sans-serveurs` assume explicitement
# une validation qui n'exerce pas les tests d'intégration. Sans ce drapeau, le
# script exige les `FORGE_REQUIRE_*` : voir le contrôle plus bas.
SANS_SERVEURS=false
_ARGS=()
for _arg in "$@"; do
    case "$_arg" in
        --with-packages) WITH_PACKAGES=true ;;
        --with-smoke) WITH_SMOKE=true ;;
        --sans-serveurs) SANS_SERVEURS=true ;;
        *) _ARGS+=("$_arg") ;;
    esac
done
VERSION="${_ARGS[0]:-}"
PUBLIC_VERSION=""
PEP440_VERSION=""
ERRORS=0
WARNS=0

_ok()   { printf "[OK]    %s\n" "$1"; }
_warn() { printf "[WARN]  %s\n" "$1"; WARNS=$((WARNS+1)); }
_fail() { printf "[FAIL]  %s\n" "$1"; ERRORS=$((ERRORS+1)); }

# ── Interpréteur Python — RELEASE-VALIDATE-PATH-ROBUSTNESS-001 ───────────────
# Tous les appels Python du script (pytest, compileall, ruff, mkdocs,
# pip-audit) passent par "$PYTHON_BIN" -m … plutôt que par les binaires
# du PATH. Ainsi, lancer le script sans venv activé donne une erreur
# explicite « Python introuvable », plutôt qu'un cascadé `command not found`
# sur chaque outil. Configurable via la variable d'environnement
# `PYTHON=/chemin/vers/python`.
PYTHON_BIN="${PYTHON:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    printf "[FAIL]  Python introuvable : %s\n" "$PYTHON_BIN" >&2
    printf "         Définissez PYTHON=/chemin/vers/python ou activez votre environnement Python.\n" >&2
    exit 1
fi

# RELEASE-VALIDATE-INTERPRETER-001 — l'interpréteur doit être CELUI du projet.
# Vérifier qu'un `python3` existe ne prouve rien : il en existe un sur toute
# machine. Lancé sans venv actif, le script validait donc le Python du système,
# où ni Forge ni l'outillage ne sont installés. Mesuré sur une validation
# réelle : deux échecs sur trois étaient des faux positifs, un module d'opt-in
# et mkdocs déclarés absents alors qu'ils sont installés dans le venv.
# Le sens inverse est plus grave : un interpréteur portant une version ANCIENNE
# de Forge donnerait un feu vert sur autre chose que ce qu'on publie.
# La distribution INSTALLÉE, et non un simple `import core` : lancé depuis la
# racine du dépôt, `python -c` ajoute le répertoire courant au chemin, si bien
# que n'importe quel interpréteur importe `core` sans que Forge y soit installé.
_FORGE_INSTALLED="$("$PYTHON_BIN" -c 'import importlib.metadata as m;print(m.version("forge-mvc"))' 2>/dev/null || true)"
if [ -z "$_FORGE_INSTALLED" ]; then
    printf "[FAIL]  L'interpréteur %s n'a pas la distribution forge-mvc installée.\n" \
        "$(command -v "$PYTHON_BIN")" >&2
    printf "         Activez l'environnement du projet : source .venv/bin/activate\n" >&2
    printf "         ou désignez-le : PYTHON=.venv/bin/python bash tools/release-validate.sh ...\n" >&2
    exit 1
fi
_FORGE_REPO_VERSION="$(sed -n 's/^version = "\(.*\)"/\1/p' pyproject.toml | head -1)"
if [ -n "$_FORGE_REPO_VERSION" ] && [ "$_FORGE_INSTALLED" != "$_FORGE_REPO_VERSION" ]; then
    printf "[FAIL]  L'interpréteur %s porte forge-mvc %s, alors qu'on valide %s.\n" \
        "$(command -v "$PYTHON_BIN")" "$_FORGE_INSTALLED" "$_FORGE_REPO_VERSION" >&2
    printf "         La validation porterait sur une autre version que celle publiée.\n" >&2
    printf "         Réinstallez en éditable : pip install -e .\n" >&2
    exit 1
fi
for _outil in pytest mkdocs ruff; do
    if ! "$PYTHON_BIN" -c "import $_outil" >/dev/null 2>&1; then
        printf "[FAIL]  L'outil %s est absent de %s.\n" "$_outil" "$(command -v "$PYTHON_BIN")" >&2
        printf "         Installez les dépendances de développement, ou activez le venv du projet.\n" >&2
        exit 1
    fi
done
# RELEASE-VALIDATE-FAUX-POSITIFS-001 — importer `pytest` ne prouve pas qu'il
# DÉMARRE. `pytest.ini` impose `addopts = --strict-markers --dist loadfile -rs`,
# donc pytest-xdist est obligatoire : sans lui, pytest s'arrête sur
# « unrecognized arguments: --dist » et sort en 4, que le script rapportait
# comme un échec des tests. Mesuré sur une validation réelle, où la suite n'a
# jamais démarré alors que le rapport annonçait « Tests : échec ».
#
# Le contrôle lance une collecte réelle plutôt que d'ajouter `xdist` à la liste
# ci-dessus : il lit `pytest.ini` et vaut donc pour TOUT plugin exigé par les
# addopts, y compris ceux qu'on y ajoutera demain. Une liste d'imports écrite à
# la main dériverait de la configuration au premier changement.
_PYTEST_START="$("$PYTHON_BIN" -m pytest --collect-only -q tools 2>&1)" && _PYTEST_CODE=0 || _PYTEST_CODE=$?
# Codes acceptés : 0 (des tests collectés) et 5 (aucun, ce qui est le cas de
# `tools/`). Ce qu'on cherche est le code 4, « unrecognized arguments », seul
# signe que pytest n'a pas pu lire sa configuration. Confondre 5 avec un échec
# ferait refuser un environnement sain, et le contrôle négatif l'a montré.
case "$_PYTEST_CODE" in
    0|5) : ;;
    *)
        printf "[FAIL]  pytest ne démarre pas avec la configuration du dépôt (pytest.ini).\n" >&2
        printf "%s\n" "$_PYTEST_START" | head -5 | sed 's/^/         /' >&2
        printf "         Installez les dépendances de développement, ou activez le venv du projet.\n" >&2
        exit 1
        ;;
esac

echo "=== Validation pré-release Forge ${VERSION:-<version non fournie>} ==="
if $WITH_PACKAGES; then
    echo "Mode : --with-packages (build des distributions core + opt-ins + twine check)"
fi
if $WITH_SMOKE; then
    echo "Mode : --with-smoke (installation vierge : forge new depuis wheels locales)"
fi
echo ""

# ── 1. Version fournie ────────────────────────────────────────────────────────
if [ -z "$VERSION" ]; then
    _warn "Aucune version fournie en argument (ex : bash tools/release-validate.sh 1.0.0-beta.9)"
elif ! is_valid_version "$VERSION"; then
    _fail "Version '$VERSION' invalide. Formats acceptés :"
    _fail "  - SemVer public : 1.0.0, 1.0.0-alpha.N, 1.0.0-beta.N, 1.0.0-rc.N"
    _fail "  - PEP 440       : 1.0.0, 1.0.0aN, 1.0.0bN, 1.0.0rcN"
else
    PUBLIC_VERSION=$(to_semver_public "$VERSION")
    PEP440_VERSION=$(to_pep440 "$VERSION")
    if [ "$PUBLIC_VERSION" = "$PEP440_VERSION" ]; then
        _ok "Version cible : $VERSION (stable, même format SemVer/PEP 440)"
    else
        _ok "Version cible : $PUBLIC_VERSION (SemVer) ≡ $PEP440_VERSION (PEP 440)"
    fi
fi

# ── 2. Cohérence des versions (format PEP 440) ───────────────────────────────
if [ -n "$PEP440_VERSION" ]; then
    PYPROJECT_VER=$("$PYTHON_BIN" -c "
import tomllib, sys
with open('pyproject.toml', 'rb') as f:
    d = tomllib.load(f)
print(d['project']['version'])
" 2>/dev/null || echo "ERREUR")

    if [ "$PYPROJECT_VER" = "$PEP440_VERSION" ]; then
        _ok "pyproject.toml version = $PEP440_VERSION (PEP 440)"
    else
        _fail "pyproject.toml version = '$PYPROJECT_VER' (attendu : '$PEP440_VERSION' au format PEP 440)"
    fi

    CORE_VER=$("$PYTHON_BIN" -c "
import ast, sys
tree = ast.parse(open('core/__init__.py').read())
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id == '__version__':
                print(ast.literal_eval(node.value))
                sys.exit(0)
print('INTROUVABLE')
" 2>/dev/null || echo "ERREUR")

    if [ "$CORE_VER" = "$PEP440_VERSION" ]; then
        _ok "core/__init__.py __version__ = $PEP440_VERSION (PEP 440)"
    else
        _fail "core/__init__.py __version__ = '$CORE_VER' (attendu : '$PEP440_VERSION' au format PEP 440)"
    fi

    FORGE_VER=$("$PYTHON_BIN" -c "
import ast, sys
tree = ast.parse(open('forge.py').read())
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id == '_FORGE_VERSION':
                print(ast.literal_eval(node.value))
                sys.exit(0)
print('INTROUVABLE')
" 2>/dev/null || echo "ERREUR")

    if [ "$FORGE_VER" = "$PEP440_VERSION" ]; then
        _ok "forge.py _FORGE_VERSION = $PEP440_VERSION (PEP 440)"
    else
        _fail "forge.py _FORGE_VERSION = '$FORGE_VER' (attendu : '$PEP440_VERSION' au format PEP 440)"
    fi
fi

# Cohérence GLOBALE et autonome : tous les emplacements de version (sous-paquets,
# pins forge-mvc, extras, squelette, package.json en SemVer), indépendamment de
# l'argument de version (PKG-VERSION-SYNC-CHECK-001).
echo ""
echo "--- Cohérence de version sur tout le dépôt (check_version_sync.py) ---"
if CVS_OUT=$("$PYTHON_BIN" tools/check_version_sync.py 2>&1); then
    _ok "check_version_sync.py : versions cohérentes"
else
    _fail "check_version_sync.py : désynchronisation de version"
    printf '%s\n' "$CVS_OUT" | sed 's/^/         /' || true
fi

# ── 3. CHANGELOG (format SemVer public) ──────────────────────────────────────
if [ -n "$PUBLIC_VERSION" ]; then
    if grep -qF "## [$PUBLIC_VERSION]" CHANGELOG.md 2>/dev/null; then
        _ok "CHANGELOG.md contient ## [$PUBLIC_VERSION] (SemVer)"
    else
        _fail "CHANGELOG.md ne contient pas ## [$PUBLIC_VERSION] (SemVer)"
    fi
fi

# Un titre de version n'est pas un journal. Le contrôle ci-dessus vérifie que
# la section existe ; celui-ci vérifie qu'elle dise ce qui a été livré.
# GOV-CHANGELOG-COMPLETUDE-GARDEFOU-001.
echo ""
echo "--- Complétude du CHANGELOG (check_changelog_completeness.py) ---"
if CCC_OUT=$("$PYTHON_BIN" tools/check_changelog_completeness.py 2>&1); then
    _ok "CHANGELOG.md : tous les tickets livrés y figurent"
else
    _fail "CHANGELOG.md : des tickets livrés manquent au journal"
    printf '%s\n' "$CCC_OUT" | sed 's/^/         /' || true
fi

# ── 4. Tests ──────────────────────────────────────────────────────────────────
echo ""
echo "--- Exécution des tests (pytest -x -q) ---"
# RELEASE-VALIDATE-SKIPS-SILENCIEUX-001 — un test d'intégration qui ne trouve
# pas son serveur se SAUTE, il n'échoue pas. Sans les `FORGE_REQUIRE_*`, le
# dépôt porte 438 tests base qui peuvent disparaître de la suite sans que le
# vert n'en souffre, et le script concluait « prêt à releaser » sur une suite
# amputée. Mesuré sur une validation réelle : 152 tests sautés, MariaDB
# refusant les identifiants par défaut, verdict inchangé.
#
# C'est le piège du pré-mortem rc3, où l'arrêt d'un serveur avait fait ignorer
# des milliers de tests d'intégration sans que rien ne le montre.
#
# Ces variables ne changent pas ce qui est exécuté : elles changent ce qui se
# passe quand la connexion échoue, un saut devenant un échec. C'est exactement
# ce qu'on veut d'une validation de release, et jamais d'une boucle de
# développement. `--sans-serveurs` permet de l'assumer explicitement, ce qui
# reste préférable à un silence.
if ! $SANS_SERVEURS; then
    _MANQUANTES=""
    for _v in FORGE_REQUIRE_DB FORGE_REQUIRE_DB_PG FORGE_REQUIRE_DB_MSSQL; do
        [ -n "${!_v:-}" ] || _MANQUANTES="$_MANQUANTES $_v"
    done
    if [ -n "$_MANQUANTES" ]; then
        printf "[FAIL]  Tests d'intégration non exigés :%s\n" "$_MANQUANTES" >&2
        printf "         Sans elles, un serveur injoignable fait SAUTER ses tests au lieu\n" >&2
        printf "         d'échouer, et la suite reste verte en ayant moins tourné.\n" >&2
        printf "         Posez-les avec les mots de passe des serveurs de test, par exemple :\n" >&2
        printf "           FORGE_REQUIRE_DB=1 FORGE_TEST_DB_PASSWORD=... \\\\\n" >&2
        printf "           FORGE_REQUIRE_DB_PG=1 FORGE_TEST_PG_PASSWORD=... \\\\\n" >&2
        printf "           FORGE_REQUIRE_DB_MSSQL=1 FORGE_TEST_MSSQL_PASSWORD=... \\\\\n" >&2
        printf "           bash tools/release-validate.sh <version>\n" >&2
        printf "         Ou assumez la lacune : --sans-serveurs\n" >&2
        exit 1
    fi
fi
# RELEASE-AUDIT-SHIPPED-SURFACE-001 : le verdict vient du CODE RETOUR, pas du
# texte de sortie. L'ancien motif cherchait « passed|no tests ran » : une suite
# ne collectant AUCUN test (pytest sort en 5) affichait « no tests ran » et
# était comptée comme réussie. Une erreur de configuration pouvait donc laisser
# passer une release sans qu'un seul test ait tourné.
if PYTEST_OUT=$("$PYTHON_BIN" -m pytest -x -q 2>&1); then
    PYTEST_CODE=0
else
    PYTEST_CODE=$?
fi
echo "$PYTEST_OUT" | tail -5
# RELEASE-VALIDATE-SKIPS-SILENCIEUX-001 : le compte des sauts est ÉNONCÉ, même
# quand tout est vert. Un saut n'est pas un succès, et le taire laisse lire une
# suite amputée comme une suite complète (principe 3).
_SKIPS="$(printf '%s' "$PYTEST_OUT" | sed -n 's/.*[^0-9]\([0-9][0-9]*\) skipped.*/\1/p' | tail -1)"
if [ -n "$_SKIPS" ] && [ "$_SKIPS" -gt 0 ] 2>/dev/null; then
    if $SANS_SERVEURS; then
        _warn "Tests : $_SKIPS sauté(s) — validation lancée avec --sans-serveurs, lacune assumée"
    else
        _warn "Tests : $_SKIPS sauté(s) malgré les FORGE_REQUIRE_* — lire les motifs ci-dessus"
    fi
fi
case "$PYTEST_CODE" in
    0) _ok "Tests : OK" ;;
    5) _fail "Tests : échec — aucun test collecté (pytest code 5), configuration à vérifier" ;;
    *) _fail "Tests : échec (pytest code $PYTEST_CODE)" ;;
esac

# ── 5. Qualité de code ────────────────────────────────────────────────────────
echo ""
echo "--- Ruff ---"
RUFF_OUT=$("$PYTHON_BIN" -m ruff check . --quiet 2>&1 || true)
if [ -z "$RUFF_OUT" ]; then
    _ok "Ruff : aucune violation"
else
    _fail "Ruff : violations détectées"
    echo "$RUFF_OUT" | head -10 | sed 's/^/         /'
fi

# ── 6. Compilation Python ─────────────────────────────────────────────────────
COMPILE_OUT=$("$PYTHON_BIN" -m compileall -q . 2>&1 || true)
SYNTAX_ERRORS=$(echo "$COMPILE_OUT" | grep -v "^Listing" || true)
if [ -z "$SYNTAX_ERRORS" ]; then
    _ok "compileall : OK"
else
    _fail "compileall : erreurs de syntaxe"
    echo "$SYNTAX_ERRORS" | head -5 | sed 's/^/         /'
fi

# ── 7. MkDocs strict ─────────────────────────────────────────────────────────
echo ""
echo "--- MkDocs --strict ---"
# RELEASE-VALIDATE-MKDOCS-SETE-FIX-001 : command-substitution placée DANS la
# condition du `if` (exemptée de `set -e`), comme pour pip-audit plus bas.
# L'ancien motif `VAR=$(cmd); EXIT=$?; true` ne protégeait PAS l'assignation :
# un mkdocs en échec tuait le script avant d'afficher le _fail.
if MKDOCS_OUT=$("$PYTHON_BIN" -m mkdocs build --strict --quiet 2>&1); then
    _ok "MkDocs build --strict : OK"
else
    _fail "MkDocs build --strict : erreurs"
    echo "$MKDOCS_OUT" | grep -v "Material for MkDocs" | head -10 | sed 's/^/         /'
fi

# ── 8. Audit dépendances Python (pip-audit) — bloquant release ───────────────
# DEPENDENCY-AUDIT-RELEASE-GUARD-001 : `.github/workflows/dependency-audit.yml`
# reste informatif (continue-on-error: true) pour la surveillance hebdo ; ici
# en validation release, toute CVE ouverte sur les requirements bloque.
echo ""
echo "--- Audit dépendances Python (pip-audit) ---"
if ! "$PYTHON_BIN" -m pip_audit --version >/dev/null 2>&1; then
    _fail "pip-audit non installé dans $PYTHON_BIN — requis pour la validation release."
    echo "         Installer : $PYTHON_BIN -m pip install 'pip-audit>=2.0'"
else
    # RELEASE-VALIDATE-SETE-FIX-001 : la command-substitution est placée
    # DANS la condition du `if` (exemptée de `set -e`). L'ancien motif
    # `VAR=$(cmd); EXIT=$?; true` ne protégeait PAS l'assignation : un
    # pip-audit en échec tuait le script avant d'afficher le _fail.
    # PYSEC-2026-217 (mariadb 1.1.14) : avis sans correctif amont (1.1.14 est la
    # dernière version ; aucune fix version). Chemin vulnérable non emprunté par
    # Forge (requêtes paramétrées, pas de mysql_real_escape_string ni big5).
    # Accepté et documenté dans SECURITY.md ; ignoré ici pour que le gate reste
    # significatif (toute AUTRE CVE bloque). À retirer dès qu'un correctif paraît.
    if PIP_AUDIT_RT_OUT=$("$PYTHON_BIN" -m pip_audit --ignore-vuln PYSEC-2026-217 -r requirements.txt 2>&1); then
        _ok "pip-audit (requirements.txt) : aucune vulnérabilité (hors PYSEC-2026-217 accepté)"
    else
        _fail "pip-audit (requirements.txt) : vulnérabilités détectées"
        printf '%s\n' "$PIP_AUDIT_RT_OUT" | head -20 | sed 's/^/         /' || true
    fi
    # RELEASE-AUDIT-SHIPPED-SURFACE-001 : `requirements.txt` ne couvre que les
    # 4 dépendances du cœur. La surface RÉELLEMENT EXPÉDIÉE inclut celles des
    # opt-ins (Pillow, cryptography, psycopg, pyodbc...), agrégées dans
    # `requirements-audit.txt` — précisément celles qui portent des CVE. Sans
    # cette étape, le garde de release ignorait tout ce que Forge livre.
    if PIP_AUDIT_SHIPPED_OUT=$("$PYTHON_BIN" -m pip_audit --ignore-vuln PYSEC-2026-217 -r requirements-audit.txt 2>&1); then
        _ok "pip-audit (requirements-audit.txt, surface expédiée) : aucune vulnérabilité (hors PYSEC-2026-217 accepté)"
    else
        _fail "pip-audit (requirements-audit.txt, surface expédiée) : vulnérabilités détectées"
        printf '%s\n' "$PIP_AUDIT_SHIPPED_OUT" | head -20 | sed 's/^/         /' || true
    fi
    # L'exclusion ci-dessus est une dette : on vérifie qu'elle reste justifiée.
    if IGNORED_OUT=$("$PYTHON_BIN" tools/check_ignored_vulns.py requirements-audit.txt 2>&1); then
        _ok "Avis ignorés : toujours sans correctif amont"
    else
        _fail "Avis ignorés : un correctif est paru, relever la borne et retirer l'exclusion"
        printf '%s\n' "$IGNORED_OUT" | head -20 | sed 's/^/         /' || true
    fi
    # RELEASE-VALIDATE-FAUX-POSITIFS-001 : l'avis PYSEC-2026-217 est exclu comme
    # sur les deux relevés ci-dessus. Il manquait ici seul, si bien que le MÊME
    # avis était accepté sur `requirements.txt` et `requirements-audit.txt` et
    # bloquant sur `requirements-dev.txt`. Mesuré : c'est l'unique vulnérabilité
    # que ce fichier remonte, `mariadb` y étant tiré comme partout ailleurs.
    # Une release valide echouait donc sur une incoherence du script.
    # L'exclusion reste surveillee par `check_ignored_vulns.py` ci-dessus, qui
    # echoue des qu'un correctif amont parait.
    if PIP_AUDIT_DEV_OUT=$("$PYTHON_BIN" -m pip_audit --ignore-vuln PYSEC-2026-217 -r requirements-dev.txt 2>&1); then
        _ok "pip-audit (requirements-dev.txt) : aucune vulnérabilité (hors PYSEC-2026-217 accepté)"
    elif printf '%s' "$PIP_AUDIT_DEV_OUT" | grep -qiE 'No matching distribution found for forge-mvc|Could not find a version that satisfies the requirement forge-mvc'; then
        # Œuf-poule pré-release : requirements-dev.txt installe les opt-ins
        # locaux en éditable, qui dépendent de forge-mvc>=<version> pas encore
        # publié sur PyPI. La résolution échoue — ce n'est PAS une CVE.
        # L'audit dev redevient effectif après publication de forge-mvc.
        _warn "pip-audit (requirements-dev.txt) : différé — opt-ins locaux exigent forge-mvc non encore publié (œuf-poule pré-release) ; relancer après publication PyPI"
    else
        _fail "pip-audit (requirements-dev.txt) : vulnérabilités détectées"
        printf '%s\n' "$PIP_AUDIT_DEV_OUT" | head -20 | sed 's/^/         /' || true
    fi
fi

# ── 9. Audit dépendances Node (npm audit) — bloquant release ─────────────────
# `--omit=dev` : ne contrôle que les dépendances de production déclarées dans
# `package.json` (devDependencies non vérifiées ici).
echo ""
echo "--- Audit dépendances Node (npm audit --omit=dev) ---"
if [ ! -f package.json ]; then
    _ok "npm audit : aucun package.json — étape sans objet."
elif ! command -v npm >/dev/null 2>&1; then
    _fail "npm non installé — requis pour la validation release Node."
    echo "         Installer Node.js / npm puis relancer."
else
    if NPM_AUDIT_OUT=$(npm audit --omit=dev 2>&1); then
        _ok "npm audit (--omit=dev) : aucune vulnérabilité"
    else
        _fail "npm audit (--omit=dev) : vulnérabilités détectées"
        printf '%s\n' "$NPM_AUDIT_OUT" | head -20 | sed 's/^/         /' || true
    fi
fi

# ── 10. État git propre ──────────────────────────────────────────────────────
DIRTY=$(git status --porcelain 2>/dev/null | grep -v "^??" || true)
if [ -z "$DIRTY" ]; then
    _ok "Git : répertoire de travail propre"
else
    _fail "Git : modifications non commitées :"
    echo "$DIRTY" | head -10 | sed 's/^/         /'
fi

# ── 11. Whitespace ───────────────────────────────────────────────────────────
WS=$(git diff --check HEAD 2>/dev/null || true)
if [ -z "$WS" ]; then
    _ok "git diff --check : aucun problème de whitespace"
else
    _warn "Whitespace : $WS"
fi

# ── 12. Tag absent (pré-release) — format SemVer public ─────────────────────
if [ -n "$PUBLIC_VERSION" ]; then
    if git tag --list "v$PUBLIC_VERSION" | grep -q "v$PUBLIC_VERSION"; then
        _warn "Tag v$PUBLIC_VERSION existe déjà (re-release ?)"
    else
        _ok "Tag v$PUBLIC_VERSION absent — prêt à créer"
    fi
fi

# ── 13. Build & twine des distributions (opt-in : --with-packages) ───────────
# RELEASE-VALIDATE-PACKAGES-001 — preuve LOCALE que le core + tous les opt-ins
# se construisent et passent twine check (pas seulement « la CI le fait »).
# La liste des opt-ins est dérivée de packages/*/ (pas de liste codée en dur :
# tout nouvel opt-in est couvert automatiquement).
# Exécuté après le contrôle git propre : les artefacts dist/ sont gitignorés.
if $WITH_PACKAGES; then
    echo ""
    echo "--- Build des distributions (core + opt-ins) ---"
    rm -rf dist build ./*.egg-info
    for _p in packages/*/; do rm -rf "${_p}dist" "${_p}build" "${_p}"*.egg-info; done 2>/dev/null || true
    BUILD_OK=true
    _dist_count=1
    if ! "$PYTHON_BIN" -m build --no-isolation >/tmp/relval_build_core.log 2>&1; then
        _fail "build core : échec"
        tail -8 /tmp/relval_build_core.log | sed 's/^/         /' || true
        BUILD_OK=false
    fi
    for _pkg in packages/*/; do
        [ -f "${_pkg}pyproject.toml" ] || continue
        if ! "$PYTHON_BIN" -m build --no-isolation "$_pkg" >/tmp/relval_build_pkg.log 2>&1; then
            _fail "build ${_pkg%/} : échec"
            tail -8 /tmp/relval_build_pkg.log | sed 's/^/         /' || true
            BUILD_OK=false
        else
            _dist_count=$((_dist_count + 1))
        fi
    done
    if $BUILD_OK; then
        _ok "Build : ${_dist_count} distributions construites (core + opt-ins)"
        echo "--- twine check des artefacts ---"
        if "$PYTHON_BIN" -m twine check dist/* packages/*/dist/* >/tmp/relval_twine.log 2>&1; then
            _ok "twine check : tous les artefacts valides"
        else
            _fail "twine check : artefact(s) invalide(s)"
            tail -20 /tmp/relval_twine.log | sed 's/^/         /' || true
        fi
    fi
fi

# ── 14. Complétude de la publication ─────────────────────────────────────────
# RELEASE-PYPI-COMPLETENESS-GUARD-001 — croiser le dépôt, la construction et
# PyPI. La rc2 a été publiée avec 24 distributions sur 27 : les trois absentes
# étaient nées après la publication précédente, et rien ne le disait. Publier
# une release sans une distribution que le dépôt porte la rend régressive pour
# qui l'utilise — le cas mesuré est `forge-mvc-entities`, sans lequel
# `make:entity`, `make:crud`, les migrations et `db:*` disparaissent.
echo ""
echo "--- Complétude de la publication (dépôt / build / PyPI) ---"
_completeness_args=""
$WITH_PACKAGES && _completeness_args="--check-build"
if "$PYTHON_BIN" tools/check_pypi_completeness.py $_completeness_args \
        >/tmp/relval_completeness.log 2>&1; then
    _ok "Complétude : toute distribution du dépôt est publiable et publiée"
    grep '\[WARN\]' /tmp/relval_completeness.log | sed 's/^/         /' || true
else
    _fail "Complétude : distribution(s) manquante(s) ou orpheline(s)"
    sed 's/^/         /' /tmp/relval_completeness.log || true
fi

# ── 15. Installation en environnement vierge (opt-in : --with-smoke) ─────────
# SMOKE-INSTALL-VIERGE-001 — preuve que `forge new` -> `pip install -r
# requirements.txt` aboutit depuis des wheels construites localement, donc
# indépendamment de la publication PyPI. C'est le garde-fou qui attrape un
# paquet épinglé mais non installable (cause d'échec du premier contact).
if $WITH_SMOKE; then
    echo ""
    echo "--- Installation en environnement vierge (smoke) ---"
    if bash tools/smoke-install.sh >/tmp/relval_smoke.log 2>&1; then
        _ok "Smoke install : forge new s'installe et démarre depuis les wheels locales"
    else
        _fail "Smoke install : forge new ne s'installe pas depuis les wheels locales"
        tail -20 /tmp/relval_smoke.log | sed 's/^/         /' || true
    fi
fi

# ── Résumé ────────────────────────────────────────────────────────────────────
echo ""
echo "=== Résumé : $ERRORS erreur(s), $WARNS avertissement(s) ==="
if [ "$ERRORS" -gt 0 ]; then
    echo "RÉSULTAT : ÉCHEC — corriger les [FAIL] avant de releaser."
    exit 1
else
    echo "RÉSULTAT : OK — prêt à releaser."
    exit 0
fi
