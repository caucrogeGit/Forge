#!/usr/bin/env python3
"""
Génère un squelette DDL ALTER TABLE pour modifier une table existante.

Usage :
    python cmd/make.py table:alter <NomEntite> [--force]

Exemple :
    python cmd/make.py table:alter Produit
    → sql/ddl/produit_alter.sql
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _common import parse_args, validate_name, to_snake

ROOT    = Path(__file__).resolve().parent.parent.parent
DDL_DIR = ROOT / "sql" / "ddl"

TEMPLATE = """\
-- DDL : modification de la table {snake}
-- Entité  : {Nom}
-- Généré  : {date}

-- Ajouter une colonne
-- ALTER TABLE {snake}
--     ADD COLUMN NouvelleColonne VARCHAR(100) DEFAULT NULL
--     AFTER {Nom}Id;

-- Modifier une colonne
-- ALTER TABLE {snake}
--     MODIFY COLUMN Colonne VARCHAR(200) NOT NULL;

-- Renommer une colonne
-- ALTER TABLE {snake}
--     RENAME COLUMN AncienNom TO NouveauNom;

-- Supprimer une colonne
-- ALTER TABLE {snake}
--     DROP COLUMN AncienneColonne;

-- Ajouter un index
-- ALTER TABLE {snake}
--     ADD INDEX idx_{snake}_col (Colonne);

-- Ajouter une clé étrangère
-- ALTER TABLE {snake}
--     ADD CONSTRAINT fk_{snake}_autre
--     FOREIGN KEY (AutreId) REFERENCES autre (AutreId)
--     ON DELETE RESTRICT ON UPDATE CASCADE;

-- Supprimer une contrainte
-- ALTER TABLE {snake}
--     DROP FOREIGN KEY fk_{snake}_autre;
"""


def main():
    args, force = parse_args()
    if len(args) != 1:
        print(__doc__)
        sys.exit(1)

    nom   = validate_name(args[0].strip())
    snake = to_snake(nom)
    dest  = DDL_DIR / f"{snake}_alter.sql"

    if dest.exists() and not force:
        print(f"[ERREUR] {dest.relative_to(ROOT)} existe déjà. Utilisez --force pour écraser.")
        sys.exit(1)

    DDL_DIR.mkdir(parents=True, exist_ok=True)
    was_new = not dest.exists()
    dest.write_text(TEMPLATE.format(Nom=nom, snake=snake, date=date.today()), encoding="utf-8")
    print(f"[OK] {dest.relative_to(ROOT)} {'créé' if was_new else 'régénéré'}.")
    print(f"     Décommentez et adaptez les instructions nécessaires.")


if __name__ == "__main__":
    main()
