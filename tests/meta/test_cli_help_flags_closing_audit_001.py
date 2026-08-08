"""Garde-fou CLI-HELP-FLAGS-CLOSING-AUDIT-001.

Ticket de clôture du chantier --help. Verrouille définitivement la
couverture acquise :

1. La liste des commandes dispatchées par forge.py est connue et figée
   ici (`ALL_DISPATCHED_COMMANDS`).
2. Chaque commande appartient à exactement une catégorie :
       AIDE_RICHE              — présente dans HELP_TEXTS_RICH
       AIDE_NATIVE_ARGPARSE    — auth:user:* (argparse-iso)
       AIDE_NATIVE_MANUELLE    — make:entity, make:relation, db:apply,
                                  migration:make, starter:build, module:*
       CAS_SPECIAL_DOCUMENTE   — aucune aujourd'hui
3. Aucune commande connue ne tombe dans le gabarit générique fallback.
4. Les 6 commandes critiques (effets de bord identifiés par l'audit
   initial) retournent toujours 0 avec --help sans rien exécuter.
5. Les commandes natives gardent leur aide native (non interceptée par
   le dispatcher central).
6. Si une nouvelle commande est ajoutée à forge.py sans entrée dans
   l'une des catégories ci-dessus, le test échoue immédiatement.

Ce test ne réenrichit aucune aide ; il vérifie le contrat.
"""
from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

from cli._support.help_dispatch import HELP_DESCRIPTIONS, HELP_TEXTS_RICH

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
FORGE_PY = PROJECT_ROOT / "forge.py"


# Liste figée des commandes dispatchées par forge.py.
# (sync:landing retirée par ADR-044 : landing canonique dans docs/.)
# Tirée de forge.py : un grep "if command (==|in)" donne la même liste.
ALL_DISPATCHED_COMMANDS: frozenset[str] = frozenset({
    # Projet
    "new", "skeleton:upgrade", "run", "update", "doctor", "project:check", "project:audit", "routes:list",
    "agents:init",
    # Entités
    "make:entity", "make:crud", "make:pivot-crud", "make:relation",
    "entity:validate", "entity:doc",
    "sync:entity", "sync:relations",
    "build:model", "check:model",
    # Pages publiques
    "make:public-page", "make:public-list", "make:public-show",
    "make:public-form", "make:public-contact",
    # Base de données
    "db:config", "db:init", "db:apply",
    "migration:status", "migration:apply", "migration:make", "migration:diff",
    # Schémas JSON
    "schema:list", "schema:doctor",
    # RBAC
    "rbac:validate", "rbac:audit",
    # Modules
    "module:list", "module:install", "module:files", "module:routes", "module:remove",
    # Auth
    "make:auth",
    "auth:init", "auth:doctor", "auth:status", "auth:list-sql",
    "auth:user:create", "auth:user:list", "auth:user:show",
    "auth:user:disable", "auth:user:enable", "auth:user:password",
    "auth:user:role:add", "auth:user:role:remove", "auth:user:roles",
    # Mail
    "mail:init", "mail:test", "mail:render", "mail:doctor", "mail:logs",
    # IoT (module opt-in forge-mvc-iot)
    "iot:doctor", "iot:init", "iot:simulate", "iot:listen",
    # Vidéo (module opt-in forge-mvc-video)
    "video:doctor", "video:init", "video:upload", "video:process", "video:cleanup",
    # Audio (module opt-in forge-mvc-audio)
    "audio:doctor",
    # Admin (module opt-in forge-mvc-admin)
    "admin:init",
    "admin:doctor",
    # Opt-ins (branchement projet)
    "opt-in:install", "opt-in:remove", "opt-in:enable", "opt-in:disable", "opt-in:list",
    "opt-in:installed",
    # Documentation
    "docs:pdf",
    # Internationalisation
    "i18n:init", "i18n:check",
    # Médias et JavaScript
    "upload:init", "media:init", "images:init", "js:init",
    # Déploiement
    "deploy:init", "deploy:check",
    # Opt-ins applicatifs (ADR-052)
    "settings:init", "audit:init", "audit:gc", "jobs:init", "notifications:init",
    "sessions:init", "sessions:gc",
    # MFA : table du registre anti-rejeu partagé, optionnelle
    # (MFA-TOTP-REPLAY-SHARED-001). Le magasin par défaut n'a besoin d'aucune table.
    "mfa:init",
    # RBAC : provisionnement de roles/permissions/role_permissions
    # (OPTIN-DDL-RBAC-INIT-001). La table pivot user_roles reste à auth:init.
    "rbac:init",
    # Fixtures (ADR-074, ADR-076)
    "fixtures:load", "fixtures:purge", "fixtures:generate", "fixtures:make-factory",
})


