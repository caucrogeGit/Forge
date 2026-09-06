#!/usr/bin/env python3
"""Refuse une release dont le CHANGELOG tait des tickets livrés.

Le pré-vol vérifiait que `CHANGELOG.md` **contient un titre** pour la version
publiée. Il ne vérifiait pas que la section correspondante dise ce qui a été
livré. Les deux se séparent très facilement, et l'ont fait : la rc8 s'est
préparée avec 51 des 106 tickets livrés depuis la rc7 au CHANGELOG, les
55 absents comprenant le refus de servir une application désarmée et les trois
opt-ins qui n'étaient pas provisionnables sur un projet neuf.

Ce que le contrôle lit : les sujets de commit depuis le dernier tag de release.
La convention Forge veut qu'un sujet finisse par le code du ticket entre
parenthèses. Chacun de ces codes doit apparaître quelque part dans
`CHANGELOG.md`.

Il n'y a pas de liste d'exemptions, et il n'y en aura pas : une liste
d'exemptions se remplit, et devient le trou qu'elle prétendait border. Un
ticket dont l'effet ne se voit pas de l'extérieur écrit une entrée d'une ligne
sous la rubrique « Tests ».

Le contrôle échoue quand l'historique lui manque plutôt que de passer : sans
tag de départ ni journal, il ne mesure rien, et un contrôle qui ne mesure rien
doit le dire.

Usage :
    python tools/check_changelog_completeness.py [TAG_DE_DEPART]

Sans argument, le tag de départ est le dernier tag annoté joignable.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Le code de ticket ferme le sujet de commit, entre parenthèses.
# Deux segments majuscules au moins, puis un numéro à trois chiffres.
CODE_TICKET = re.compile(r"\(([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+-\d{3})\)")


class HistoriqueIndisponible(RuntimeError):
    """L'historique git manque, le contrôle ne peut rien mesurer."""


def _git(*args: str) -> str:
    resultat = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    if resultat.returncode != 0:
        raise HistoriqueIndisponible(
            f"git {' '.join(args)} a échoué : {resultat.stderr.strip()}"
        )
    return resultat.stdout


def dernier_tag() -> str:
    """Rend le dernier tag joignable depuis HEAD."""
    tag = _git("describe", "--tags", "--abbrev=0").strip()
    if not tag:
        raise HistoriqueIndisponible("aucun tag joignable depuis HEAD")
    return tag


def sujets_depuis(tag: str) -> list[str]:
    """Rend les sujets de commit livrés depuis `tag`."""
    journal = _git("log", "--format=%s", f"{tag}..HEAD")
    sujets = [ligne for ligne in journal.splitlines() if ligne.strip()]
    if not sujets:
        raise HistoriqueIndisponible(
            f"aucun commit entre {tag} et HEAD : historique tronqué ou tag erroné"
        )
    return sujets


def tickets_absents(sujets: list[str], changelog: str) -> list[str]:
    """Rend les codes de ticket livrés qui ne figurent pas au CHANGELOG.

    Fonction pure, exercée par le garde-fou sur des entrées fabriquées : elle
    doit rester vérifiable sans dépôt git, la CI travaillant sur un clone
    superficiel.
    """
    livres: list[str] = []
    for sujet in sujets:
        livres.extend(CODE_TICKET.findall(sujet))
    return sorted({code for code in livres if code not in changelog})


def main(argv: list[str]) -> int:
    try:
        tag = argv[1] if len(argv) > 1 else dernier_tag()
        sujets = sujets_depuis(tag)
    except HistoriqueIndisponible as erreur:
        print(f"ÉCHEC : {erreur}", file=sys.stderr)
        print(
            "Ce contrôle a besoin des tags et du journal complet. "
            "Sur un clone superficiel, refaire un `git fetch --unshallow --tags`.",
            file=sys.stderr,
        )
        return 2

    changelog = (PROJECT_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    absents = tickets_absents(sujets, changelog)
    total = len({code for sujet in sujets for code in CODE_TICKET.findall(sujet)})

    if absents:
        pluriel = "s" if len(absents) > 1 else ""
        manquent = "manquent" if len(absents) > 1 else "manque"
        print(
            f"ÉCHEC : {len(absents)} ticket{pluriel} livré{pluriel} depuis {tag} "
            f"{manquent} au CHANGELOG."
        )
        for code in absents:
            print(f"  - {code}")
        print()
        print("Écrire leur entrée avant de publier.")
        print("Un ticket sans effet visible de l'extérieur prend une ligne sous « Tests ».")
        return 1

    print(f"OK : les {total} tickets livrés depuis {tag} figurent au CHANGELOG.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
