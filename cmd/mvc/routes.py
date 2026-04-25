#!/usr/bin/env python3
"""
Enregistre les routes CRUD d'une entité dans mvc/routes.py.

Usage :
    python cmd/make.py routes <NomEntite> [--plural <slug>]

Exemple :
    python cmd/make.py routes Produit
    python cmd/make.py routes CommandeLigne --plural commandes
    → ajoute l'import + 6 appels router.add() dans mvc/routes.py
"""

import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _common import parse_all_args, validate_name, to_snake

ROOT      = Path(__file__).resolve().parent.parent.parent
ROUTES_PY = ROOT / "mvc" / "routes.py"


def main():
    args, _, plural = parse_all_args()
    if len(args) != 1:
        print(__doc__)
        sys.exit(1)

    nom   = validate_name(args[0].strip())
    snake = to_snake(nom)
    slug  = plural if plural else f"{snake}s"
    ctrl  = f"{nom}Controller"
    imp   = f"from mvc.controllers.{snake}_controller import {ctrl}"

    if not ROUTES_PY.exists():
        print(f"[ERREUR] mvc/routes.py introuvable.")
        sys.exit(1)

    contenu = ROUTES_PY.read_text(encoding="utf-8")

    if ctrl in contenu:
        print(f"[ERREUR] {ctrl} est déjà enregistré dans routes.py.")
        sys.exit(1)

    ctrl_path = ROOT / "mvc" / "controllers" / f"{snake}_controller.py"
    if not ctrl_path.exists():
        print(f"[ERREUR] {ctrl_path.relative_to(ROOT)} introuvable.")
        print(f"         Générez-le d'abord : python cmd/make.py controller {nom}")
        sys.exit(1)

    # ── Import ────────────────────────────────────────────────────────────────
    dernier_import = max(
        (m.end() for m in re.finditer(r'^from mvc\.controllers\..+$', contenu, re.MULTILINE)),
        default=None,
    )
    if dernier_import is None:
        print("[ERREUR] Impossible de localiser les imports dans routes.py.")
        sys.exit(1)

    contenu = contenu[:dernier_import] + f"\n{imp}" + contenu[dernier_import:]

    # ── Routes ────────────────────────────────────────────────────────────────
    nouvelles = "\n".join([
        f'router.add("GET",  "/{slug}",        {ctrl}.list,      name="{snake}_list")',
        f'router.add("GET",  "/{slug}/add",    {ctrl}.add_form,  name="{snake}_add_form")',
        f'router.add("GET",  "/{slug}/edit",   {ctrl}.edit_form, name="{snake}_edit_form")',
        f'router.add("GET",  "/{slug}/{{id}}", {ctrl}.show,      name="{snake}_show")',
        f'router.add("POST", "/{slug}/add",    {ctrl}.add,       name="{snake}_add")',
        f'router.add("POST", "/{slug}/edit",   {ctrl}.edit,      name="{snake}_edit")',
        f'router.add("POST", "/{slug}/delete", {ctrl}.delete,    name="{snake}_delete")',
    ]) + "\n"

    # Insère après le dernier router.add() existant, ou en fin de fichier
    matches = list(re.finditer(r'^router\.add\(.*\)$', contenu, re.MULTILINE))
    if matches:
        pos     = matches[-1].end()
        contenu = contenu[:pos] + "\n" + nouvelles + contenu[pos:]
    else:
        contenu = contenu.rstrip("\n") + "\n\n" + nouvelles

    ROUTES_PY.write_text(contenu, encoding="utf-8")
    print(f"[OK] {ROUTES_PY.relative_to(ROOT)} mis à jour.")
    print(f"     Import : {imp}")
    print(f"     Routes : /{slug}, /{slug}/add, /{slug}/edit, /{slug}/{{id}}, /{slug}/delete")


if __name__ == "__main__":
    main()
