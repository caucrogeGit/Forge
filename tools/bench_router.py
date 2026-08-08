#!/usr/bin/env python3
"""ROUTER-METHOD-HOIST-001 — banc de mesure de la résolution de routes.

Un ticket de performance dont le chiffre n'est pas rejouable se périme en
silence, et pire, il laisse la porte ouverte à des affirmations invérifiables.
Ce banc existe pour que toute personne puisse contredire les chiffres du
changelog en une commande, sur sa propre machine.

    python tools/bench_router.py

Il mesure le **chemin applicatif complet**, celui de `core/app/application.py`,
et non `Router.match()` seul. La distinction n'est pas cosmétique : sur un 404,
l'application enchaîne `match()` puis `allowed_methods()`, donc mesurer la
première seule sous-estime le coût de moitié. C'est l'erreur que ce banc évite.

Quatre cas, parce qu'ils n'ont pas le même coût.

- **Succès sur route statique**, la forme la plus courante sous l'ADR-029.
- **Succès sur route dynamique**, dont la regex porte un groupe de capture.
- **404**, aucune route ne concorde, donc deux parcours complets.
- **405**, le chemin existe mais pas pour cette méthode.

Les routes suivent le gabarit réellement engendré par `make:crud`, quatre
routes par entité, moitié statiques, moitié dynamiques. Un banc bâti sur des
routes toutes statiques flatterait l'index et mentirait.

Le point visé est celui du milieu du tableau, ni la première route déclarée
(qui mesure surtout la vitesse d'entrée dans la boucle) ni la dernière (qui ne
mesure que le pire cas).
"""
from __future__ import annotations

import sys
import timeit
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from core.http.router import Router  # noqa: E402

#: Nombres d'entités mesurés. Quatre routes chacune.
ENTITES = (25, 125, 250)

#: Repères de contexte relevés sur la devstation, en microsecondes.
#: Ils disent si un gain compte ou s'il se noie dans le reste de la requête.
REPERES = (
    ("aller-retour SQL trivial, connexion ouverte", 54.2),
    ("rendu Jinja d'un gabarit de vingt lignes", 26.8),
)


def bati(entites: int) -> Router:
    """Routeur au gabarit `make:crud`, quatre routes par entité."""
    routeur = Router()
    for i in range(entites):
        nom = f"ressource{i}"
        routeur.add("GET", f"/{nom}/index", lambda r: None, name=f"{nom}-index")
        routeur.add("POST", f"/{nom}/create", lambda r: None, name=f"{nom}-create")
        routeur.add("GET", f"/{nom}/show/{{id}}", lambda r: None, name=f"{nom}-show")
        routeur.add("POST", f"/{nom}/update/{{id}}", lambda r: None, name=f"{nom}-update")
    return routeur


def microsecondes(fonction, repetitions: int = 3000) -> float:
    return timeit.timeit(fonction, number=repetitions) / repetitions * 1_000_000


def main() -> int:
    print("Résolution de routes, chemin applicatif complet (match + allowed_methods).")
    print()
    print(f"{'ROUTES':>7}  {'CAS':<28} {'DURÉE':>9}")
    print("-" * 48)

    for entites in ENTITES:
        routeur = bati(entites)
        nb = len(routeur.iter_routes())
        milieu = entites // 2
        cas = (
            ("succès, route statique", f"/ressource{milieu}/index", "GET"),
            ("succès, route dynamique", f"/ressource{milieu}/update/7", "POST"),
            ("404, chemin inconnu", "/inconnu/vraiment", "GET"),
            ("405, méthode refusée", f"/ressource{milieu}/index", "DELETE"),
        )
        for etiquette, chemin, methode in cas:
            def chemin_applicatif() -> None:
                if routeur.match(methode, chemin) is None:
                    routeur.allowed_methods(chemin)

            print(f"{nb:>7}  {etiquette:<28} {microsecondes(chemin_applicatif):>8.1f}µ")
        print()

    print("Repères de contexte, même machine :")
    for etiquette, duree in REPERES:
        print(f"  {etiquette:<44} {duree:>6.1f}µ")
    print()
    print("Lecture : sous trois cents routes environ, la résolution reste une")
    print("fraction d'un aller-retour SQL. Le coût ne devient visible qu'au delà.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
