#!/usr/bin/env python3
"""
Génère un validateur MVC générique.

Usage :
    python cmd/make.py validator <NomEntite> [--force]

Options :
    --force, -f   Écrase le fichier s'il existe déjà

Exemple :
    python cmd/make.py validator Produit
    → mvc/validators/produit_validator.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _common import to_snake, parse_args, validate_name

ROOT = Path(__file__).resolve().parent.parent.parent

TEMPLATE = '''\
from core.mvc.model.validator import Validator

_REQUIS = []

_LONGUEUR_MAX = {{
    # "Champ": longueur_max,
}}


class {Nom}Validator(Validator):
    def __init__(self, data):
        super().__init__()
        for champ in _REQUIS:
            self.required(data.get(champ, ""), champ)
        for champ, max_len in _LONGUEUR_MAX.items():
            self.max_length(data.get(champ, ""), max_len, champ)
'''


def main():
    args, force = parse_args()
    if len(args) != 1:
        print(__doc__)
        sys.exit(1)

    nom   = validate_name(args[0].strip())
    snake = to_snake(nom)
    dest  = ROOT / "mvc" / "validators" / f"{snake}_validator.py"

    if dest.exists() and not force:
        print(f"[ERREUR] {dest.relative_to(ROOT)} existe déjà. Utilisez --force pour écraser.")
        sys.exit(1)

    was_new = not dest.exists()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(TEMPLATE.format(Nom=nom), encoding="utf-8")
    print(f"[OK] {dest.relative_to(ROOT)} {'créé' if was_new else 'régénéré'}.")
    if was_new:
        print(f"     Pensez à renseigner _REQUIS et _LONGUEUR_MAX.")


if __name__ == "__main__":
    main()
