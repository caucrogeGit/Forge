#!/usr/bin/env python3
# pyright: strict
"""forge.py — CLI officielle de Forge. Aide : forge help"""

from typing import Any, cast
from collections.abc import Callable
import os
import re
import sys
import shutil
import subprocess
import importlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from cli.entities.db_apply import main as db_apply_main
from cli.entities.db_init import main as db_init_main
from cli.entities.migrations import main as migrations_main
from cli.entities.make_entity import main as make_entity_main
from cli.entities.make_relation import main as make_relation_main
from cli.entities.make_crud import cmd_make_crud_main
from cli.entities.model import main as model_main
from cli.entities.entity_validate import main as entity_validate_main
from cli.public.public_contact import main as public_contact_main
from cli.public.public_form import main as public_form_main
from cli.public.public_list import main as public_list_main
from cli.public.public_page import main as public_page_main
from cli.public.public_show import main as public_show_main
from cli.assets.front import main as front_main
from cli.security.auth import main as auth_main
from cli.assets.i18n import main as i18n_main
from cli.project.run import main as run_main
from cli.project.update import main as update_main
from cli.deploy.modules import main as modules_main
from cli.project.project_profiles import (
    SUPPORTED_PROJECT_PROFILES,
    DEFAULT_PROJECT_PROFILE,
)
from cli._support.errors import cli_fail
from cli._support.help_dispatch import format_command_help, wants_help
from cli.commands.optin_dispatch import dispatch_optin


_FORGE_VERSION = "1.0.0rc2"
# Tag git de release correspondant à cette version. N'est plus utilisé pour
# créer un projet (forge new copie un squelette embarqué, ADR-024) ; conservé
# comme métadonnée de release, ancrée par la gouvernance de version (tests
# release/meta de cohérence de version).
_FORGE_DEFAULT_REF = "v1.0.0-rc.2"


# ── Utilitaires ───────────────────────────────────────────────────────────────

def _print_step(message: str) -> None:
    print(f"  {message}")


def _run(args: list[str], cwd: str | None = None, capture: bool = False, check: bool = False) -> "subprocess.CompletedProcess[str]":
    result = subprocess.run(
        args,
        cwd=cwd,
        capture_output=capture,
        text=True,
    )
    if check and result.returncode != 0:
        stderr = result.stderr.strip() if result.stderr else ""
        stdout = result.stdout.strip() if result.stdout else ""
        details = stderr or stdout or f"Commande échouée : {' '.join(args)}"
        raise RuntimeError(details)
    return result


def _require_command(command: str, label: str | None = None) -> None:
    if shutil.which(command) is None:
        sys.exit(f"Erreur : prérequis manquant : {label or command}")


def _venv_python(project_dir: str) -> str:
    if os.name == "nt":
        return os.path.join(project_dir, ".venv", "Scripts", "python.exe")
    return os.path.join(project_dir, ".venv", "bin", "python")


def _venv_activate_hint() -> str:
    if os.name == "nt":
        return r".venv\Scripts\activate"
    return "source .venv/bin/activate"


def _safe_remove_git(dest: str) -> None:
    git_dir = os.path.join(dest, ".git")
    if os.path.isdir(git_dir):
        shutil.rmtree(git_dir, ignore_errors=True)


# ── Étapes d'initialisation ───────────────────────────────────────────────────

def _materialize_skeleton(dest: str) -> None:
    """Matérialise le squelette de projet nu (ADR-024).

    Copie l'arbre curé `cli/skeleton/data/` dans le projet — plus de
    clone du dépôt. Le `core` du projet vient ensuite du paquet `forge-mvc`
    (voir requirements.txt du squelette).
    """
    _print_step("Création du projet à partir du squelette Forge...")
    from cli.skeleton import materialize
    materialize(dest)


