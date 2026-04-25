#!/usr/bin/env python3
"""
Crée la base de données (schéma), configure la connexion et valide l'ensemble.

Usage :
    python cmd/make.py schema:create [--env dev|prod]

Options :
    --env   dev|prod   Environnement à configurer (défaut : dev)

Étapes :
    1. Saisie interactive des paramètres de connexion
    2. Connexion au serveur MariaDB (sans base précisée)
    3. CREATE DATABASE IF NOT EXISTS avec utf8mb4
    4. Validation de la connexion sur la base créée
    5. Sauvegarde dans env/dev ou env/prod

Exemple :
    python cmd/make.py schema:create
    python cmd/make.py schema:create --env prod
"""

import sys
import argparse
import getpass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

DB_CHAMPS = [
    ("DB_HOST",       "Hôte",            "localhost"),
    ("DB_PORT",       "Port",            "3306"),
    ("DB_NAME",       "Base de données", "forge_db"),
    ("DB_USER_LOGIN", "Utilisateur",     "root"),
    ("DB_USER_PWD",   "Mot de passe",    ""),
    ("DB_POOL_SIZE",  "Taille du pool",  "5"),
]


def lire_env(chemin: Path) -> dict:
    valeurs = {}
    if not chemin.exists():
        return valeurs
    for ligne in chemin.read_text(encoding="utf-8").splitlines():
        ligne = ligne.strip()
        if ligne and not ligne.startswith("#") and "=" in ligne:
            cle, _, val = ligne.partition("=")
            valeurs[cle.strip()] = val.strip()
    return valeurs


def ecrire_env(chemin: Path, nouvelles: dict) -> None:
    if not chemin.exists():
        chemin.write_text("", encoding="utf-8")

    lignes    = chemin.read_text(encoding="utf-8").splitlines()
    modifiees = set()
    resultat  = []

    for ligne in lignes:
        cle = ligne.split("=")[0].strip() if "=" in ligne else None
        if cle in nouvelles:
            resultat.append(f"{cle}={nouvelles[cle]}")
            modifiees.add(cle)
        else:
            resultat.append(ligne)

    for cle, valeur in nouvelles.items():
        if cle not in modifiees:
            resultat.append(f"{cle}={valeur}")

    chemin.write_text("\n".join(resultat) + "\n", encoding="utf-8")


def saisir(label: str, defaut: str, secret: bool = False) -> str:
    if secret:
        masque = ("*" * len(defaut)) if defaut else "(vide)"
        valeur = getpass.getpass(f"  {label:<20} [{masque}] : ")
    else:
        valeur = input(f"  {label:<20} [{defaut}] : ").strip()
    return valeur if valeur else defaut


def connecter_serveur(host, port, user, pwd):
    """Connexion au serveur MariaDB sans sélectionner de base."""
    import mariadb
    return mariadb.connect(
        host=host,
        port=int(port),
        user=user,
        password=pwd,
    )


def creer_schema(conn, name: str) -> bool:
    """Exécute CREATE DATABASE IF NOT EXISTS. Retourne True si créée, False si existait."""
    cur = conn.cursor()
    cur.execute(
        f"CREATE DATABASE IF NOT EXISTS `{name}` "
        f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    # ROW_COUNT() vaut 1 si créée, 0 si existait déjà
    cur.execute("SELECT ROW_COUNT()")
    row = cur.fetchone()
    cur.close()
    return row[0] == 1


def valider_connexion(host, port, name, user, pwd) -> tuple[bool, str]:
    """Tente une connexion directe sur la base créée."""
    try:
        import mariadb
        conn = mariadb.connect(
            host=host,
            port=int(port),
            database=name,
            user=user,
            password=pwd,
        )
        version = conn.server_version_info
        conn.close()
        return True, f"MariaDB {'.'.join(str(v) for v in version)} — {host}:{port}/{name}"
    except Exception as e:
        return False, str(e)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", choices=["dev", "prod"], default="dev")
    args, _ = parser.parse_known_args()

    env_path = ROOT / "env" / args.env
    actuels  = lire_env(env_path)

    print(f"Configuration du schéma de base de données")
    print(f"Environnement : {args.env}  →  env/{args.env}")
    print(f"Laissez vide pour conserver la valeur actuelle.\n")

    nouvelles = {}
    for cle, label, defaut_global in DB_CHAMPS:
        defaut = actuels.get(cle, defaut_global)
        nouvelles[cle] = saisir(label, defaut, secret=(cle == "DB_USER_PWD"))

    host = nouvelles["DB_HOST"]
    port = nouvelles["DB_PORT"]
    name = nouvelles["DB_NAME"]
    user = nouvelles["DB_USER_LOGIN"]
    pwd  = nouvelles["DB_USER_PWD"]

    # Étape 1 — connexion au serveur
    print(f"\n[1/3] Connexion au serveur {host}:{port}...")
    try:
        conn = connecter_serveur(host, port, user, pwd)
        version = conn.server_version_info
        print(f"      MariaDB {'.'.join(str(v) for v in version)}")
    except Exception as e:
        print(f"[ERREUR] Impossible de joindre le serveur : {e}")
        if input("\nSauvegarder quand même ? (oui/non) : ").strip().lower() == "oui":
            ecrire_env(env_path, nouvelles)
            print(f"[OK] env/{args.env} sauvegardé (connexion non validée).")
        else:
            print("Annulé — aucune modification.")
            sys.exit(1)
        return

    # Étape 2 — création du schéma
    print(f"[2/3] Création du schéma `{name}`...")
    try:
        creee = creer_schema(conn, name)
        if creee:
            print(f"      Base `{name}` créée (utf8mb4).")
        else:
            print(f"      Base `{name}` existe déjà — aucune modification.")
    except Exception as e:
        print(f"[ERREUR] CREATE DATABASE échoué : {e}")
        conn.close()
        sys.exit(1)
    finally:
        conn.close()

    # Étape 3 — validation de la connexion complète
    print(f"[3/3] Validation de la connexion sur `{name}`...")
    ok, message = valider_connexion(host, port, name, user, pwd)

    if ok:
        print(f"      {message}")
        ecrire_env(env_path, nouvelles)
        print(f"\n[OK] env/{args.env} mis à jour.")
    else:
        print(f"[ERREUR] Connexion à la base échouée : {message}")
        if input("\nSauvegarder quand même ? (oui/non) : ").strip().lower() == "oui":
            ecrire_env(env_path, nouvelles)
            print(f"[OK] env/{args.env} sauvegardé (validation échouée).")
        else:
            print("Annulé — aucune modification.")
            sys.exit(1)


if __name__ == "__main__":
    main()