# Commandes natives argparse : leur main() utilise argparse, qui gère
# `--help` automatiquement. Le dispatcher central NE doit PAS les
# intercepter pour ne pas écraser leur aide détaillée.
NATIVE_ARGPARSE_COMMANDS: frozenset[str] = frozenset({
    "auth:user:create",
    "auth:user:show",
    "auth:user:disable",
    "auth:user:enable",
    "auth:user:password",
    "auth:user:role:add",
    "auth:user:role:remove",
    "auth:user:roles",
})


# Commandes natives manuelles : leur main() (ou le dispatcher pour
# db:apply) gère explicitement `if "--help" in args:` et imprime une
# aide propre. Pareil — pas interceptées par le dispatcher central.
NATIVE_MANUAL_COMMANDS: frozenset[str] = frozenset({
    "make:entity",
    "make:relation",
    "db:apply",
    "migration:make",
    "module:list",
    "module:install",
    "module:files",
    "module:routes",
    "module:remove",
})


# Aujourd'hui aucune commande n'est dans cette catégorie. Le set est
# défini pour pouvoir documenter explicitement un cas spécial futur
# sans rouvrir le test.
SPECIAL_DOCUMENTED_COMMANDS: frozenset[str] = frozenset()


# 6 commandes critiques identifiées par CLI-HELP-FLAGS-AUDIT-001 comme
# ayant des effets de bord si --help n'était pas intercepté.
CRITICAL_INIT_COMMANDS: tuple[str, ...] = (
    "db:init",
    "mail:init",
    "i18n:init",
    "upload:init",
    "media:init",
    "deploy:init",
)


_FORGE_PY_TEXT = FORGE_PY.read_text(encoding="utf-8")


def _commands_referenced_in_forge_py() -> set[str]:
    """Extrait toutes les chaînes comparées à `command` dans forge.py.

    Parcourt l'AST et trouve les nœuds `Compare` ou `In` dont l'opérande
    gauche est le nom `command`. Pour chaque comparator on capture les
    chaînes littérales — tuple, set ou string seule.
    """
    found: set[str] = set()
    tree = ast.parse(_FORGE_PY_TEXT)

    def _add_string_consts(node: ast.AST) -> None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            found.add(node.value)
        elif isinstance(node, (ast.Tuple, ast.List, ast.Set)):
            for elt in node.elts:
                _add_string_consts(elt)

    for node in ast.walk(tree):
        if isinstance(node, ast.Compare) and isinstance(node.left, ast.Name) \
                and node.left.id == "command":
            for cmp in node.comparators:
                _add_string_consts(cmp)
    # ADR-059 : les commandes opt-in et les commandes du cœur déléguées sont
    # dispatchées via des tables centrales, plus uniquement par le if-chain.
    from forge import CORE_COMMANDS

    from cli.commands.optin_dispatch import all_optin_commands

    found |= set(all_optin_commands()) | set(CORE_COMMANDS)
    return found


def _run_forge(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(FORGE_PY), *args],
        capture_output=True, text=True, timeout=15,
    )


# ── Tests de classification ───────────────────────────────────────────────────