def _configure_env_files(dest: str, project_name: str) -> None:
    _print_step("Configuration des fichiers d'environnement...")

    example_path = os.path.join(dest, "env", "example")
    if not os.path.exists(example_path):
        raise RuntimeError("Fichier introuvable : env/example")

    with open(example_path, "r", encoding="utf-8") as file:
        content = file.read()

    # ADR-060 : le squelette est livré sans backend BDD ; la configuration de
    # connexion appartient au backend installé et n'est plus injectée ici.
    # forge new ne renseigne que le nom applicatif.
    content = re.sub(
        r"^APP_NAME=.*$",
        f"APP_NAME={project_name}",
        content,
        flags=re.MULTILINE,
    )

    with open(example_path, "w", encoding="utf-8") as file:
        file.write(content)

    # env/dev reprend le même contenu qu'env/example (nom applicatif substitué).
    dev_content = content

    dev_path = os.path.join(dest, "env", "dev")
    with open(dev_path, "w", encoding="utf-8") as file:
        file.write(dev_content)

    # env/prod : en production derrière Nginx, Forge écoute en HTTP local
    # (le proxy termine TLS). On force donc APP_SSL_ENABLED=false.
    prod_content, replaced = re.subn(
        r"^#?\s*APP_SSL_ENABLED=.*$",
        "APP_SSL_ENABLED=false",
        dev_content,
        flags=re.MULTILINE,
    )
    if replaced == 0:
        prod_content = prod_content.rstrip("\n") + "\nAPP_SSL_ENABLED=false\n"

    prod_path = os.path.join(dest, "env", "prod")
    with open(prod_path, "w", encoding="utf-8") as file:
        file.write(prod_content)


def _setup_python_environment(dest: str) -> None:
    _print_step("Création de l'environnement virtuel Python...")
    _run([sys.executable, "-m", "venv", ".venv"], cwd=dest, check=True)

    venv_python = _venv_python(dest)

    _print_step("Mise à jour de pip...")
    _run([venv_python, "-m", "pip", "install", "--upgrade", "pip", "-q"], cwd=dest, check=True)

    # Mode dev (retour terrain) : si FORGE_DEV_SRC pointe vers un dépôt source
    # Forge, on installe forge-mvc en ÉDITABLE depuis ce dépôt au lieu de la
    # version PyPI épinglée par requirements.txt. Le projet généré exécute alors
    # le working tree, pas la version publiée. Explicite et opt-in (principe 3).
    dev_src = os.environ.get("FORGE_DEV_SRC")
    if dev_src and os.path.isdir(dev_src):
        _print_step(f"Mode dev : forge-mvc en éditable depuis {dev_src}...")
        _run([venv_python, "-m", "pip", "install", "-e", dev_src, "-q"], cwd=dest, check=True)
        return

    requirements_path = os.path.join(dest, "requirements.txt")
    if os.path.exists(requirements_path):
        _print_step("Installation des dépendances Python...")
        _run([venv_python, "-m", "pip", "install", "-r", "requirements.txt", "-q"], cwd=dest, check=True)


def _setup_node_environment(dest: str) -> list[str]:
    warnings: list[str] = []
    package_json = os.path.join(dest, "package.json")
    if not os.path.exists(package_json):
        return warnings

    if shutil.which("npm") is None:
        warnings.append("Node.js / npm absent — relance 'npm install && npm run build:css' pour compiler Tailwind")
        return warnings

    _print_step("Installation des dépendances Node.js...")
    _run(["npm", "install"], cwd=dest, check=True)

    _print_step("Compilation du CSS Tailwind...")
    result = _run(["npm", "run", "build:css"], cwd=dest, capture=True)
    if result.returncode != 0:
        warnings.append("build:css a échoué — relance 'npm run build:css' après avoir configuré Tailwind")

    return warnings


def _generate_certificates(dest: str) -> None:
    cert_path = os.path.join(dest, "cert.pem")
    key_path = os.path.join(dest, "key.pem")

    if os.path.exists(cert_path) and os.path.exists(key_path):
        return

    _print_step("Génération des certificats SSL...")
    _run(
        [
            "openssl", "req",
            "-x509",
            "-newkey", "rsa:2048",
            "-keyout", "key.pem",
            "-out", "cert.pem",
            "-days", "365",
            "-nodes",
            "-subj", "/CN=localhost",
        ],
        cwd=dest,
        capture=True,
        check=True,
    )



def _reinitialize_git(dest: str, project_name: str) -> None:
    _print_step("Réinitialisation du dépôt Git...")
    _safe_remove_git(dest)
    _run(["git", "init", "-q"], cwd=dest, check=True)
    _run(["git", "add", "-A"], cwd=dest, check=True)

    result = _run(
        ["git", "commit", "-q", "-m", f"init: {project_name} — based on Forge {_FORGE_VERSION}"],
        cwd=dest,
        capture=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Impossible de créer le commit initial Git. "
            "Vérifie que user.name et user.email sont configurés."
        )


