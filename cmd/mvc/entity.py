#!/usr/bin/env python3
"""
Génère une classe entité (dataclass) représentant l'objet métier.

Usage :
    python cmd/make.py entity <NomEntite> [--force]

Exemple :
    python cmd/make.py entity Client
    → mvc/entities/client_entity.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _common import to_snake, parse_args, validate_name

ROOT        = Path(__file__).resolve().parent.parent.parent
ENTITIES_DIR = ROOT / "mvc" / "entities"

TEMPLATE = '''\
from dataclasses import dataclass
from typing import Optional


@dataclass
class {Nom}:
    {Nom}Id : str = ""
    # TODO: ajouter les champs
    # Exemple :
    # Nom     : str           = ""
    # Email   : Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "{Nom}":
        return cls(**{{k: data.get(k) for k in cls.__dataclass_fields__}})

    def to_dict(self) -> dict:
        return {{k: getattr(self, k) for k in self.__dataclass_fields__}}
'''


def main():
    args, force = parse_args()
    if len(args) != 1:
        print(__doc__)
        sys.exit(1)

    nom   = validate_name(args[0].strip())
    snake = to_snake(nom)
    dest  = ENTITIES_DIR / f"{snake}_entity.py"

    if dest.exists() and not force:
        print(f"[ERREUR] {dest.relative_to(ROOT)} existe déjà. Utilisez --force pour écraser.")
        sys.exit(1)

    was_new = not dest.exists()
    ENTITIES_DIR.mkdir(parents=True, exist_ok=True)
    dest.write_text(TEMPLATE.format(Nom=nom), encoding="utf-8")
    print(f"[OK] {dest.relative_to(ROOT)} {'créé' if was_new else 'régénéré'}.")
    if was_new:
        print(f"     Complétez les champs dans la dataclass.")


if __name__ == "__main__":
    main()
