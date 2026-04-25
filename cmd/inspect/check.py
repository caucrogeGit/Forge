#!/usr/bin/env python3
"""
Vérifie l'état de tous les fichiers d'une entité MVC.

Usage :
    python cmd/inspect/check.py <NomEntite>

Exemple :
    python cmd/inspect/check.py Produit
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _common import parse_args, validate_name, to_snake

ROOT      = Path(__file__).resolve().parent.parent.parent
ROUTES_PY = ROOT / "mvc" / "routes.py"


def verif(label, path):
    exists = Path(path).exists()
    icone  = "[OK]" if exists else "[!] "
    print(f"  {icone}  {label:35} {Path(path).relative_to(ROOT)}")
    return exists


def main():
    args, _ = parse_args()
    if len(args) != 1:
        print(__doc__)
        sys.exit(1)

    nom   = validate_name(args[0].strip())
    snake = to_snake(nom)

    print(f"Diagnostic de l'entité « {nom} »")
    print("=" * 55)

    ok = []
    ok.append(verif("Contrôleur",         ROOT / "mvc" / "controllers"                    / f"{snake}_controller.py"))
    ok.append(verif("Validateur",          ROOT / "mvc" / "validators"                     / f"{snake}_validator.py"))
    ok.append(verif("Modèle",             ROOT / "mvc" / "models"                         / f"{snake}_model.py"))
    ok.append(verif("Requêtes SQL (dev)", ROOT / "mvc" / "models" / "sql" / "dev"         / f"{snake}_queries.py"))
    ok.append(verif("Vue index",          ROOT / "mvc" / "views" / f"{snake}s"            / "index.html"))
    ok.append(verif("Vue create",         ROOT / "mvc" / "views" / f"{snake}s"            / "create.html"))
    ok.append(verif("Vue edit",           ROOT / "mvc" / "views" / f"{snake}s"            / "edit.html"))
    ok.append(verif("Partiel fields",     ROOT / "mvc" / "views" / f"{snake}s" / "partials" / "fields.html"))
    ok.append(verif("Partiel row",        ROOT / "mvc" / "views" / f"{snake}s" / "partials" / "row.html"))

    contenu   = ROUTES_PY.read_text(encoding="utf-8")
    routes_ok = f"{nom}Controller" in contenu
    print(f"  {'[OK]' if routes_ok else '[!] '}  {'Routes enregistrées':35} mvc/routes.py")
    ok.append(routes_ok)

    print("=" * 55)
    nb_ok  = sum(ok)
    nb_tot = len(ok)
    if nb_ok == nb_tot:
        print(f"[OK] Entité complète ({nb_ok}/{nb_tot})")
    else:
        print(f"[!]  {nb_tot - nb_ok} élément(s) manquant(s) sur {nb_tot}")
        sys.exit(1)


if __name__ == "__main__":
    main()
