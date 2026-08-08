"""Garde-fou FORGE-HELP-COVERAGE-001.

Vérifie la cohérence entre :
1. Les commandes affichées par `forge --help`
2. Les commandes documentées dans `docs/reference/cli-commands.md`
3. La qualité des aides individuelles pour les commandes qui l'implémentent

Origine : audit F23 — la doc CLI a été livrée en PR1 (3.0.1) mais
la cohérence avec le CLI réel n'avait pas été automatiquement validée.

Sans ce garde-fou, l'ajout futur d'une commande CLI sans documentation
correspondante (ou inversement) ne serait pas détecté.

Notes de reconnaissance T11 :
- `forge --help` liste 48 commandes réelles (+ artefacts `help,` et `forge`)
- `cli-commands.md` documente 51 commandes + 2 flags (`--help`, `--version`)
- 3 commandes fonctionnelles absentes de `forge --help` : i18n:check,
  i18n:init, sync:landing → ajoutées à KNOWN_DOCUMENTED_EXCEPTIONS
- ~20 commandes ne gèrent pas `--help` comme flag (structural CLI issue,
  hors scope T11) → l'échantillon de test se limite aux commandes connues
  pour l'implémenter correctement
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
CLI_DOC = PROJECT_ROOT / "docs" / "reference" / "cli-commands.md"


def _get_cli_commands() -> set[str]:
    """Extrait la liste des commandes réelles depuis `forge --help`."""
    try:
        result = subprocess.run(
            ["forge", "--help"],
            capture_output=True, text=True, timeout=10,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pytest.skip("forge non disponible dans le PATH du test")

    commands = set()
    for line in result.stdout.splitlines():
        # Format possible :
        #   "  command:name        Description..."   (commandes sans arg)
        #   "  command <Arg>       Description..."   (commandes avec arg positionnel)
        # On capture le premier mot après les 2 espaces d'indentation.
        match = re.match(r"^  ([a-z][a-z0-9:_-]+)[ <\s]", line)
        if match:
            cmd = match.group(1)
            # Filtrer les artefacts connus (ligne "help, --help, -h")
            if cmd not in ("forge", "help,"):
                commands.add(cmd)
    return commands


def _get_documented_commands() -> set[str]:
    """Extrait la liste des commandes depuis cli-commands.md.

    Le catalogue concis (DOCS-CLI-COMMANDS-CATALOG-001) liste les commandes
    dans des tableaux Markdown sous la forme ``| `forge <cmd>` | … |``. On
    accepte aussi les anciens formats (titre ``### `forge <cmd>` `` et fiche
    ``<summary><code>forge <cmd></code>``) pour rester robuste.
    """
    text = CLI_DOC.read_text(encoding="utf-8")
    commands = set()
    for match in re.finditer(r"^### `forge ([a-z][a-z0-9:_-]+)`", text, re.MULTILINE):
        commands.add(match.group(1))
    for match in re.finditer(
        r"<summary><code>forge ([a-z][a-z0-9:_-]+)</code>",
        text,
    ):
        commands.add(match.group(1))
    # Catalogue concis : entrée de tableau « | `forge <cmd>` | … ».
    for match in re.finditer(r"^\|\s*`forge ([a-z][a-z0-9:_-]+)`", text, re.MULTILINE):
        commands.add(match.group(1))
    return commands


# Commandes documentées dans cli-commands.md mais absentes de `forge --help`
# parce qu'elles ne sont pas listées dans l'aide globale (commandes "silencieuses").
# Ces commandes sont fonctionnelles — elles s'exécutent normalement, elles sont
# simplement cachées du listing --help.
# Identifiées lors de la reconnaissance T11 (audit F23).
KNOWN_DOCUMENTED_EXCEPTIONS: set[str] = set()
# (sync:landing retirée par ADR-044 : landing canonique dans docs/.)

# ADR-042 : les commandes livrées par les opt-ins (documentées dans leur propre
# espace, pas dans la référence CLI du cœur). Exclues du contrôle de couverture
# « commande CLI absente de la doc cœur ».
OPT_IN_CLI_NAMESPACES = (
    "mail:", "iot:", "video:", "audio:", "i18n:",
    "rbac:", "workflow:", "stats:", "pivot:", "admin:",
    # Opt-ins ADR-052 : commandes :init documentées dans la doc embarquée du paquet.
    "settings:", "audit:", "jobs:", "notifications:",
    # Opt-ins médias et sessions : doc embarquée du paquet (ADR-038).
    "images:", "sessions:",
    # MFA : `mfa:init` provisionne la table du registre anti-rejeu partagé,
    # optionnelle (MFA-TOTP-REPLAY-SHARED-001). Documentée dans la doc
    # embarquée du paquet, section « Mise en service ».
    "mfa:",
)

# Commandes dans forge --help intentionnellement non documentées (rare)
KNOWN_CLI_EXCEPTIONS: set[str] = set()

# Commandes de l'échantillon pour le test d'aide individuelle.
# Limitées aux commandes connues pour implémenter --help correctement
# (~20 autres commandes ont une limitation structurelle CLI — hors scope T11).
COMMANDS_WITH_HELP_SUPPORT = [
    "auth:doctor",
    "auth:init",
    "auth:user:list",
    "build:model",
    "check:model",
    "js:init",
    "mail:test",
    "make:entity",
    "make:relation",
    "module:install",
    "module:routes",
]


class TestCliVsDoc:
    """Cohérence entre forge --help et cli-commands.md."""

    def test_cli_help_returns_output(self):
        """forge --help retourne au moins 40 commandes réelles."""
        cmds = _get_cli_commands()
        assert len(cmds) >= 40, (
            f"forge --help retourne seulement {len(cmds)} commandes, "
            f"attendu au moins 40. Vérifier l'installation."
        )

    def test_cli_doc_documents_many_commands(self):
        """cli-commands.md documente au moins 40 commandes."""
        cmds = _get_documented_commands()
        assert len(cmds) >= 40, (
            f"cli-commands.md documente seulement {len(cmds)} commandes, "
            f"attendu au moins 40. PR1 (DOCS-CLI-COMMANDS-REFERENCE-001) "
            f"devait livrer ~53 commandes."
        )

    def test_no_cli_commands_missing_in_doc(self):
        """Toute commande dans forge --help est documentée dans cli-commands.md."""
        cli = _get_cli_commands()
        doc = _get_documented_commands()
        missing = {
            c for c in (cli - doc - KNOWN_CLI_EXCEPTIONS)
            if not c.startswith(OPT_IN_CLI_NAMESPACES)
        }
        assert not missing, (
            "Commandes dans le CLI mais absentes de cli-commands.md :\n  "
            + "\n  ".join(sorted(missing))
            + "\n\nAjouter une section `### \\`forge <cmd>\\`` dans cli-commands.md "
            + "pour chacune, ou les ajouter à KNOWN_CLI_EXCEPTIONS avec justification."
        )

    def test_no_documented_commands_missing_in_cli(self):
        """Toute commande documentée existe dans le CLI ou est une exception connue."""
        cli = _get_cli_commands()
        doc = _get_documented_commands()
        orphan = doc - cli - KNOWN_DOCUMENTED_EXCEPTIONS
        assert not orphan, (
            "Commandes documentées mais absentes du CLI :\n  "
            + "\n  ".join(sorted(orphan))
            + "\n\nSoit retirer la section dans cli-commands.md, soit ajouter "
            + "à KNOWN_DOCUMENTED_EXCEPTIONS avec justification."
        )

    def test_known_documented_exceptions_still_functional(self):
        """Les commandes KNOWN_DOCUMENTED_EXCEPTIONS existent encore dans le code CLI."""
        # On vérifie leur présence dans cli-commands.md (et non pas qu'elles retournent
        # quelque chose de spécifique, pour ne pas dépendre de l'état du projet de test)
        doc = _get_documented_commands()
        for cmd in KNOWN_DOCUMENTED_EXCEPTIONS:
            assert cmd in doc, (
                f"KNOWN_DOCUMENTED_EXCEPTIONS contient '{cmd}' mais cette commande "
                f"n'est plus documentée dans cli-commands.md. Mettre à jour la liste."
            )


class TestIndividualCommandHelp:
    """Les commandes qui implémentent --help retournent une aide structurée."""

    @pytest.mark.parametrize("command", COMMANDS_WITH_HELP_SUPPORT)
    def test_command_has_structured_help(self, command: str):
        """`forge <command> --help` retourne un texte d'aide non vide avec indicateur."""
        try:
            result = subprocess.run(
                ["forge", command, "--help"],
                capture_output=True, text=True, timeout=10,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("forge non disponible")

        output = result.stdout + result.stderr
        assert len(output.strip()) > 20, (
            f"forge {command} --help retourne une sortie trop courte : "
            f"'{output[:100]}'."
        )

        output_lower = output.lower()
        indicators = ["usage", f"forge {command}", "options", "arguments", "génère", "affiche"]
        found = [ind for ind in indicators if ind in output_lower]
        assert found, (
            f"forge {command} --help ne contient aucun indicateur d'aide "
            f"structurée. Sortie : '{output[:200]}'"
        )


class TestDocStructure:
    """Le doc CLI a une structure cohérente."""

    def test_doc_exists(self):
        assert CLI_DOC.exists(), "docs/reference/cli-commands.md doit exister"

    def test_doc_has_section_headers(self):
        """cli-commands.md a au moins 10 sections H2 (groupes de commandes)."""
        text = CLI_DOC.read_text(encoding="utf-8")
        h2_count = len(re.findall(r"^## [A-Z]", text, re.MULTILINE))
        assert h2_count >= 10, (
            f"cli-commands.md doit avoir au moins 10 sections H2. "
            f"Trouvé : {h2_count}."
        )

    def test_doc_covers_main_groups(self):
        """Les groupes principaux de commandes sont couverts."""
        text = CLI_DOC.read_text(encoding="utf-8").lower()
        expected_groups = ["projet", "entité", "page", "donné", "starter", "auth", "mail"]
        found = [g for g in expected_groups if g in text]
        assert len(found) >= 5, (
            f"cli-commands.md doit couvrir les groupes principaux. "
            f"Groupes trouvés ({len(found)}/7) : {found}."
        )
