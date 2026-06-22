"""Garde-fou DOCS-GUARD-OBSOLETE-CLI-001.

Empêche qu'une page de documentation active recommande une commande CLI
absente du registre Forge.

Motivation : la bêta.17 a livré README.md avec `forge starter:build welcome`,
commande supprimée par l'ADR-035, sans qu'aucun test ne le détecte. Ce module
ajoute le garde-fou de la classe de ce bug.

Principe :
- on extrait, dans les blocs de code shell des pages actives (README + docs/,
  hors archives), toute invocation `forge <commande>` ;
- on croise chaque commande avec le registre CLI canonique dérivé du code
  (HELP_DESCRIPTIONS + HELP_TEXTS_RICH + littéraux de dispatch de forge.py) ;
- toute commande inconnue échoue le test.

Effet de bord vertueux (principe 10, contrat de complétude) : une commande
réellement enregistrée mais absente du registre canonique est aussi signalée.

Limites : seules les invocations `forge <cmd>` en bloc shell sont contrôlées ;
ni `python forge.py …`, ni les arguments/options/chemins. Voir la spec du
ticket pour le détail.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from cli import help_dispatch as help_dispatch

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
FORGE_PY = PROJECT_ROOT / "forge.py"
FORGE_CLI = PROJECT_ROOT / "cli"

# Pseudo-commandes acceptées sans entrée de registre (entrypoint forge.py).
EXTRA_KNOWN = frozenset({"help"})

# Zones d'archive : des commandes historiques (supprimées) y sont légitimes.
EXCLUDED_DIRS = ("history", "adr", "roadmap", "release")

# Docs de conception/audit qui conservent volontairement un nom de commande
# d'époque, avec une note explicite en tête pointant la commande réelle. Ils ne
# trompent pas le lecteur (cf. l'admonition ADR-016 en tête de ce fichier :
# « la commande s'appelle désormais forge opt-in:enable »). Exclus nommément
# pour rester localisé — toute nouvelle entrée doit être justifiée de même.
EXCLUDED_FILES = frozenset(
    {
        Path("docs") / "architecture" / "optins-cli-enable-audit.md",
    }
)

# Langages de fence considérés comme du shell.
SHELL_FENCES = ("bash", "sh", "shell", "console")

# Une ligne de fence ouvrante/fermante : ```lang  ou  ```
_FENCE_RE = re.compile(r"^\s*```(\w*)\s*$")

# Premier jeton après `forge` : nom de commande (`make:entity`, `db:init`, `new`).
# `(?:^|\s)forge\s+` impose une espace après forge -> `cd forge-demo` ne matche pas.
_FORGE_CALL_RE = re.compile(r"(?:^|\s)forge\s+([A-Za-z][\w:-]*)")

# Flags acceptés sans subcommande.
_FLAG_PREFIX = "-"


def _is_command_operand(node: ast.expr) -> bool:
    """Vrai si `node` est l'opérande de dispatch d'une commande : la variable
    `command` (forge.py et la plupart des sous-dispatchers) ou `args[0]`
    (sous-dispatchers comme entities/migrations.py)."""
    if isinstance(node, ast.Name) and node.id == "command":
        return True
    if (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and node.value.id == "args"
        and isinstance(node.slice, ast.Constant)
        and node.slice.value == 0
    ):
        return True
    return False


def _dispatch_literals(path: Path) -> set[str]:
    """Extrait les noms de commandes comparés à l'opérande de dispatch dans
    un fichier Python.

    Couvre `command == "x"`, `command in ("x", "y")`, et les littéraux de type
    set `command in {"x", "y"}` (indispensable : migration:make n'apparaît que
    dans un set de forge.py). Scanné sur forge.py ET cli/**/*.py pour
    couvrir les sous-dispatchers (module:remove est dans cli/modules.py).
    """
    literals: set[str] = set()
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        if not _is_command_operand(node.left):
            continue
        for op, comparator in zip(node.ops, node.comparators):
            if isinstance(op, ast.Eq) and isinstance(comparator, ast.Constant):
                if isinstance(comparator.value, str):
                    literals.add(comparator.value)
            elif isinstance(op, ast.In) and isinstance(
                comparator, (ast.Tuple, ast.List, ast.Set)
            ):
                for elt in comparator.elts:
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                        literals.add(elt.value)
    return literals


def _known_commands() -> set[str]:
    """Registre CLI canonique : union des sources de vérité du code.

    - registre d'aide (HELP_DESCRIPTIONS + HELP_TEXTS_RICH) ;
    - littéraux de dispatch de forge.py et des sous-dispatchers cli/ ;
    - pseudo-commandes de l'entrypoint (`help`).
    """
    known = set(help_dispatch.HELP_DESCRIPTIONS) | set(help_dispatch.HELP_TEXTS_RICH)
    known |= _dispatch_literals(FORGE_PY)
    for py in FORGE_CLI.rglob("*.py"):
        known |= _dispatch_literals(py)
    known |= EXTRA_KNOWN
    return known


def _active_docs() -> list[Path]:
    """README + docs/**/*.md, hors zones d'archive."""
    pages: list[Path] = []
    readme = PROJECT_ROOT / "README.md"
    if readme.exists():
        pages.append(readme)
    docs = PROJECT_ROOT / "docs"
    for md in docs.rglob("*.md"):
        rel_parts = md.relative_to(docs).parts
        if rel_parts and rel_parts[0] in EXCLUDED_DIRS:
            continue
        if md.relative_to(PROJECT_ROOT) in EXCLUDED_FILES:
            continue
        pages.append(md)
    return pages


