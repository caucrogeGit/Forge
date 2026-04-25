#!/usr/bin/env python3
"""
Génère le DDL CREATE TABLE de référence pour une entité.

Usage :
    python cmd/make.py table:create <NomEntite> [--force]

Exemple :
    python cmd/make.py table:create Produit
    → sql/ddl/produit_create.sql
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _common import parse_args, validate_name, to_snake

ROOT    = Path(__file__).resolve().parent.parent.parent
DDL_DIR = ROOT / "sql" / "ddl"

TEMPLATE = """\
-- DDL : création de la table {snake}
-- Entité  : {Nom}
-- Généré  : {date}

CREATE TABLE IF NOT EXISTS {snake} (
    {Nom}Id    VARCHAR(10)   NOT NULL          COMMENT 'Identifiant unique',
    -- TODO : ajouter les colonnes
    -- Exemples :
    -- Nom        VARCHAR(100)  NOT NULL,
    -- Prix       DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    -- Description TEXT          DEFAULT NULL,
    -- Actif      TINYINT(1)    NOT NULL DEFAULT 1,
    -- CreeLe     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- ModifieLe  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
    --                                   ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY ({Nom}Id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='{Nom}';
"""


def main():
    args, force = parse_args()
    if len(args) != 1:
        print(__doc__)
        sys.exit(1)

    nom   = validate_name(args[0].strip())
    snake = to_snake(nom)
    dest  = DDL_DIR / f"{snake}_create.sql"

    if dest.exists() and not force:
        print(f"[ERREUR] {dest.relative_to(ROOT)} existe déjà. Utilisez --force pour écraser.")
        sys.exit(1)

    DDL_DIR.mkdir(parents=True, exist_ok=True)
    was_new = not dest.exists()
    dest.write_text(TEMPLATE.format(Nom=nom, snake=snake, date=date.today()), encoding="utf-8")
    print(f"[OK] {dest.relative_to(ROOT)} {'créé' if was_new else 'régénéré'}.")
    print(f"     Complétez les colonnes et types SQL.")


if __name__ == "__main__":
    main()
