# pyright: strict
"""Commande forge update — met à jour Forge dans l'environnement courant.

Ticket : FORGE-UPDATE-COMMAND-001.

Cible : un utilisateur qui a un projet créé avec une ancienne beta
et veut s'assurer qu'il utilise bien la dernière version de Forge
dans son environnement Python courant (`.venv` ou pipx).

Modes :

- ``forge update``           : `pip install --upgrade forge-mvc`.
- ``forge update --pre``     : ajoute `--pre` (utile tant que Forge est en beta).
- ``forge update --check``   : affiche version installée + commande qui
                               serait lancée, ne modifie rien.
- ``forge update --dry-run`` : affiche la commande pip qui serait
                               exécutée, ne modifie rien.
- ``forge update --help``    : aide (interceptée en amont par le
                               dispatcher CLI via `format_command_help`).

Principes :

- ``sys.executable`` est utilisé pour rester dans l'environnement
  Python courant (`.venv` du projet, ou pipx isolé).
- Si Forge est installé via pipx (`sys.executable` sous
  ``~/.local/share/pipx/venvs/forge-mvc/``), la commande ne lance PAS
  pip mais affiche le bon `pipx upgrade …` à exécuter — pipx isole
  chaque app et `pip install` ne mettrait pas à jour l'install pipx
  globale.
- Aucun fichier projet n'est modifié, aucune migration n'est lancée,
  aucun fichier ``env/*`` n'est touché.
"""

from __future__ import annotations

import importlib.metadata
import os
import subprocess
import sys
from typing import Sequence


PACKAGE = "forge-mvc"


def _installed_version() -> str | None:
    """Retourne la version installée de forge-mvc, ou None si absent."""
    try:
        return importlib.metadata.version(PACKAGE)
    except importlib.metadata.PackageNotFoundError:
        return None


def _is_pipx_install() -> bool:
    """Détecte si Forge tourne depuis un venv pipx.

    Pipx isole chaque app sous ``~/.local/share/pipx/venvs/<app>/``
    (Linux/macOS) ou ``%LOCALAPPDATA%\\pipx\\pipx\\venvs\\<app>\\``
    (Windows). ``sys.executable`` y pointe directement quand la
    commande est lancée depuis pipx.
    """
    exe = os.path.realpath(sys.executable)
    # Normalise les séparateurs pour matcher Windows aussi
    norm = exe.replace("\\", "/")
    return "/pipx/venvs/" in norm


def _build_pip_command(pre: bool) -> list[str]:
    """Construit la commande pip à exécuter (liste pour subprocess).

    ``--disable-pip-version-check`` supprime la notice pip
    « A new release of pip is available » : elle concerne pip lui-même,
    pas Forge, et s'affiche juste avant « Version installée après »,
    ce qui prête à confusion dans la sortie de ``forge update``.
    """
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade",
           "--disable-pip-version-check"]
    if pre:
        cmd.append("--pre")
    cmd.append(PACKAGE)
    return cmd


def _pipx_command(pre: bool) -> str:
    """Commande pipx équivalente à afficher à l'utilisateur."""
    suffix = ' --pip-args="--pre"' if pre else ""
    return f"pipx upgrade {PACKAGE}{suffix}"


def _print_help() -> None:
    print(
        "forge update — met à jour Forge dans l'environnement courant\n"
        "\n"
        "Usage :\n"
        "  forge update [--pre] [--check] [--dry-run]\n"
        "\n"
        "Options :\n"
        "  --check    Affiche la version installée et la commande pip qui\n"
        "             serait lancée, sans rien modifier.\n"
        "  --dry-run  Affiche la commande pip qui serait exécutée, sans la lancer.\n"
        "  --pre      Autorise les versions de pré-release (utile tant que\n"
        "             Forge est en beta — défaut explicite recommandé).\n"
        "  -h, --help Affiche cette aide.\n"
        "\n"
        "Cas pipx : si Forge est installé via pipx, la commande affiche le\n"
        "bon `pipx upgrade forge-mvc` à exécuter au lieu de lancer pip."
    )


def _run_check(pre: bool) -> int:
    installed = _installed_version() or "(non installée)"
    print(f"Version installée : {installed}")
    if _is_pipx_install():
        print(f"Mise à jour pipx : {_pipx_command(pre)}")
    else:
        print("Commande pip qui serait lancée :")
        print("  " + " ".join(_build_pip_command(pre)))
    if not pre:
        print()
        print(
            "Astuce : Forge est encore en beta (1.0.0bN). Utilisez "
            "`forge update --pre` pour récupérer la dernière beta."
        )
    return 0


def _run_dry_run(pre: bool) -> int:
    print("[dry-run] Aucune action effectuée.")
    if _is_pipx_install():
        print("[dry-run] Commande pipx qui serait lancée :")
        print("  " + _pipx_command(pre))
    else:
        print("[dry-run] Commande pip qui serait lancée :")
        print("  " + " ".join(_build_pip_command(pre)))
    return 0


def _run_update(pre: bool) -> int:
    if _is_pipx_install():
        print(
            "Forge est installé via pipx — `pip install --upgrade` "
            "depuis ce venv isolé ne mettrait pas à jour l'install pipx "
            "globale. Lancez plutôt :"
        )
        print(f"  {_pipx_command(pre)}")
        return 1

    installed_before = _installed_version() or "(non installée)"
    print(f"Version installée avant : {installed_before}")

    cmd = _build_pip_command(pre)
    print(f"Lancement : {' '.join(cmd)}")

    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"\nErreur pip : exit {result.returncode}")
        return result.returncode

    # Re-import importlib.metadata pour récupérer la version après upgrade
    # (le cache de metadata peut avoir gardé l'ancien path).
    importlib.invalidate_caches()
    installed_after = _installed_version() or "(non installée)"
    print(f"Version installée après : {installed_after}")
    print()
    print("Pour vérifier la cohérence du projet : `forge doctor`.")
    return 0


def main(args: Sequence[str] | None = None) -> int:
    """Point d'entrée de la commande `forge update`.

    Retourne un exit code (0 succès, !=0 erreur). Le dispatcher CLI
    peut propager via `sys.exit(rc)`.
    """
    argv = list(args) if args is not None else sys.argv[1:]

    if "--help" in argv or "-h" in argv:
        _print_help()
        return 0

    pre = "--pre" in argv

    if "--check" in argv:
        return _run_check(pre=pre)

    if "--dry-run" in argv:
        return _run_dry_run(pre=pre)

    return _run_update(pre=pre)