def _forge_invocations(text: str) -> list[tuple[int, str]]:
    """Renvoie [(no_ligne, commande)] des invocations `forge <cmd>` trouvées
    dans les blocs de code shell de `text`.

    Restreindre aux fences shell attrape les vraies invocations et évite les
    faux positifs de prose (ex. `forge starter:build` cité comme motif
    interdit dans docs/contributing) et les liens `forgemvc.com/...`.
    """
    found: list[tuple[int, str]] = []
    in_shell_block = False
    for lineno, line in enumerate(text.splitlines(), start=1):
        fence = _FENCE_RE.match(line)
        if fence is not None:
            lang = fence.group(1).lower()
            if not in_shell_block:
                # Fence ouvrante : on entre si le langage est shell.
                in_shell_block = lang in SHELL_FENCES
            else:
                # Fence fermante (```), quel que soit le contenu.
                in_shell_block = False
            continue
        if not in_shell_block:
            continue
        for match in _FORGE_CALL_RE.finditer(line):
            token = match.group(1)
            if token.startswith(_FLAG_PREFIX):
                continue  # forge --version / forge -h
            found.append((lineno, token))
    return found


class TestNoObsoleteCliCommands:
    """Aucune page active ne référence une commande CLI absente du registre."""

    def test_registre_canonique_non_vide(self):
        known = _known_commands()
        # Sanity : le registre doit contenir des commandes connues stables.
        assert {"new", "run", "make:entity", "db:init"} <= known, (
            "Registre CLI canonique incomplet — vérifier HELP_DESCRIPTIONS / "
            "HELP_TEXTS_RICH / dispatch forge.py"
        )

    def test_aucune_commande_obsolete_dans_doc_active(self):
        known = _known_commands()
        offenders: list[str] = []
        for page in _active_docs():
            text = page.read_text(encoding="utf-8")
            for lineno, command in _forge_invocations(text):
                if command not in known:
                    rel = page.relative_to(PROJECT_ROOT)
                    offenders.append(f"{rel}:{lineno} — commande « {command} »")
        if offenders:
            raise AssertionError(
                f"{len(offenders)} commande(s) CLI absente(s) du registre dans "
                f"la doc active :\n"
                + "\n".join(f"  - {o}" for o in offenders)
                + "\n\nCommandes connues : voir HELP_DESCRIPTIONS / "
                "HELP_TEXTS_RICH (cli/help_dispatch.py) et le dispatch "
                "de forge.py."
            )


class TestGuardActuallyBites:
    """Le garde-fou doit mordre : un bloc shell avec une commande inconnue
    est rejeté, une commande connue est acceptée."""

    def test_commande_bidon_detectee(self):
        sample = "```bash\nforge commande:bidon\n```\n"
        invocations = _forge_invocations(sample)
        assert ("commande:bidon" in [c for _, c in invocations])
        known = _known_commands()
        assert "commande:bidon" not in known

    def test_starter_build_serait_rejete(self):
        # Reproduit la régression bêta.17 : doit être hors registre.
        sample = "```bash\nforge starter:build welcome\n```\n"
        invocations = _forge_invocations(sample)
        assert ("starter:build" in [c for _, c in invocations])
        assert "starter:build" not in _known_commands()

    def test_commande_reelle_acceptee(self):
        sample = "```bash\nforge new mon-projet\ncd mon-projet\nforge run\n```\n"
        commands = [c for _, c in _forge_invocations(sample)]
        assert commands == ["new", "run"]
        known = _known_commands()
        assert all(c in known for c in commands)

    def test_flags_et_cd_ignores(self):
        sample = "```bash\nforge --version\nforge -h\ncd forge-demo\n```\n"
        assert _forge_invocations(sample) == []

    def test_prose_inline_hors_fence_ignoree(self):
        # `forge starter:build` en prose à backticks ne doit pas être capté.
        sample = "Pas de motif interdit (`forge starter:build …`) dans un palier.\n"
        assert _forge_invocations(sample) == []
