#!/usr/bin/env python3
"""
Génère le modèle MVC et les fichiers de requêtes SQL.

Usage :
    python cmd/make.py model <NomEntite> [--force]

Options :
    --force, -f   Écrase les fichiers existants

Exemple :
    python cmd/make.py model Produit
    → mvc/models/produit_model.py
    → mvc/models/sql/dev/produit_queries.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _common import to_snake, parse_args, validate_name, read_project_var

_SQL_DIR_REL = read_project_var("SQL_DIR", "mvc/models/sql", ROOT)

T_MODEL = '''\
import mariadb
from core.database.connection import get_connection, close_connection
from core.database.sql_loader import charger_queries
from core.mvc.model.exceptions import DoublonError

_q = charger_queries("{snake}_queries.py")

COUNT_{UPPER}S    = _q.COUNT_{UPPER}S
GET_{UPPER}S_PAGE = _q.GET_{UPPER}S_PAGE
GET_{UPPER}_BY_ID = _q.GET_{UPPER}_BY_ID
ADD_{UPPER}       = _q.ADD_{UPPER}
UPDATE_{UPPER}    = _q.UPDATE_{UPPER}
DELETE_{UPPER}    = _q.DELETE_{UPPER}


def count_{snake}s():
    connection = None
    cursor     = None
    try:
        connection = get_connection()
        cursor     = connection.cursor(dictionary=True)
        cursor.execute(COUNT_{UPPER}S)
        return cursor.fetchone()["total"]
    finally:
        if cursor:     cursor.close()
        close_connection(connection)


def get_{snake}s_page(page, par_page=10):
    connection = None
    cursor     = None
    try:
        offset     = (page - 1) * par_page
        connection = get_connection()
        cursor     = connection.cursor(dictionary=True)
        cursor.execute(GET_{UPPER}S_PAGE, (par_page, offset))
        return cursor.fetchall()
    finally:
        if cursor:     cursor.close()
        close_connection(connection)


def get_{snake}_by_id({snake}_id):
    connection = None
    cursor     = None
    try:
        connection = get_connection()
        cursor     = connection.cursor(dictionary=True)
        cursor.execute(GET_{UPPER}_BY_ID, ({snake}_id,))
        return cursor.fetchone()
    finally:
        if cursor:     cursor.close()
        close_connection(connection)


def add_{snake}({snake}):
    connection = None
    cursor     = None
    try:
        connection = get_connection()
        cursor     = connection.cursor()
        cursor.execute(ADD_{UPPER}, (
            # TODO: remplacer par les vrais champs, ex: {snake}["NomColonne"]
        ))
        connection.commit()
    except mariadb.IntegrityError:
        raise DoublonError({snake}.get("id", "?"))  # TODO: adapter à la vraie clé primaire
    finally:
        if cursor:     cursor.close()
        close_connection(connection)


def update_{snake}({snake}):
    connection = None
    cursor     = None
    try:
        connection = get_connection()
        cursor     = connection.cursor()
        cursor.execute(UPDATE_{UPPER}, (
            # TODO: ajouter les champs à mettre à jour
            # TODO: dernier paramètre = clé primaire pour WHERE, ex: {snake}["NomId"]
        ))
        connection.commit()
    finally:
        if cursor:     cursor.close()
        close_connection(connection)


def delete_{snake}({snake}_id):
    connection = None
    cursor     = None
    try:
        connection = get_connection()
        cursor     = connection.cursor()
        cursor.execute(DELETE_{UPPER}, ({snake}_id,))
        connection.commit()
    finally:
        if cursor:     cursor.close()
        close_connection(connection)
'''

T_QUERIES = '''\
COUNT_{UPPER}S = """
SELECT COUNT(*) AS total FROM {snake}
"""

GET_{UPPER}S_PAGE = """
SELECT
    {Nom}Id
    -- TODO: ajouter les colonnes
FROM {snake}
ORDER BY {Nom}Id
LIMIT ? OFFSET ?
"""

GET_{UPPER}_BY_ID = """
SELECT
    {Nom}Id
    -- TODO: ajouter les colonnes
FROM {snake}
WHERE {Nom}Id = ?
"""

ADD_{UPPER} = """
INSERT INTO {snake} (
    {Nom}Id
    -- TODO: ajouter les colonnes
)
VALUES (?)
-- TODO: ajuster le nombre de ?
"""

UPDATE_{UPPER} = """
UPDATE {snake}
SET
    -- TODO: ajouter les colonnes = ?
WHERE {Nom}Id = ?
"""

DELETE_{UPPER} = """
DELETE FROM {snake}
WHERE {Nom}Id = ?
"""
'''

FICHIERS = {
    ROOT / "mvc" / "models"                      : ("{snake}_model.py",   T_MODEL),
    ROOT / _SQL_DIR_REL / "dev"                  : ("{snake}_queries.py", T_QUERIES),
}


def main():
    args, force = parse_args()
    if len(args) != 1:
        print(__doc__)
        sys.exit(1)

    nom   = validate_name(args[0].strip())
    snake = to_snake(nom)
    upper = snake.upper()

    creees  = []
    ignores = []

    for dossier, (nom_fichier, template) in FICHIERS.items():
        dest = dossier / nom_fichier.format(snake=snake)
        if dest.exists() and not force:
            ignores.append(dest.relative_to(ROOT))
            continue
        was_new = not dest.exists()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(
            template.format(Nom=nom, snake=snake, UPPER=upper),
            encoding="utf-8",
        )
        creees.append((dest.relative_to(ROOT), "créé" if was_new else "régénéré"))

    for f, action in creees:
        print(f"[OK] {f} {action}.")
    for f in ignores:
        print(f"[IGNORÉ] {f}  (utilisez --force pour écraser)")

    if creees:
        print(f"\n     Pensez à :")
        print(f"       - Renseigner les colonnes SQL dans les fichiers _queries.py")
        print(f"       - Compléter add_{snake}() et update_{snake}() avec les bons champs")

    if ignores:
        if creees:
            print("\n[ATTENTION] Certains fichiers existants n'ont pas été mis à jour.")
            print("[CONSEIL]   Utilisez --force pour regénérer TOUS les fichiers.")
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
