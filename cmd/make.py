#!/usr/bin/env python3
"""
make — Outil de génération Forge
=======================================

Usage :
    python cmd/make.py <commande> [NomEntite] [options]

Commandes MVC :
    mvc        <NomEntite>   Pile MVC complète (model+validator+controller+views+routes)
    entity     <NomEntite>   Classe entité (dataclass)
    controller <NomEntite>   Contrôleur
    validator  <NomEntite>   Validateur
    model      <NomEntite>   Modèle + requêtes SQL
    views      <NomEntite>   Templates HTML
    routes     <NomEntite>   Enregistre les routes dans routes.py

SQL :
    schema:create            Crée la BDD, configure et valide la connexion
    migration  <NomEntite>   Migration versionnée  → sql/migrations/YYYYMMDD_create_xxx.sql
    table:create <NomEntite> CREATE TABLE          → sql/ddl/xxx_create.sql
    table:alter  <NomEntite> ALTER TABLE squelette → sql/ddl/xxx_alter.sql
    table:fixtures <NomEntite> Script fixtures Faker → sql/fixtures/xxx_fixtures.py

Inspection :
    check      <NomEntite>   Vérifie l'état des fichiers d'une entité
    list                     Liste toutes les entités et leur état

Sécurité :
    security:init            Initialise les tables utilisateur/rôle
    security:hash            Génère un hash de mot de passe

Options :
    --force, -f              Écrase les fichiers existants
    --env   dev|prod         Environnement (défaut : dev)
    --reset                  (security:init) Recrée les tables depuis zéro

Exemples :
    python cmd/make.py mvc Client
    python cmd/make.py entity Client
    python cmd/make.py ddl:create Produit
    python cmd/make.py migration Produit
    python cmd/make.py check Client
    python cmd/make.py list
    python cmd/make.py security:init --env prod
"""

import sys
import subprocess
from pathlib import Path

CMD_DIR = Path(__file__).resolve().parent

# commande → (script, entite_requise)
COMMANDES = {
    # MVC
    "mvc"          : (CMD_DIR / "mvc"      / "mvc.py",          True),
    "entity"       : (CMD_DIR / "mvc"      / "entity.py",       True),
    "controller"   : (CMD_DIR / "mvc"      / "controller.py",   True),
    "validator"    : (CMD_DIR / "mvc"      / "validator.py",    True),
    "model"        : (CMD_DIR / "mvc"      / "model.py",        True),
    "views"        : (CMD_DIR / "mvc"      / "views.py",        True),
    "routes"       : (CMD_DIR / "mvc"      / "routes.py",       True),
    # SQL
    "schema:create": (CMD_DIR / "sql"      / "schema_create.py", False),
    "migration"    : (CMD_DIR / "sql"      / "migration.py",     True),
    "table:create" : (CMD_DIR / "sql"      / "table_create.py",  True),
    "table:alter"  : (CMD_DIR / "sql"      / "table_alter.py",   True),
    "table:fixtures": (CMD_DIR / "sql"      / "table_fixtures.py", True),
    # Inspection
    "check"        : (CMD_DIR / "inspect"  / "check.py",        True),
    "list"         : (CMD_DIR / "inspect"  / "list.py",         False),
    # Sécurité
    "security:init": (CMD_DIR / "security" / "init_users.py",   False),
    "security:hash": (CMD_DIR / "security" / "hash.py",         False),
}


def afficher_aide():
    print(__doc__)


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        afficher_aide()
        sys.exit(0)

    commande = args[0]

    if commande not in COMMANDES:
        print(f"[ERREUR] Commande inconnue : « {commande} »")
        print(f"         Commandes disponibles : {', '.join(COMMANDES)}")
        print(f"         Aide : python cmd/make.py --help")
        sys.exit(1)

    script, entite_requise = COMMANDES[commande]
    sous_args = args[1:]

    if entite_requise and (not sous_args or sous_args[0].startswith("-")):
        print(f"[ERREUR] La commande « {commande} » requiert un NomEntite.")
        print(f"         Exemple : python cmd/make.py {commande} MonEntite")
        sys.exit(1)

    result = subprocess.run(
        [sys.executable, str(script)] + sous_args,
        cwd=str(CMD_DIR.parent),
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
