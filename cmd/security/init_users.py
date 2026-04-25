#!/usr/bin/env python3
"""
Initialise les tables de sécurité et crée l'utilisateur admin par défaut.

Usage :
    python cmd/make.py security:init [--env dev|prod] [--reset]

Options :
    --env    Environnement à utiliser (défaut : dev)
    --reset  Supprime et recrée les tables (ATTENTION : perte de données)

Tables créées :
    role             — liste des rôles disponibles
    utilisateur      — comptes utilisateurs
    utilisateur_role — association utilisateur ↔ rôle (many-to-many)

Utilisateur admin créé par défaut :
    Login    : admin
    Password : saisi interactivement
"""

import sys
import os
import argparse
import getpass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

# Positionner APP_ENV avant l'import de config (qui le lit à l'import)
_pre = argparse.ArgumentParser(add_help=False)
_pre.add_argument("--env", default=None, choices=["dev", "prod"])
_pre_args, _ = _pre.parse_known_args()
if _pre_args.env is not None:
    os.environ["APP_ENV"] = _pre_args.env

from config import (
    APP_NAME,
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER_LOGIN,
    DB_USER_PWD,
    DB_POOL_SIZE,
)
from core import forge
from core.database.connection import get_connection, close_connection
from core.security.hashing import hacher_mot_de_passe

forge.configure(
    app_name=APP_NAME,
    db_host=DB_HOST,
    db_port=DB_PORT,
    db_name=DB_NAME,
    db_user=DB_USER_LOGIN,
    db_password=DB_USER_PWD,
    db_pool_size=DB_POOL_SIZE,
)

SQL_DROP = [
    "DROP TABLE IF EXISTS utilisateur_role",
    "DROP TABLE IF EXISTS utilisateur",
    "DROP TABLE IF EXISTS role",
]

SQL_CREATE = [
    """
    CREATE TABLE IF NOT EXISTS role (
        RoleId    VARCHAR(20)  NOT NULL,
        Libelle   VARCHAR(50)  NOT NULL,
        PRIMARY KEY (RoleId)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS utilisateur (
        UtilisateurId  INT          NOT NULL AUTO_INCREMENT,
        Login          VARCHAR(50)  NOT NULL,
        PasswordHash   VARCHAR(200) NOT NULL,
        Prenom         VARCHAR(50)  DEFAULT NULL,
        Nom            VARCHAR(50)  DEFAULT NULL,
        Email          VARCHAR(100) DEFAULT NULL,
        Actif          TINYINT(1)   NOT NULL DEFAULT 1,
        CreeLe         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
        ModifieLe      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
                                             ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (UtilisateurId),
        UNIQUE KEY uq_login (Login)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS utilisateur_role (
        UtilisateurId  INT         NOT NULL,
        RoleId         VARCHAR(20) NOT NULL,
        PRIMARY KEY (UtilisateurId, RoleId),
        CONSTRAINT fk_ur_utilisateur FOREIGN KEY (UtilisateurId)
            REFERENCES utilisateur (UtilisateurId) ON DELETE CASCADE ON UPDATE CASCADE,
        CONSTRAINT fk_ur_role FOREIGN KEY (RoleId)
            REFERENCES role (RoleId) ON DELETE CASCADE ON UPDATE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
]

ROLES_PAR_DEFAUT = [
    ("admin", "Administrateur"),
    ("user",  "Utilisateur"),
]


def creer_tables(cursor, reset):
    if reset:
        print("  Suppression des tables existantes...")
        for sql in SQL_DROP:
            cursor.execute(sql)
    print("  Création des tables...")
    for sql in SQL_CREATE:
        cursor.execute(sql)
    print("  [OK] Tables role, utilisateur, utilisateur_role")


def inserer_roles(cursor):
    for role_id, libelle in ROLES_PAR_DEFAUT:
        cursor.execute(
            "INSERT IGNORE INTO role (RoleId, Libelle) VALUES (?, ?)",
            (role_id, libelle),
        )
    print(f"  [OK] Rôles : {', '.join(r[0] for r in ROLES_PAR_DEFAUT)}")


def inserer_admin(cursor):
    cursor.execute("SELECT UtilisateurId FROM utilisateur WHERE Login = ?", ("admin",))
    if cursor.fetchone():
        print("  [--] Utilisateur admin existe déjà — ignoré.")
        return
    print()
    while True:
        pwd1 = getpass.getpass("  Mot de passe admin        : ")
        pwd2 = getpass.getpass("  Confirmer le mot de passe : ")
        if not pwd1:
            print("  [ERREUR] Le mot de passe ne peut pas être vide.")
            continue
        if pwd1 != pwd2:
            print("  [ERREUR] Les mots de passe ne correspondent pas.")
            continue
        break
    password_hash = hacher_mot_de_passe(pwd1)
    cursor.execute(
        "INSERT INTO utilisateur (Login, PasswordHash, Prenom, Nom) VALUES (?, ?, ?, ?)",
        ("admin", password_hash, "Admin", "Système"),
    )
    cursor.execute(
        "INSERT INTO utilisateur_role (UtilisateurId, RoleId) VALUES (?, ?)",
        (cursor.lastrowid, "admin"),
    )
    print("  [OK] Utilisateur admin créé.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", default="dev", choices=["dev", "prod"],
                        help="Environnement à utiliser (défaut : dev)")
    parser.add_argument("--reset", action="store_true")
    args, _ = parser.parse_known_args()

    print(f"Environnement   : {os.environ.get('APP_ENV', 'dev')}")
    print(f"Base de données : {DB_HOST}:{DB_PORT}/{DB_NAME}")
    print(f"Utilisateur SQL : {DB_USER_LOGIN}")

    if args.reset:
        print("[!] Mode --reset : les tables seront supprimées et recréées.")
        if input("    Confirmer ? (oui) : ").strip().lower() != "oui":
            print("Annulé.")
            sys.exit(0)

    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        creer_tables(cursor, args.reset)
        inserer_roles(cursor)
        inserer_admin(cursor)
        connection.commit()
        print("\n[OK] Initialisation terminée.")
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"\n[ERREUR] {e}")
        sys.exit(1)
    finally:
        if cursor:
            cursor.close()
        close_connection(connection)


if __name__ == "__main__":
    main()