def _warn_initial_git_failed(exc: Exception) -> None:
    print()
    print("  Attention : le commit Git initial n’a pas pu être créé.")
    print(f"  Détail : {exc}")
    print("  Le projet est conservé. Configurez Git avec :")
    print('    git config --global user.name "Votre nom"')
    print('    git config --global user.email "votre.email@example.com"')
    print("  Puis lancez :")
    print("    git add .")
    print('    git commit -m "Initial commit"')


# ── Commande : new ────────────────────────────────────────────────────────────

def cmd_new(
    project_name: str,
    profile: str = DEFAULT_PROJECT_PROFILE,
) -> None:
    if not re.match(r"^[A-Za-z][A-Za-z0-9_-]*$", project_name):
        sys.exit(
            f"Erreur : nom invalide '{project_name}'.\n"
            "Utilisez uniquement lettres, chiffres, _ ou - et commencez par une lettre."
        )

    if profile not in SUPPORTED_PROJECT_PROFILES:
        profiles_list = ", ".join(SUPPORTED_PROJECT_PROFILES)
        sys.exit(
            f"Profil inconnu : {profile}. "
            f"Profils disponibles : {profiles_list}."
        )

    _require_command("git")
    _require_command("openssl")

    dest = os.path.join(os.getcwd(), project_name)
    if os.path.exists(dest):
        sys.exit(f"Erreur : le dossier '{dest}' existe déjà.")

    print(f"\nForge {_FORGE_VERSION} — nouveau projet : {project_name} [profil : {profile}]\n")

    node_warnings = []
    agent_files: list[str] = []
    try:
        _materialize_skeleton(dest)
        _configure_env_files(dest, project_name)
        _setup_python_environment(dest)
        node_warnings = _setup_node_environment(dest)
        _generate_certificates(dest)
        Path(dest, "forge_profile.txt").write_text(profile + "\n", encoding="utf-8")
        # Couche guidance agent IA (ADR-047) : CLAUDE.md, AGENTS.md, ADR-001.
        from cli.agents import emit_app_agent_files
        agent_files = emit_app_agent_files(Path(dest))

    except Exception as exc:
        shutil.rmtree(dest, ignore_errors=True)
        sys.exit(f"\nErreur lors de l'initialisation : {exc}")

    git_initialized = True
    try:
        _reinitialize_git(dest, project_name)
    except Exception as exc:
        git_initialized = False
        _warn_initial_git_failed(exc)

    if git_initialized:
        print(f"\n  Projet '{project_name}' créé et initialisé dans ./{project_name}/\n")
    else:
        print(f"\n  Projet '{project_name}' créé avec succès dans ./{project_name}/\n")

    if node_warnings:
        print("  Avertissements :")
        for warning in node_warnings:
            print(f"    - {warning}")
        print()

    if agent_files:
        print("  Guidance agent IA (ADR-047) :")
        for created in agent_files:
            print(f"    - {created}")
        print()

    print("  Étapes suivantes :\n")
    print(f"    cd {project_name}")
    print(f"    {_venv_activate_hint()}")
    print("    forge doctor")
    print("    forge run")
    print()
    print("  Les premiers paliers tournent sans base de données.")
    print("  Pour la base de données : installez un backend (ex. pip install forge-mvc-sqlite),")
    print("  configurez son environnement dans env/dev, puis forge db:init.")
    print()

    dev_src = os.environ.get("FORGE_DEV_SRC")
    if dev_src and os.path.isdir(dev_src):
        print(f"  Mode dev (FORGE_DEV_SRC={dev_src}) : forge-mvc installé en éditable.")
        print("  Pour tester aussi un backend sur le working tree, installez-le en éditable :")
        print(f"    pip install -e {dev_src}/packages/forge-mvc-<backend>")
        print()


# ── Commande : help ───────────────────────────────────────────────────────────

def cmd_help() -> None:
    from cli._support.help import build_help
    print(build_help(_FORGE_VERSION))


def cmd_version() -> None:
    print(f"Forge {_FORGE_VERSION}")


