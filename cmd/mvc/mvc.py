#!/usr/bin/env python3
"""
Génère toute la pile MVC pour une entité (model, validator, controller, views, routes).

Usage :
    python cmd/make.py mvc <NomEntite> [--force]

Exemple :
    python cmd/make.py mvc Client
"""

import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _common import parse_args, validate_name, to_snake

GENERATE_DIR = Path(__file__).resolve().parent

SCRIPTS = [
    "model.py",
    "validator.py",
    "controller.py",
    "views.py",
    "routes.py",
]


def main():
    args, force = parse_args()
    if len(args) != 1:
        print(__doc__)
        sys.exit(1)

    nom   = validate_name(args[0].strip())
    flags = ["--force"] if force else []

    print(f"Génération MVC complète « {nom} »")
    print("=" * 40)

    erreurs = []
    for script in SCRIPTS:
        result = subprocess.run(
            [sys.executable, str(GENERATE_DIR / script), nom] + flags,
            capture_output=True, text=True,
        )
        if result.stdout.strip():
            print(result.stdout.strip())
        if result.returncode != 0 and result.stderr.strip():
            print(result.stderr.strip())
        if result.returncode != 0:
            erreurs.append(script.replace(".py", ""))

    print("=" * 40)
    if erreurs:
        print(f"[!] Erreurs dans : {', '.join(erreurs)}")
        print(f"    Utilisez --force pour écraser les fichiers existants.")
        sys.exit(1)
    else:
        print(f"[OK] Pile MVC « {nom} » complète.")


if __name__ == "__main__":
    main()
