#!/usr/bin/env python3
"""
forge.py — CLI officielle de Forge

Usage :
    forge new NomProjet
    forge make:entity NomEntite
    forge make:crud NomEntite [--dry-run]
    forge make:relation
    forge sync:entity NomEntite
    forge sync:relations
    forge sync:landing [--check]
    forge upload:init
    forge build:model
    forge check:model
    forge db:init
    forge db:apply
    forge routes:list
    forge deploy:init
    forge deploy:check
    forge starter:list
    forge doctor
    forge help

Exemples :
    forge new GestionVentes
    forge make:entity Contact
    forge make:crud Contact
    forge make:crud Contact --dry-run
"""

import os
import re
import sys
import shutil
import subprocess
import importlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from forge_cli.entities.db_apply import main as db_apply_main
from forge_cli.entities.db_init import main as db_init_main
from forge_cli.entities.make_entity import main as make_entity_main
from forge_cli.entities.make_relation import main as make_relation_main
from forge_cli.entities.make_crud import cmd_make_crud_main
from forge_cli.entities.model import main as model_main
from forge_cli.sync_landing import main as sync_landing_main
from forge_cli.uploads import main as upload_main
from forge_cli.deploy import main as deploy_main
from forge_cli.starters import main as starters_main


_FORGE_REPO = "https://github.com/caucrogeGit/Forge.git"
_FORGE_VERSION = "main"
_FORGE_DEFAULT_BRANCH = "main"


# ── Utilitaires ───────────────────────────────────────────────────────────────

def _to_snake(name: str) -> str:
    """CamelCase ou kebab-case → snake_case."""
    name = name.replace("-", "_")
    name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    name = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", name)
    return name.lower()


def _print_step(message: str) -> None:
    print(f"  {message}")


def _run(args, cwd=None, capture=False, check=False):
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

