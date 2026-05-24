#!/usr/bin/env python3
"""forge.py — CLI officielle de Forge. Aide : forge help"""

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
from forge_cli.entities.migrations import main as migrations_main
from forge_cli.entities.make_entity import main as make_entity_main
from forge_cli.entities.make_relation import main as make_relation_main
from forge_cli.entities.make_crud import cmd_make_crud_main
from forge_cli.entities.model import main as model_main
from forge_cli.entities.entity_validate import main as entity_validate_main
from forge_cli.public_contact import main as public_contact_main
from forge_cli.public_form import main as public_form_main
from forge_cli.public_list import main as public_list_main
from forge_cli.public_page import main as public_page_main
from forge_cli.public_show import main as public_show_main
from forge_cli.sync_landing import main as sync_landing_main
from forge_cli.uploads import main as upload_main
from forge_cli.front import main as front_main
from forge_cli.auth import main as auth_main
from forge_cli.mail import main as mail_main
from forge_cli.deploy import main as deploy_main
from forge_cli.i18n import main as i18n_main
from forge_cli.starters import main as starters_main  # noqa: E402 (package replaces starters.py)
from forge_cli.modules import main as modules_main
from forge_cli.project_profiles import (
    SUPPORTED_PROJECT_PROFILES,
    DEFAULT_PROJECT_PROFILE,
)
from forge_cli.errors import cli_fail
from forge_cli.help_dispatch import format_command_help, wants_help


_FORGE_REPO = "https://github.com/caucrogeGit/Forge.git"
_FORGE_VERSION = "1.0.0b8"
_FORGE_DEFAULT_REF = "v1.0.0-beta.8"


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
    branch = ref or _FORGE_DEFAULT_REF
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

def _apply_starter_to_new_project(dest: str, starter_id: str) -> None:
    """Copie les fichiers d'un starter skeleton dans un projet neuf et injecte ses routes."""
    from forge_cli.starters._exceptions import StarterBuildError
    from forge_cli.starters.registry import StarterNotFound, resolve
    from forge_cli.starters.route_ops import inject_block, read_snippet, replace_home_route

    try:
        meta = resolve(starter_id)
    except StarterNotFound:
        print(f"\n  Attention : starter inconnu '{starter_id}' — ignoré.")
        return

    if meta.get("status") != "available":
        print(f"\n  Attention : starter '{starter_id}' non disponible — ignoré.")
        return

    if meta.get("requires_db"):
        print(f"\n  Attention : le starter '{starter_id}' nécessite une base de données.")
        print("  Lancez 'forge db:init' puis 'forge starter:build' depuis le projet.")
        return

    root = Path(dest)
    files_dir = meta["_dir"] / "files"

    if files_dir.exists():
        for src in files_dir.rglob("*"):
            if src.is_file() and "__pycache__" not in src.parts and src.suffix != ".pyc":
                rel = src.relative_to(files_dir)
                dst = root / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

    routes_py = root / "mvc" / "routes.py"
    if routes_py.exists():
        try:
            block = read_snippet(meta)
        except StarterBuildError as exc:
            print(f"\n  Attention : snippet de routes introuvable ({exc}) — routes non injectées.")
            return
        inject_block(routes_py, block)
        home = meta.get("home_route")
        if home and home != "/":
            replace_home_route(routes_py, home)

    _print_step(f"Starter '{meta['name']}' appliqué.")