class TestEveryDispatchedCommandIsClassified:
    """Chaque commande dispatchée appartient à exactement une catégorie."""

    def test_categories_partition_dispatched_commands(self):
        rich = set(HELP_TEXTS_RICH)
        union = (
            rich
            | NATIVE_ARGPARSE_COMMANDS
            | NATIVE_MANUAL_COMMANDS
            | SPECIAL_DOCUMENTED_COMMANDS
        )
        unclassified = ALL_DISPATCHED_COMMANDS - union
        assert not unclassified, (
            "Commandes dispatchées sans classification :\n  "
            + "\n  ".join(sorted(unclassified))
            + "\n\nAjouter une entrée dans HELP_TEXTS_RICH OU dans "
            "NATIVE_ARGPARSE_COMMANDS / NATIVE_MANUAL_COMMANDS / "
            "SPECIAL_DOCUMENTED_COMMANDS selon le cas."
        )

    def test_categories_are_disjoint(self):
        rich = set(HELP_TEXTS_RICH)
        for left_name, left in [
            ("HELP_TEXTS_RICH", rich),
            ("NATIVE_ARGPARSE_COMMANDS", set(NATIVE_ARGPARSE_COMMANDS)),
            ("NATIVE_MANUAL_COMMANDS", set(NATIVE_MANUAL_COMMANDS)),
            ("SPECIAL_DOCUMENTED_COMMANDS", set(SPECIAL_DOCUMENTED_COMMANDS)),
        ]:
            for right_name, right in [
                ("HELP_TEXTS_RICH", rich),
                ("NATIVE_ARGPARSE_COMMANDS", set(NATIVE_ARGPARSE_COMMANDS)),
                ("NATIVE_MANUAL_COMMANDS", set(NATIVE_MANUAL_COMMANDS)),
                ("SPECIAL_DOCUMENTED_COMMANDS", set(SPECIAL_DOCUMENTED_COMMANDS)),
            ]:
                if left_name >= right_name:
                    continue
                overlap = left & right
                assert not overlap, (
                    f"{left_name} et {right_name} se recouvrent : "
                    f"{sorted(overlap)}. Une commande doit appartenir "
                    "à exactement une catégorie."
                )

    def test_no_unknown_commands_in_rich(self):
        unknown = set(HELP_TEXTS_RICH) - ALL_DISPATCHED_COMMANDS
        assert not unknown, (
            "Entrées HELP_TEXTS_RICH pour des commandes non dispatchées "
            f"par forge.py : {sorted(unknown)}. Soit ajouter la commande "
            "au dispatcher, soit retirer l'entrée."
        )


class TestForgePyMatchesAuditedList:
    """forge.py n'a pas évolué silencieusement depuis la clôture."""

    def test_dispatched_commands_match_audited_list(self):
        referenced = _commands_referenced_in_forge_py()
        # On retire les littéraux propres aux comparaisons globales en
        # amont du dispatch (`help`, `--help`, `-h`, `--version`).
        meta = {"help", "--help", "-h", "--version"}
        cleaned = referenced - meta
        missing = cleaned - ALL_DISPATCHED_COMMANDS
        added = ALL_DISPATCHED_COMMANDS - cleaned
        assert not missing and not added, (
            f"Liste figée vs forge.py désynchronisée.\n"
            f"  Présentes dans forge.py mais absentes du garde-fou : "
            f"{sorted(missing)}\n"
            f"  Présentes dans le garde-fou mais absentes de forge.py : "
            f"{sorted(added)}\n"
            f"Mettre à jour ALL_DISPATCHED_COMMANDS si forge.py a évolué."
        )


# ── Tests de comportement runtime ────────────────────────────────────────────


class TestRichCommandsAllExitZero:
    """Toutes les commandes en aide riche retournent 0 avec --help / -h."""

    @pytest.mark.parametrize("command", sorted(HELP_TEXTS_RICH))
    def test_long_form(self, command: str):
        result = _run_forge(command, "--help")
        assert result.returncode == 0, (
            f"forge {command} --help doit retourner 0 "
            f"(aide riche présente). stderr={result.stderr!r}"
        )

    @pytest.mark.parametrize("command", sorted(HELP_TEXTS_RICH))
    def test_short_form(self, command: str):
        result = _run_forge(command, "-h")
        assert result.returncode == 0, (
            f"forge {command} -h doit retourner 0 "
            f"(aide riche présente). stderr={result.stderr!r}"
        )


