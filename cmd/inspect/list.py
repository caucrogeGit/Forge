#!/usr/bin/env python3
"""
Liste toutes les entités MVC et leur état.

Usage :
    python cmd/inspect/list.py

Affiche pour chaque entité détectée :
    CTRL  VALID  MODEL  SQL  VIEWS  ROUTES
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _common import to_snake

ROOT      = Path(__file__).resolve().parent.parent.parent
ROUTES_PY = ROOT / "mvc" / "routes.py"

EXCLUSIONS = {"auth"}


def detecter_entites():
    ctrl_dir = ROOT / "mvc" / "controllers"
    entites  = []
    for f in sorted(ctrl_dir.glob("*_controller.py")):
        snake = f.stem.replace("_controller", "")
        if snake not in EXCLUSIONS:
            nom = "".join(w.capitalize() for w in snake.split("_"))
            entites.append((nom, snake))
    return entites


def check(path):
    return "[OK]" if Path(path).exists() else "[ ]"


def main():
    entites = detecter_entites()
    if not entites:
        print("Aucune entité trouvée dans mvc/controllers/.")
        sys.exit(0)

    routes_contenu = ROUTES_PY.read_text(encoding="utf-8")

    col = "{:<18} {:^6} {:^6} {:^6} {:^5} {:^6} {:^7}"
    sep = "-" * 60
    print(col.format("Entité", "CTRL", "VALID", "MODEL", "SQL", "VIEWS", "ROUTES"))
    print(sep)

    for nom, snake in entites:
        ctrl   = check(ROOT / "mvc" / "controllers"                / f"{snake}_controller.py")
        valid  = check(ROOT / "mvc" / "validators"                  / f"{snake}_validator.py")
        model  = check(ROOT / "mvc" / "models"                      / f"{snake}_model.py")
        sql    = check(ROOT / "mvc" / "models" / "sql" / "dev"      / f"{snake}_queries.py")
        views  = check(ROOT / "mvc" / "views" / f"{snake}s"         / "index.html")
        routes = "[OK]" if f"{nom}Controller" in routes_contenu else "[ ]"
        print(col.format(nom, ctrl, valid, model, sql, views, routes))

    print(sep)
    print(f"  {len(entites)} entité(s) détectée(s).")


if __name__ == "__main__":
    main()
