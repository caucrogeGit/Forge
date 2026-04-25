#!/usr/bin/env python3
"""
Génère un fichier SQL de migration versionné (CREATE TABLE squelette).

Usage :
    python cmd/make.py migration <NomEntite> [--force]

Exemple :
    python cmd/make.py migration Produit
    → sql/migrations/20260420_create_produit.sql
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _common import parse_args, validate_name, to_snake

ROOT     = Path(__file__).resolve().parent.parent.parent
MIGR_DIR = ROOT / "sql" / "migrations"

TEMPLATE = """\
-- Migration : création de la table {snake}
-- Entité    : {Nom}
-- Date      : {date}

CREATE TABLE IF NOT EXISTS {snake} (
    {Nom}Id   VARCHAR(10)  NOT NULL,
    -- TODO : ajouter les colonnes

    PRIMARY KEY ({Nom}Id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""


def main():
    args, force = parse_args()
    if len(args) != 1:
        print(__doc__)
        sys.exit(1)

    nom   = validate_name(args[0].strip())
    snake = to_snake(nom)
    today = date.today().strftime("%Y%m%d")
    dest  = MIGR_DIR / f"{today}_create_{snake}.sql"

    if dest.exists() and not force:
        print(f"[ERREUR] {dest.relative_to(ROOT)} existe déjà. Utilisez --force pour écraser.")
        sys.exit(1)

    MIGR_DIR.mkdir(parents=True, exist_ok=True)
    was_new = not dest.exists()
    dest.write_text(TEMPLATE.format(Nom=nom, snake=snake, date=date.today()), encoding="utf-8")
    print(f"[OK] {dest.relative_to(ROOT)} {'créé' if was_new else 'régénéré'}.")
    print(f"     Complétez les colonnes puis exécutez le fichier sur votre base.")


if __name__ == "__main__":
    main()