def cmd_doctor() -> None:
    from cli.project.doctor import has_failures, print_report, run_all
    results = run_all(Path.cwd(), _FORGE_VERSION)
    print_report(results, _FORGE_VERSION)
    if has_failures(results):
        sys.exit(1)


def cmd_project_check() -> None:
    from cli.project.project_check import has_failures, print_check_report, run_project_check
    root = Path.cwd()
    if not (root / "app.py").exists() or not (root / "mvc").exists():
        cli_fail(
            "forge project:check doit être lancé depuis la racine d'un projet Forge.",
            hint="lance la commande depuis un dossier contenant app.py et mvc/, "
                 "ou crée un nouveau projet avec forge new <NomProjet>.",
        )
    results = run_project_check(root, _FORGE_VERSION)
    print_check_report(results, _FORGE_VERSION)
    if has_failures(results):
        sys.exit(1)


def cmd_project_audit() -> None:
    from cli.project.project_audit import has_failures, print_audit_report, run_project_audit
    root = Path.cwd()
    if not (root / "app.py").exists() or not (root / "mvc").exists():
        cli_fail(
            "forge project:audit doit être lancé depuis la racine d'un projet Forge.",
            hint="lance la commande depuis un dossier contenant app.py et mvc/, "
                 "ou crée un nouveau projet avec forge new <NomProjet>.",
        )
    results = run_project_audit(root, _FORGE_VERSION)
    print_audit_report(results, _FORGE_VERSION)
    if has_failures(results):
        sys.exit(1)


