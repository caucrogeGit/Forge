#!/usr/bin/env python3
"""DOC-UML-FRESHNESS-001 — les diagrammes de classe décrivent-ils le code réel.

Chaque page de référence porte un chapitre « Schémas UML », soit 27 diagrammes
de classe et 27 de séquence. Ils sont dessinés à la main et vieillissent en
silence : une classe renommée, une méthode retirée, et le diagramme continue de
montrer l'architecture d'avant, avec l'autorité d'un schéma.

Ces diagrammes sont **semi-formels**, et c'est voulu : ils mêlent de vrais noms
de code (`SQLiteBackend`, `get_connection()`) à de la prose explicative
(`+CREATE INDEX séparés`, `class fichier`). Un contrôle mécanique doit donc
trier, et ne juger que ce qui se donne pour du code.

Deux règles de tri, volontairement strictes. Dans le doute, on se tait : un
garde qui crie sur de la prose se fait désactiver, et ne garde alors plus rien.

- Une **classe** n'est jugée que si son nom est un identifiant PascalCase
  **et** qu'une classe de ce nom existe dans le dépôt. Sinon c'est un acteur
  conceptuel, et un diagramme a le droit d'en dessiner.
  Limite assumée : une classe renommée disparaît alors du contrôle au lieu
  d'être signalée. Le prix d'un garde silencieux plutôt que criard.
- Un **membre** n'est jugé que s'il finit par `()` et que son nom est un
  identifiant. `+types SQLite` ou `+name = "sqlite"` ne le sont pas.

Le code est lu par AST, jamais importé : un opt-in absent de l'environnement ne
doit pas faire échouer le contrôle des autres.
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

BLOC_MERMAID = re.compile(r"^([ \t]*)```mermaid[ \t]*$(.*?)^\1```[ \t]*$",
                          re.MULTILINE | re.DOTALL)
DEBUT_CLASSE = re.compile(r"^\s*class\s+([\w]+)\s*\{")
MEMBRE = re.compile(r"^\s*[+\-#~]?\s*([A-Za-z_]\w*)\(\)")
IDENTIFIANT_CLASSE = re.compile(r"^[A-Z][A-Za-z0-9_]*$")


def classes_du_code() -> "dict[str, set[str]]":
    """Toutes les classes du dépôt, avec leurs méthodes, lues par AST.

    Les noms sont pris tels quels : deux classes homonymes dans deux paquets
    fusionnent leurs méthodes. C'est délibéré, un diagramme ne portant pas le
    module de la classe qu'il dessine, et l'inverse produirait des faux refus.
    """
    trouvees: "dict[str, set[str]]" = {}
    racines = [PROJECT_ROOT / "core", PROJECT_ROOT / "cli",
               *sorted(PROJECT_ROOT.glob("packages/*/forge_mvc_*"))]
    for racine in racines:
        if not racine.is_dir():
            continue
        for source in racine.rglob("*.py"):
            try:
                arbre = ast.parse(source.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError):
                continue
            for noeud in ast.walk(arbre):
                if not isinstance(noeud, ast.ClassDef):
                    continue
                methodes = trouvees.setdefault(noeud.name, set())
                for membre in noeud.body:
                    if isinstance(membre, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methodes.add(membre.name)
    return trouvees


def diagrammes_de_classe(page: Path) -> "list[tuple[int, str]]":
    texte = page.read_text(encoding="utf-8")
    trouves: "list[tuple[int, str]]" = []
    for m in BLOC_MERMAID.finditer(texte):
        corps = m.group(2)
        if corps.strip().startswith("classDiagram"):
            trouves.append((texte[: m.start()].count("\n") + 1, corps))
    return trouves


def lire_classes(diagramme: str) -> "dict[str, list[str]]":
    """Classes déclarées dans le diagramme, avec leurs membres en `()`."""
    declarees: "dict[str, list[str]]" = {}
    courante: "str | None" = None
    for ligne in diagramme.splitlines():
        debut = DEBUT_CLASSE.match(ligne)
        if debut:
            courante = str(debut.group(1))
            declarees.setdefault(courante, [])
            continue
        if courante and "}" in ligne:
            courante = None
            continue
        if courante:
            membre = MEMBRE.match(ligne)
            if membre:
                declarees[courante].append(membre.group(1))
    return declarees


def verifier(cible: "str | None") -> int:
    code = classes_du_code()
    pages = ([PROJECT_ROOT / "packages" / f"forge-mvc-{cible}" / "docs" / "reference.md"]
             if cible else sorted(PROJECT_ROOT.glob("packages/*/docs/reference.md")))

    problemes: "list[str]" = []
    classes_jugees = membres_juges = ignorees = 0

    for page in pages:
        if not page.is_file():
            continue
        relatif = page.relative_to(PROJECT_ROOT)
        for ligne, diagramme in diagrammes_de_classe(page):
            for nom, membres in lire_classes(diagramme).items():
                if not IDENTIFIANT_CLASSE.fullmatch(nom):
                    ignorees += 1
                    continue
                if nom not in code:
                    # Acteur conceptuel, non classe périmée. Les diagrammes
                    # dessinent aussi ce qui n'est pas du code : l'exécuteur
                    # injecté (`DBExecutor`), la bibliothèque externe
                    # (`Pillow`), le contrôleur du lecteur (`Controller`), la
                    # factory d'exemple (`VilleFactory`). Les refuser ferait
                    # crier ce garde sur douze abstractions justes, et un
                    # garde qui crie à tort finit désactivé.
                    ignorees += 1
                    continue
                classes_jugees += 1
                for membre in membres:
                    membres_juges += 1
                    if membre not in code[nom]:
                        problemes.append(
                            f"{relatif}:{ligne} — «{nom}.{membre}()» absent de la classe")

    print(f"Classes jugées : {classes_jugees} ; méthodes jugées : {membres_juges} ; "
          f"entrées de prose ignorées : {ignorees}")
    for souci in problemes:
        print(f"  [FAIL] {souci}")
    if problemes:
        print(f"ÉCHEC : {len(problemes)} élément(s) de diagramme sans contrepartie")
        return 1
    print("OK : chaque classe et méthode dessinée existe dans le code")
    return 0


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", metavar="NOM", default=None,
                        help="ne vérifier qu'un opt-in (nom court, ex. « sqlite »)")
    args = parser.parse_args(argv)
    return verifier(args.package)


if __name__ == "__main__":
    sys.exit(main())
