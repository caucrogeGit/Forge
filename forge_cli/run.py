"""Commande `forge run` — point d'entrée officiel pour lancer Forge.

Tickets :
    FORGE-RUN-COMMAND-001  — commande officielle, dev/prod.
    DEV-SERVER-AUTORELOAD-001 — autoreload par redémarrage de processus en dev.

Comportement :
    - APP_ENV=dev (défaut)
        - sans --no-reload (défaut) : superviseur DevReloader
          (`forge_cli.dev_reloader`) qui spawne `python app.py` et le
          redémarre quand un fichier surveillé change ;
        - avec --no-reload : délègue à `scripts/dev-server.sh` (POSIX) ;
          fallback : `python app.py`.
    - APP_ENV=prod : refus du serveur intégré + message WSGI (Gunicorn +
      reverse proxy). Ne mentionne jamais `python app.py`. Exit 1.

Hors périmètre (tickets suivants) :
    - lancement automatique de Gunicorn par `forge run` ;
    - live reload navigateur, WebSocket, reload partiel.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from forge_cli.errors import cli_fail


_VALID_ENVS = ("dev", "prod")


def _parse_env(args: list[str]) -> str:
    """Détermine l'environnement effectif pour le lancement.

    Priorité : flag `--env <valeur>` > variable APP_ENV > défaut "dev".
    """
    if "--env" in args:
        idx = args.index("--env")
        if idx + 1 >= len(args):
            cli_fail(
                "argument manquant pour «forge run --env».",
                hint=f"indique la valeur après --env. Exemple : forge run --env dev "
                     f"(valeurs : {', '.join(_VALID_ENVS)}).",
            )
        candidate = args[idx + 1]
        if candidate not in _VALID_ENVS:
            cli_fail(
                f"valeur d'environnement inconnue : {candidate!r}.",
                hint=f"valeurs acceptées : {', '.join(_VALID_ENVS)}.",
            )
        return candidate
    return os.environ.get("APP_ENV", "dev")


def _parse_reload(args: list[str]) -> bool:
    """True si l'autoreload est actif (défaut). False si `--no-reload`."""
    return "--no-reload" not in args


def _check_project_root(root: Path) -> None:
    if not (root / "app.py").exists() or not (root / "mvc").is_dir():
        cli_fail(
            "forge run doit être lancé depuis la racine d'un projet Forge.",
            hint="lance la commande depuis un dossier contenant app.py et mvc/, "
                 "ou crée un nouveau projet avec forge new <NomProjet>.",
        )


def _format_prod_refusal() -> str:
    """Message imprimé en mode prod — pas d'exécution.

    Ne mentionne PAS `python app.py` comme solution. La voie supportée
    est WSGI + Gunicorn + reverse proxy (voir docs/deployment/wsgi-deployment.md).
    """
    return (
        "forge run refuse de démarrer le serveur intégré en production.\n"
        "\n"
        "  APP_ENV = 'prod'\n"
        "\n"
        "En production, Forge s'expose via WSGI derrière un reverse proxy :\n"
        "\n"
        "  gunicorn --workers 1 --bind 127.0.0.1:8000 \\\n"
        "      'core.wsgi:create_configured_wsgi_app()'\n"
        "\n"
        "Nginx ou Caddy terminent HTTPS et reverse-proxy vers Gunicorn.\n"
        "\n"
        "Voir :\n"
        "  - docs/deployment/wsgi-deployment.md\n"
        "  - docs/deployment/production-limits.md\n"
        "  - forge deploy:init  (génère nginx/forge-app.conf + systemd)\n"
    )


def _run_dev_legacy(root: Path) -> int:
    """Lancement dev sans autoreload (`--no-reload`).

    Délègue à `scripts/dev-server.sh` (POSIX uniquement) quand il existe ;
    sinon `python app.py` directement.
    """
    dev_script = root / "scripts" / "dev-server.sh"
    if dev_script.is_file() and os.name != "nt":
        return subprocess.run(["bash", str(dev_script)], cwd=str(root)).returncode

    app_py = root / "app.py"
    return subprocess.run([sys.executable, str(app_py)], cwd=str(root)).returncode


def _run_dev_with_reloader(root: Path) -> int:
    """Lancement dev avec autoreload (défaut)."""
    # Import paresseux : aucune dépendance circulaire avec forge_cli.run.
    from forge_cli.dev_reloader import DevReloader

    reloader = DevReloader(root)
    return reloader.run()


def cmd_run(args: list[str]) -> None:
    """Implémente `forge run [--env dev|prod] [--no-reload]`."""
    env = _parse_env(args)
    reload_enabled = _parse_reload(args)
    root = Path.cwd().resolve()
    _check_project_root(root)

    if env == "prod":
        sys.stderr.write(_format_prod_refusal())
        sys.exit(1)

    # APP_ENV=dev — propagé au sous-processus.
    os.environ.setdefault("APP_ENV", "dev")
    mode = "autoreload" if reload_enabled else "no-reload"
    print(f"forge run — APP_ENV=dev [{mode}] ({root})")
    code = (
        _run_dev_with_reloader(root)
        if reload_enabled
        else _run_dev_legacy(root)
    )
    if code != 0:
        sys.exit(code)


def main(args: list[str]) -> None:
    cmd_run(args)