def _clone_skeleton(dest: str, ref: str | None = None) -> None:
    _print_step("Clonage du squelette Forge...")
    branch = ref or _FORGE_DEFAULT_BRANCH
    result = _run(
        ["git", "clone", "--branch", branch, "--depth=1", "--quiet", _FORGE_REPO, dest],
        capture=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Échec du clonage Git.")


def _configure_env_files(dest: str, project_name: str, db_name: str) -> None:
    _print_step("Configuration des fichiers d'environnement...")

    example_path = os.path.join(dest, "env", "example")
    if not os.path.exists(example_path):
        raise RuntimeError("Fichier introuvable : env/example")

    with open(example_path, "r", encoding="utf-8") as file:
        content = file.read()

    content = re.sub(
        r"^APP_NAME=.*$",
        f"APP_NAME={project_name}",
        content,
        flags=re.MULTILINE,
    )
    content = re.sub(
        r"^DB_NAME=.*$",
        f"DB_NAME={db_name}",
        content,
        flags=re.MULTILINE,
    )

    with open(example_path, "w", encoding="utf-8") as file:
        file.write(content)

    app_login = _to_snake(project_name) + "_app"
    dev_content = re.sub(
        r"^DB_APP_LOGIN=.*$",
        f"DB_APP_LOGIN={app_login}",
        content,
        flags=re.MULTILINE,
    )

    dev_path = os.path.join(dest, "env", "dev")
    with open(dev_path, "w", encoding="utf-8") as file:
        file.write(dev_content)


def _setup_python_environment(dest: str) -> None:
    _print_step("Création de l'environnement virtuel Python...")
    _run([sys.executable, "-m", "venv", ".venv"], cwd=dest, check=True)

    venv_python = _venv_python(dest)

    _print_step("Mise à jour de pip...")
    _run([venv_python, "-m", "pip", "install", "--upgrade", "pip", "-q"], cwd=dest, check=True)

    requirements_path = os.path.join(dest, "requirements.txt")
    if os.path.exists(requirements_path):
        _print_step("Installation des dépendances Python...")
        _run([venv_python, "-m", "pip", "install", "-r", "requirements.txt", "-q"], cwd=dest, check=True)


def _setup_node_environment(dest: str) -> list[str]:
    warnings = []
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


# ── Commande : new ────────────────────────────────────────────────────────────

def cmd_new(project_name: str, ref: str | None = None) -> None:
    if not re.match(r"^[A-Za-z][A-Za-z0-9_-]*$", project_name):
        sys.exit(
            f"Erreur : nom invalide '{project_name}'.\n"
            "Utilisez uniquement lettres, chiffres, _ ou - et commencez par une lettre."
        )

    _require_command("git")
    _require_command("openssl")

    dest = os.path.join(os.getcwd(), project_name)
    if os.path.exists(dest):
        sys.exit(f"Erreur : le dossier '{dest}' existe déjà.")

    db_name = _to_snake(project_name) + "_db"

    print(f"\nForge {_FORGE_VERSION} — nouveau projet : {project_name}\n")

    node_warnings = []
    try:
        _clone_skeleton(dest, ref=ref)
        _configure_env_files(dest, project_name, db_name)
        _setup_python_environment(dest)
        node_warnings = _setup_node_environment(dest)
        _generate_certificates(dest)
        _reinitialize_git(dest, project_name)

    except Exception as exc:
        shutil.rmtree(dest, ignore_errors=True)
        sys.exit(f"\nErreur lors de l'initialisation : {exc}")

    print(f"\n  Projet '{project_name}' créé et initialisé dans ./{project_name}/\n")

    if node_warnings:
        print("  Avertissements :")
        for warning in node_warnings:
            print(f"    - {warning}")
        print()

    print("  Étapes suivantes :\n")
    print(f"    cd {project_name}")
    print(f"    {_venv_activate_hint()}")
    print("    forge doctor")
    print("    # Ajustez env/dev si nécessaire (DB_ADMIN_PWD, DB_APP_PWD…)")
    print("    forge db:init")
    print("    python app.py\n")


# ── Commande : help ───────────────────────────────────────────────────────────

def cmd_help() -> None:
    print(__doc__)


def cmd_doctor() -> None:
    from forge_cli.doctor import has_failures, print_report, run_all
    results = run_all(Path.cwd(), _FORGE_VERSION)
    print_report(results, _FORGE_VERSION)
    if has_failures(results):
        sys.exit(1)


def cmd_routes_list() -> None:
    """Affiche les routes déclarées par le module APP_ROUTES_MODULE."""
    from forge_cli.project_config import load_project_config, ProjectConfigError

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

    entries = router.iter_routes()
    if not entries:
        print("Aucune route déclarée.")
        return

    headers = ["METHOD", "PATH", "NAME", "PUBLIC", "CSRF", "API", "HANDLER"]
    rows = []
    for entry in entries:
        handler_name = getattr(entry.handler, "__qualname__", repr(entry.handler))
        methods = entry.method if isinstance(entry.method, list) else [entry.method]
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

def main() -> None:
    args = sys.argv[1:]

    if not args or args[0] in ("help", "--help", "-h"):
        cmd_help()
        return

    command = args[0]

    if command == "new":
        if len(args) < 2:
            sys.exit("Usage : forge new NomProjet [--ref <branche>]")
        ref = None
        remaining = args[2:]
        if "--ref" in remaining:
            idx = remaining.index("--ref")
            if idx + 1 < len(remaining):
                ref = remaining[idx + 1]
            else:
                sys.exit("Usage : forge new NomProjet [--ref <branche>]")
        cmd_new(args[1], ref=ref)
        return

    if command == "make:entity":
        make_entity_main(args[1:])
        return
    if command == "make:crud":
        if len(args) < 2:
            sys.exit("Usage : forge make:crud NomEntite [--dry-run]")
        cmd_make_crud_main(args[1:])
        return
    if command == "make:relation":
        make_relation_main(args[1:])
        return

    if command == "sync:entity":
        model_main(args)
        return

    if command == "sync:landing":
        sync_landing_main(args)
        return

    if command == "upload:init":
        upload_main(args)
        return

    if command in ("deploy:init", "deploy:check"):
        deploy_main(args)
        return

    if command == "starter:list":
        starters_main(args)
        return

    if command in {"sync:relations", "build:model", "check:model"}:
        model_main(args)
        return

    if command == "db:init":
        db_init_main([command])
        return

    if command == "db:apply":
        db_apply_main([command])
        return

    if command == "routes:list":
        if len(args) != 1:
            sys.exit("Usage : forge routes:list")
        cmd_routes_list()
        return

    if command == "doctor":
        cmd_doctor()
        return

    sys.exit(f"Commande inconnue : '{command}'. Voir : forge help")


def cli_entrypoint() -> None:
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterruption utilisateur. Commande annulée.", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    cli_entrypoint()