def cmd_new(
    project_name: str,
    ref: str | None = None,
    profile: str = DEFAULT_PROJECT_PROFILE,
    starter: str | None = None,
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

    db_name = _to_snake(project_name) + "_db"

    print(f"\nForge {_FORGE_VERSION} — nouveau projet : {project_name} [profil : {profile}]\n")

    node_warnings = []
    try:
        _clone_skeleton(dest, ref=ref)
        _configure_env_files(dest, project_name, db_name)
        _setup_python_environment(dest)
        node_warnings = _setup_node_environment(dest)
        _generate_certificates(dest)
        Path(dest, "forge_profile.txt").write_text(profile + "\n", encoding="utf-8")
        if starter:
            _apply_starter_to_new_project(dest, starter)

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

    print("  Étapes suivantes :\n")
    print(f"    cd {project_name}")
    print(f"    {_venv_activate_hint()}")
    print("    forge doctor")
    if not starter:
        print("    # Ajustez env/dev si nécessaire (DB_ADMIN_PWD, DB_APP_PWD…)")
        print("    forge db:init")
    open_url = None
    if starter:
        from forge_cli.starters.registry import resolve, StarterNotFound
        try:
            open_url = resolve(starter).get("open_url")
        except StarterNotFound:
            pass
    print("    python app.py")
    if open_url:
        print(f"    # Ouvrir : {open_url}\n")
    else:
        print()


# ── Commande : help ───────────────────────────────────────────────────────────

def cmd_help() -> None:
    from forge_cli.help import build_help
    print(build_help(_FORGE_VERSION))


def cmd_version() -> None:
    print(f"Forge {_FORGE_VERSION}")


def cmd_doctor() -> None:
    from forge_cli.doctor import has_failures, print_report, run_all
    results = run_all(Path.cwd(), _FORGE_VERSION)
    print_report(results, _FORGE_VERSION)
    if has_failures(results):
        sys.exit(1)


def cmd_project_check() -> None:
    from forge_cli.project_check import has_failures, print_check_report, run_project_check
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
    from forge_cli.project_audit import has_failures, print_audit_report, run_project_audit
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

    if args and args[0] == "--version":
        cmd_version()
        return

    if not args or args[0] in ("help", "--help", "-h"):
        cmd_help()
        return

    command = args[0]

    # Garde-fou central CLI-HELP-FLAGS-DISPATCHER-001 : intercepte --help/-h
    # avant toute exécution métier pour les commandes connues sans support
    # --help natif (cf. forge_cli/help_dispatch.py et l'audit
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
        ref = None
        profile = DEFAULT_PROJECT_PROFILE
        remaining = args[2:]
        if "--ref" in remaining:
            idx = remaining.index("--ref")
            if idx + 1 < len(remaining):
                ref = remaining[idx + 1]
            else:
                cli_fail(
                    "argument manquant pour «forge new».",
                    hint="indique la branche après --ref. Exemple : forge new GestionVentes --ref main",
                )
        if "--profile" in remaining:
            idx = remaining.index("--profile")
            if idx + 1 < len(remaining):
                profile = remaining[idx + 1]
            else:
                cli_fail(
                    "argument manquant pour «forge new».",
                    hint="indique le profil après --profile. Profils disponibles : "
                         + ", ".join(SUPPORTED_PROJECT_PROFILES),
                )
        starter = None
        if "--starter" in remaining:
            idx = remaining.index("--starter")
            if idx + 1 < len(remaining):
                starter = remaining[idx + 1]
            else:
                cli_fail(
                    "argument manquant pour «forge new».",
                    hint="indique l'identifiant du starter après --starter. Exemple : forge new MonProjet --starter welcome",
                )
        cmd_new(args[1], ref=ref, profile=profile, starter=starter)
        return

    if command == "make:entity":
        if len(args) < 2:
            cli_fail(
                "argument manquant pour «forge make:entity».",
                hint="indique le nom de l'entité. Exemple : forge make:entity Contact",
            )
        make_entity_main(args[1:])
        return
    if command == "make:crud":
        if len(args) < 2:
            cli_fail(
                "argument manquant pour «forge make:crud».",
                hint="indique le nom de l'entité. Exemple : forge make:crud Contact",
            )
        cmd_make_crud_main(args[1:])
        return
    if command == "make:public-page":
        public_page_main(args[1:])
        return
    if command == "make:public-list":
        public_list_main(args[1:])
        return
    if command == "make:public-show":
        public_show_main(args[1:])
        return
    if command == "make:public-form":
        public_form_main(args[1:])
        return
    if command == "make:public-contact":
        public_contact_main(args[1:])
        return
    if command == "make:relation":
        make_relation_main(args[1:])
        return
    if command == "make:pivot-crud":
        if len(args) < 3:
            cli_fail(
                "arguments manquants pour «forge make:pivot-crud».",
                hint="indique l'entité source et le nom de la relation. Exemple : forge make:pivot-crud Article tags",
            )
        from forge_cli.entities.make_pivot_crud import cmd_make_pivot_crud_main
        cmd_make_pivot_crud_main(args[1:])
        return

    if command == "entity:validate":
        entity_validate_main(args[1:])
        return

    if command == "sync:entity":
        model_main(args)
        return

    if command == "sync:landing":
        sync_landing_main(args)
        return

    if command in ("upload:init", "media:init"):
        upload_main(args)
        return

    if command == "js:init":
        front_main(args)
        return

    if command in ("i18n:init", "i18n:check"):
        i18n_main(args)
        return

    if command in (
        "auth:init",
        "auth:doctor",
        "auth:status",
        "auth:list-sql",
        "auth:user:create",
        "auth:user:list",
        "auth:user:show",
        "auth:user:disable",
        "auth:user:enable",
        "auth:user:password",
        "auth:user:role:add",
        "auth:user:role:remove",
        "auth:user:roles",
    ):
        auth_main(args)
        return

    if command in ("mail:init", "mail:test", "mail:render", "mail:doctor", "mail:logs"):
        mail_main(args)
        return

    if command in ("deploy:init", "deploy:check"):
        deploy_main(args)
        return

    if command == "starter:list":
        starters_main(args)
        return
    if command == "starter:build":
        if len(args) < 2:
            cli_fail(
                "argument manquant pour «forge starter:build».",
                hint="indique l'identifiant du starter. Lance forge starter:list pour voir les disponibles.",
            )
        starters_main(args)
        return

    if command in ("module:list", "module:install", "module:files", "module:routes"):
        modules_main(args)
        return

    if command == "docs:pdf":
        from forge_cli.docs.quarkdown import build_pdf
        build_pdf()
        return

    if command in {"sync:relations", "build:model", "check:model"}:
        model_main(args)
        return

    if command == "db:init":
        db_init_main([command])
        return

    if command == "db:apply":
        if "--help" in args:
            print("Usage : forge db:apply")
            print()
            print("Applique le SQL de toutes les entités du projet (mvc/entities/) à la base.")
            print("Requiert une connexion MariaDB active (voir forge db:init).")
            raise SystemExit(0)
        db_apply_main([command])
        return

    if command in {"migration:status", "migration:apply", "migration:make", "migration:diff"}:
        migrations_main(args)
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

    if command == "schema:list":
        from forge_cli.schemas.schema_list import schema_list_main
        schema_list_main(args[1:])
        return

    if command == "schema:doctor":
        from forge_cli.schemas.schema_doctor import schema_doctor_main
        schema_doctor_main(args[1:])
        return

    if command == "rbac:validate":
        from forge_cli.rbac_validate import rbac_validate_main
        rbac_validate_main(args[1:])
        return

    if command == "rbac:audit":
        from forge_cli.rbac_audit import rbac_audit_main
        rbac_audit_main(args[1:])
        return

    cli_fail(
        f"commande inconnue : «{command}».",
        hint="lancez «forge help» pour afficher les commandes disponibles.",
    )


def cli_entrypoint() -> None:
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterruption utilisateur. Commande annulée.", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    cli_entrypoint()