def cmd_routes_list() -> None:
    """Affiche les routes déclarées par le module APP_ROUTES_MODULE."""
    from cli.project.project_config import load_project_config, ProjectConfigError

    project_root = Path.cwd().resolve()
    try:
        config = load_project_config(project_root)
        routes_module_name = config.APP_ROUTES_MODULE
    except ProjectConfigError as exc:
        sys.exit(f"Erreur : {exc}")

    root_str = str(project_root)
    path_inserted = root_str not in sys.path
    if path_inserted:
        sys.path.insert(0, root_str)
    try:
        routes_module = importlib.import_module(routes_module_name)
        router = getattr(routes_module, "router")
    except Exception as exc:
        sys.exit(f"Erreur : impossible de charger les routes applicatives ({exc}).")

    entries = cast("list[Any]", router.iter_routes())
    if not entries:
        print("Aucune route déclarée.")
        return

    headers = ["METHOD", "PATH", "NAME", "PUBLIC", "CSRF", "API", "HANDLER"]
    rows: list[list[str]] = []
    for entry in entries:
        handler_name = getattr(entry.handler, "__qualname__", repr(entry.handler))
        method_val = cast("str | list[str]", entry.method)
        methods: list[str] = method_val if isinstance(method_val, list) else [method_val]
        csrf_required = any(entry.requires_csrf(method) for method in methods)
        rows.append([
            entry.method_label,
            entry.pattern,
            entry.name or "-",
            "oui" if entry.public else "non",
            "oui" if csrf_required else "non",
            "oui" if entry.api else "non",
            handler_name,
        ])

    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]
    print("  ".join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print("  ".join(value.ljust(widths[index]) for index, value in enumerate(row)))


# ── Dispatch ──────────────────────────────────────────────────────────────────

# ── Registre de dispatch des commandes du cœur (ADR-059) ─────────────────────
# Chaque commande déléguée à un sous-module cli.* est décrite par un lanceur.
# Le handler est invoqué via une lambda qui le résout dans les globals de
# forge.py au moment de l'appel : il reste patchable (les tests de routage font
# monkeypatch.setattr(forge, "<handler>")). Ajouter une commande déléguée se
# fait par une ligne de table, sans toucher la chaîne de dispatch.
_CoreRunner = Callable[[list[str]], None]
_CoreCall = Callable[[list[str]], Any]


def _delegate(
    call: _CoreCall,
    *,
    full: bool = False,
    exit_rc: bool = False,
    min_args: int = 0,
    label: str = "",
    missing_hint: str = "",
) -> _CoreRunner:
    def run(args: list[str]) -> None:
        if min_args and len(args) < min_args:
            cli_fail(f"argument manquant pour «forge {label}».", hint=missing_hint)
        rc = call(args if full else args[1:])
        if exit_rc and rc:
            sys.exit(rc)

    return run


def _lazy(
    module: str,
    *,
    attr: str = "main",
    full: bool = False,
    exit_rc: bool = False,
    no_args: bool = False,
) -> _CoreRunner:
    def run(args: list[str]) -> None:
        handler: Callable[..., Any] = getattr(importlib.import_module(module), attr)
        if no_args:
            handler()
            return
        rc = handler(args if full else args[1:])
        if exit_rc and rc:
            sys.exit(rc)

    return run


def _group(commands: tuple[str, ...], runner: _CoreRunner) -> dict[str, _CoreRunner]:
    return {name: runner for name in commands}


_MAKE_ENTITY_HINT = "indique le nom de l'entité. Exemple : forge make:entity Contact"
_MAKE_CRUD_HINT = "indique le nom de l'entité. Exemple : forge make:crud Contact"
_AUTH_COMMANDS = (
    "auth:init", "auth:doctor", "auth:status", "auth:list-sql",
    "auth:user:create", "auth:user:list", "auth:user:show", "auth:user:disable",
    "auth:user:enable", "auth:user:password", "auth:user:role:add",
    "auth:user:role:remove", "auth:user:roles",
)

CORE_COMMANDS: dict[str, _CoreRunner] = {
    "run": _delegate(lambda a: run_main(a)),
    "update": _delegate(lambda a: update_main(a), exit_rc=True),
    "make:entity": _delegate(
        lambda a: make_entity_main(a), min_args=2,
        label="make:entity", missing_hint=_MAKE_ENTITY_HINT,
    ),
    "make:crud": _delegate(
        lambda a: cmd_make_crud_main(a), min_args=2,
        label="make:crud", missing_hint=_MAKE_CRUD_HINT,
    ),
    "make:public-page": _delegate(lambda a: public_page_main(a)),
    "make:public-list": _delegate(lambda a: public_list_main(a)),
    "make:public-show": _delegate(lambda a: public_show_main(a)),
    "make:public-form": _delegate(lambda a: public_form_main(a)),
    "make:public-contact": _delegate(lambda a: public_contact_main(a)),
    "make:relation": _delegate(lambda a: make_relation_main(a)),
    "entity:validate": _delegate(lambda a: entity_validate_main(a)),
    "sync:entity": _delegate(lambda a: model_main(a), full=True),
    "js:init": _delegate(lambda a: front_main(a), full=True),
    **_group(("i18n:init", "i18n:check"), _delegate(lambda a: i18n_main(a), full=True)),
    **_group(_AUTH_COMMANDS, _delegate(lambda a: auth_main(a), full=True)),
    "agents:init": _lazy("cli.agents.cli", exit_rc=True),
    "opt-in:install": _lazy("cli.optins.install", exit_rc=True),
    "opt-in:enable": _lazy("cli.optins.enable", exit_rc=True),
    "opt-in:list": _lazy("cli.optins.list", exit_rc=True),
    "opt-in:remove": _lazy("cli.optins.remove", exit_rc=True),
    "opt-in:disable": _lazy("cli.optins.disable", exit_rc=True),
    **_group(
        ("module:list", "module:install", "module:files", "module:routes", "module:remove"),
        _delegate(lambda a: modules_main(a), full=True),
    ),
    "docs:pdf": _lazy("cli.docs.quarkdown", attr="build_pdf", no_args=True),
    **_group(
        ("sync:relations", "build:model", "check:model"),
        _delegate(lambda a: model_main(a), full=True),
    ),
    **_group(
        ("migration:status", "migration:apply", "migration:make", "migration:diff"),
        _delegate(lambda a: migrations_main(a), full=True),
    ),
    "schema:list": _lazy("cli.schemas.schema_list", attr="schema_list_main"),
    "schema:doctor": _lazy("cli.schemas.schema_doctor", attr="schema_doctor_main"),
}


def dispatch_core(command: str, args: list[str]) -> bool:
    """Exécute une commande déléguée du cœur si elle figure dans la table."""
    runner = CORE_COMMANDS.get(command)
    if runner is None:
        return False
    runner(args)
    return True


def main() -> None:
    args = sys.argv[1:]

    if args and args[0] == "--version":
        cmd_version()
        return

    if not args or args[0] in ("help", "--help", "-h"):
        cmd_help()
        return

    command = args[0]

    # Garde-fou central CLI-HELP-FLAGS-DISPATCHER-001 : intercepte --help/-h
    # avant toute exécution métier pour les commandes connues sans support
    # --help natif (cf. cli/_support/help_dispatch.py et l'audit
    # docs/history/audits/cli-help-flags-audit-001.md).
    if wants_help(args[1:]):
        help_text = format_command_help(command)
        if help_text is not None:
            print(help_text)
            return

    if command == "new":
        if len(args) < 2:
            cli_fail(
                "argument manquant pour «forge new».",
                hint="indique le nom du projet. Exemple : forge new GestionVentes",
            )
        profile = DEFAULT_PROJECT_PROFILE
        remaining = args[2:]
        # CLI-NEW-UNKNOWN-ARGS-001 : on consomme uniquement `--profile <valeur>`
        # et on refuse explicitement tout autre argument, plutôt que de l'ignorer
        # silencieusement (une option mal orthographiée doit échouer, pas passer).
        consumed: set[int] = set()
        if "--profile" in remaining:
            idx = remaining.index("--profile")
            consumed.add(idx)
            if idx + 1 < len(remaining):
                profile = remaining[idx + 1]
                consumed.add(idx + 1)
            else:
                cli_fail(
                    "argument manquant pour «forge new».",
                    hint="indique le profil après --profile. Profils disponibles : "
                         + ", ".join(SUPPORTED_PROJECT_PROFILES),
                )
        unexpected = [tok for i, tok in enumerate(remaining) if i not in consumed]
        if unexpected:
            cli_fail(
                "argument inconnu pour «forge new» : " + ", ".join(unexpected) + ".",
                hint="usage : forge new <NomDuProjet> [--profile <profil>]. "
                     "Profils disponibles : " + ", ".join(SUPPORTED_PROJECT_PROFILES),
            )
        cmd_new(args[1], profile=profile)
        return

    if command == "make:pivot-crud":
        if len(args) < 3:
            cli_fail(
                "arguments manquants pour «forge make:pivot-crud».",
                hint="indique l'entité source et le nom de la relation. Exemple : forge make:pivot-crud Article tags",
            )
        try:
            from forge_mvc_pivot.make_pivot_crud import cmd_make_pivot_crud_main
        except ImportError:
            cli_fail(
                "module forge-mvc-pivot non installé.",
                hint="installe le module opt-in : pip install --pre forge-mvc-pivot",
            )
        cmd_make_pivot_crud_main(args[1:])
        return

    if command == "db:init":
        db_init_main([command])
        return

    if command == "db:apply":
        if "--help" in args:
            print("Usage : forge db:apply")
            print()
            print("Applique le SQL de toutes les entités du projet (mvc/entities/) à la base.")
            print("Requiert un backend BDD installé et une base configurée (voir forge db:init).")
            raise SystemExit(0)
        db_apply_main([command])
        return

    if command == "routes:list":
        if len(args) != 1:
            cli_fail(
                "trop d'arguments pour «forge routes:list».",
                hint="la commande ne prend pas d'argument. Utilise simplement : forge routes:list",
            )
        cmd_routes_list()
        return

    if command == "doctor":
        cmd_doctor()
        return

    if command == "project:check":
        cmd_project_check()
        return

    if command == "project:audit":
        cmd_project_audit()
        return

    # Commandes du cœur déléguées à un sous-module cli.* (ADR-059) : table de
    # dispatch, puis commandes livrées par les opt-ins.
    if dispatch_core(command, args):
        return

    if dispatch_optin(command, args):
        return

    # ADR-059 : les commandes opt-in sont découvertes par entry points ; une
    # commande namespacée inconnue provient souvent d'un opt-in non installé.
    hint = "lancez «forge help» pour afficher les commandes disponibles."
    if ":" in command:
        hint = (
            "lancez «forge help» pour la liste des commandes. Si «" + command
            + "» provient d'un module opt-in, installez-le "
            "(voir «forge opt-in:list» ou la doc des opt-ins)."
        )
    cli_fail(f"commande inconnue : «{command}».", hint=hint)


def cli_entrypoint() -> None:
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterruption utilisateur. Commande annulée.", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    cli_entrypoint()