class TestNativeCommandsKeepTheirHelp:
    """Les commandes natives gardent leur aide propre."""

    @pytest.mark.parametrize("command", sorted(NATIVE_ARGPARSE_COMMANDS))
    def test_argparse_help_is_native(self, command: str):
        out = _run_forge(command, "--help").stdout
        # Marqueur argparse minuscule
        assert f"usage: forge {command}" in out, (
            f"{command} n'a plus son aide argparse native (interception "
            f"indue ?). Sortie : {out[:200]!r}"
        )
        # Marqueur du gabarit central (à ne PAS retrouver)
        assert "Description:" not in out, (
            f"{command} : le dispatcher central a écrasé l'aide argparse."
        )

    @pytest.mark.parametrize("command", sorted(NATIVE_MANUAL_COMMANDS))
    def test_manual_help_returns_zero(self, command: str):
        result = _run_forge(command, "--help")
        assert result.returncode == 0, (
            f"forge {command} --help doit retourner 0 "
            f"(aide manuelle native). stderr={result.stderr!r}"
        )


class TestCriticalCommandsRemainSafe:
    """Les 6 commandes critiques n'exécutent toujours rien avec --help."""

    SAFE_MARKERS_TO_REJECT = (
        "[OK]",
        "[ERREUR]",
        "Provisioning",
        "[PRÉSERVÉ]",
        "Dossier prêt",
    )

    @pytest.mark.parametrize("command", CRITICAL_INIT_COMMANDS)
    def test_long_form_safe(self, command: str):
        result = _run_forge(command, "--help")
        assert result.returncode == 0
        combined = result.stdout + result.stderr
        offenders = [m for m in self.SAFE_MARKERS_TO_REJECT if m in combined]
        assert not offenders, (
            f"{command} --help a déclenché un effet de bord "
            f"(marqueurs : {offenders}). Régression CLI-HELP-FLAGS-"
            f"DISPATCHER-001."
        )

    @pytest.mark.parametrize("command", CRITICAL_INIT_COMMANDS)
    def test_short_form_safe(self, command: str):
        result = _run_forge(command, "-h")
        assert result.returncode == 0
        combined = result.stdout + result.stderr
        offenders = [m for m in self.SAFE_MARKERS_TO_REJECT if m in combined]
        assert not offenders, (
            f"{command} -h a déclenché un effet de bord "
            f"(marqueurs : {offenders}). Régression CLI-HELP-FLAGS-"
            f"DISPATCHER-001."
        )


# ── Test du filet de sécurité HELP_DESCRIPTIONS ─────────────────────────────


class TestSafetyNetDuplication:
    """Les 45 entrées riches sont aussi présentes dans HELP_DESCRIPTIONS.

    Décision Option A de CLI-HELP-FLAGS-CLOSING-AUDIT-001 : la
    duplication est délibérée. Une future commande oubliée tombera dans
    le gabarit générique plutôt que dans le dispatcher métier.
    """

    def test_rich_entries_also_in_descriptions(self):
        rich_only = set(HELP_TEXTS_RICH) - set(HELP_DESCRIPTIONS)
        assert not rich_only, (
            "Entrées riches non doublées dans HELP_DESCRIPTIONS : "
            f"{sorted(rich_only)}. Décision Option A : conserver la "
            "duplication pour garder un filet de sécurité."
        )

    def test_descriptions_keys_match_rich_keys(self):
        # Comme la duplication est totale aujourd'hui, on verrouille
        # cette propriété pour repérer toute dérive ultérieure.
        only_in_desc = set(HELP_DESCRIPTIONS) - set(HELP_TEXTS_RICH)
        only_in_rich = set(HELP_TEXTS_RICH) - set(HELP_DESCRIPTIONS)
        assert not only_in_desc and not only_in_rich, (
            "HELP_DESCRIPTIONS et HELP_TEXTS_RICH ont divergé.\n"
            f"  Seulement dans HELP_DESCRIPTIONS : {sorted(only_in_desc)}\n"
            f"  Seulement dans HELP_TEXTS_RICH  : {sorted(only_in_rich)}"
        )
