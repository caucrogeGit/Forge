"""Commande forge starter:list — liste les starter apps disponibles."""

from __future__ import annotations

_DOC_BASE = "https://caucrogegit.github.io/Forge"

STARTERS: list[tuple[int, str, str, str]] = [
    (1, "contact-simple",            "Contact simple",            "CRUD basique sur une entité unique"),
    (2, "utilisateurs-auth",         "Utilisateurs / auth",       "Login, sessions, routes protégées, CSRF"),
    (3, "carnet-contacts",           "Carnet relationnel",        "many_to_one, pivot many-to-many, JOIN SQL"),
    (4, "suivi-comportement-eleves", "Suivi comportement élèves", "Application métier, cases à cocher, synthèses"),
]


def cmd_starter_list() -> None:
    print(f"\nStarter apps Forge\n")
    for level, slug, name, description in STARTERS:
        print(f"  Niveau {level}  {name:<30}  {description}")
        print(f"           docs : {_DOC_BASE}/starter-app-0{level}-{slug}/")
        print()
    print(f"  Index : {_DOC_BASE}/starter-apps/\n")


def main(args: list[str]) -> None:
    if not args or args[0] != "starter:list":
        print("Usage : forge starter:list")
        raise SystemExit(1)
    cmd_starter_list()
