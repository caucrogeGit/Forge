#!/usr/bin/env python3
"""DOC-CODE-ADEQUATION-001 — la documentation nomme-t-elle du code qui existe.

Une page qui montre `from forge_mvc_x import Y` promet que `Y` s'importe. Rien
ne le vérifiait, et le seul retour possible était celui d'un lecteur qui essaie.
Or Forge a renommé, extrait et supprimé beaucoup depuis la 0.x, et la doc suit
à la main.

Ce script lit les blocs `python` de toute la documentation embarquée, en extrait
les imports visant Forge, puis demande à l'interpréteur si le module et le
symbole existent. Il ne juge pas le sens, seulement l'existence : c'est le
minimum qu'une documentation doive à son lecteur, et c'est vérifiable sans
ambiguïté.

Trois verdicts par import.

    OK        le module s'importe et porte le symbole
    ABSENT    le module s'importe mais ne porte pas ce symbole
    INTROUVABLE   le module lui-même ne s'importe pas

Les modules applicatifs (`mvc.*`, `app.*`) sont ignorés : ils appartiennent au
projet du lecteur, pas au framework, et n'existent pas dans ce dépôt.

Un bloc qui ne se parse pas n'est pas une erreur : la documentation montre
souvent des fragments, une méthode isolée ou un corps de fonction. Seuls les
blocs syntaxiquement complets sont interrogés.
"""
from __future__ import annotations

import argparse
import ast
import importlib
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

#: Préfixes de modules appartenant au framework, donc vérifiables ici.
PREFIXES_FORGE = ("core", "cli", "forge_mvc_", "forge")

#: Préfixes appartenant au projet du lecteur : hors de portée de ce dépôt.
PREFIXES_APPLICATIFS = ("mvc", "app", "tests", "optins")

#: Déclaration d'une page qui conserve sciemment des noms d'époque.
MARQUEUR_IGNORE = "<!-- check-docs-symbols: ignore -->"

BLOC_PYTHON = re.compile(r"^```python\s*$(.*?)^```\s*$", re.MULTILINE | re.DOTALL)
BLOC_BASH = re.compile(r"^```bash\s*$(.*?)^```\s*$", re.MULTILINE | re.DOTALL)

#: `forge db:init --run`, `./.venv/bin/forge doctor`, `forge  make:entity Article`.
APPEL_FORGE = re.compile(r"(?:^|\|\s*|&&\s*)(?:\S*/)?forge\s+([a-z][\w:-]*)", re.MULTILINE)


def blocs_bash(texte: str) -> "list[tuple[int, str]]":
    trouves: "list[tuple[int, str]]" = []
    for correspondance in BLOC_BASH.finditer(texte):
        ligne = texte[: correspondance.start()].count("\n") + 1
        trouves.append((ligne, correspondance.group(1)))
    return trouves


def commandes_connues() -> "set[str]":
    """Ce que le CLI déclare savoir faire, lu de lui et non d'une liste écrite ici.

    Deux sources, car le dispatch est en deux morceaux depuis l'ADR-059 : l'aide
    du cœur, et les tables d'opt-ins publiées en entry points.
    """
    import importlib.metadata
    import subprocess

    connues: "set[str]" = set()
    aide = subprocess.run([sys.executable, str(PROJECT_ROOT / "forge.py"), "--help"],
                          capture_output=True, text=True, cwd=PROJECT_ROOT)
    for ligne in aide.stdout.splitlines():
        # Le nom peut être suivi de ses arguments : « new <NomProjet>    Crée… ».
        # Les exiger absents ratait exactement les commandes les plus citées.
        trouve = re.match(r"^ {2}([a-z][\w:-]*)(?: +[<\[]\S*)*\s{2,}\S", ligne)
        if trouve:
            connues.add(trouve.group(1))
    # `forge help` est servi par le même chemin que `--help`, sans figurer dans
    # la liste des commandes qu'il affiche.
    connues.add("help")

    for point in importlib.metadata.entry_points(group="forge_mvc.commands"):
        try:
            table = point.load()
        except Exception:  # noqa: BLE001 — opt-in absent : ses commandes aussi
            continue
        if isinstance(table, dict):
            connues.update(str(nom) for nom in table)  # pyright: ignore[reportUnknownArgumentType]
    return connues


def blocs_python(texte: str) -> "list[tuple[int, str]]":
    """Rend les blocs `python` avec la ligne où chacun commence."""
    trouves: "list[tuple[int, str]]" = []
    for correspondance in BLOC_PYTHON.finditer(texte):
        ligne = texte[: correspondance.start()].count("\n") + 1
        trouves.append((ligne, correspondance.group(1)))
    return trouves


def imports_forge(code: str) -> "list[tuple[str, str]]":
    """Rend les couples (module, symbole) que ce bloc prétend importer.

    Un bloc non parsable rend une liste vide : la documentation montre souvent
    des fragments, et les refuser noierait le signal utile sous le bruit.
    """
    try:
        arbre = ast.parse(code)
    except SyntaxError:
        return []

    couples: "list[tuple[str, str]]" = []
    for noeud in ast.walk(arbre):
        if not isinstance(noeud, ast.ImportFrom) or not noeud.module:
            continue
        racine = noeud.module.split(".")[0]
        if racine in PREFIXES_APPLICATIFS:
            continue
        if not any(noeud.module.startswith(p) for p in PREFIXES_FORGE):
            continue
        for alias in noeud.names:
            couples.append((noeud.module, alias.name))
    return couples


def verdict(module: str, symbole: str) -> "str | None":
    """Rend le problème constaté, ou `None` si l'import tient."""
    try:
        objet = importlib.import_module(module)
    except Exception as erreur:  # noqa: BLE001 — toute cause vaut « introuvable »
        return f"module INTROUVABLE ({type(erreur).__name__})"
    if symbole == "*":
        return None
    if hasattr(objet, symbole):
        return None
    # `from core.database import db` vise un SOUS-MODULE, que le paquet parent
    # ne porte comme attribut qu'une fois celui-ci importé. Conclure sur le seul
    # `hasattr` refusait donc des imports parfaitement valides : ce script a
    # commencé par se tromper de cette façon sur deux pages de fixtures.
    try:
        importlib.import_module(f"{module}.{symbole}")
    except Exception:  # noqa: BLE001 — ni attribut ni sous-module : vraiment absent
        return "symbole ABSENT du module"
    return None


def _adr_remplace(page: Path) -> bool:
    """Vrai si la section « Statut » de cet ADR annonce un remplacement."""
    texte = page.read_text(encoding="utf-8")
    if "## Statut" not in texte:
        return False
    apres = texte.split("## Statut", 1)[1]
    statut = apres.split("\n## ", 1)[0]
    return "**Remplacé**" in statut


def pages(cible: "str | None") -> "list[Path]":
    """Toute la doc embarquée, ou celle d'un seul paquet."""
    if cible:
        racines = [PROJECT_ROOT / "packages" / f"forge-mvc-{cible}" / "docs"]
    else:
        racines = [
            *sorted(PROJECT_ROOT.glob("packages/*/docs")),
            *sorted(PROJECT_ROOT.glob("core/*/docs")),
            PROJECT_ROOT / "docs",
        ]
    fichiers: "list[Path]" = []
    for racine in racines:
        if racine.is_dir():
            fichiers.extend(sorted(racine.rglob("*.md")))
    # `docs/history/` est la mémoire brute de Forge : ces pages décrivent l'état
    # de leur époque et citent volontairement du code depuis supprimé. Les
    # corriger effacerait ce qu'elles servent à conserver.
    fichiers = [f for f in fichiers if "history" not in f.parts]
    # Un ADR qui se déclare remplacé décrit par définition un état passé, et
    # doit continuer de montrer la commande ou l'API qu'il a fait adopter.
    # L'y corriger réécrirait la décision qu'il enregistre ; la règle vaut donc
    # pour tous les ADR remplacés à venir, sans exception à écrire une par une.
    fichiers = [f for f in fichiers
                if not (f.parent.name == "adr" and _adr_remplace(f))]
    # Une page peut se déclarer hors contrôle, à condition de dire pourquoi.
    # Cela vaut mieux qu'une liste de répertoires exclus écrite ici : l'auteur
    # de la page est seul à savoir qu'il conserve un nom d'époque à dessein, et
    # sa déclaration reste visible à côté du texte concerné (principe 3).
    return [f for f in fichiers if MARQUEUR_IGNORE not in f.read_text(encoding="utf-8")]


def verifier(cible: "str | None", *, welcome_seul: bool) -> int:
    problemes: "list[str]" = []
    total_imports = 0
    total_commandes = 0
    connues = commandes_connues()

    for page in pages(cible):
        if welcome_seul and "welcome" not in page.parts:
            continue
        texte = page.read_text(encoding="utf-8")
        relatif = page.relative_to(PROJECT_ROOT)

        for ligne, code in blocs_python(texte):
            for module, symbole in imports_forge(code):
                total_imports += 1
                souci = verdict(module, symbole)
                if souci:
                    problemes.append(
                        f"{relatif}:{ligne} — from {module} import {symbole} : {souci}"
                    )

        for ligne, script in blocs_bash(texte):
            for commande in APPEL_FORGE.findall(script):
                total_commandes += 1
                if commande not in connues:
                    problemes.append(
                        f"{relatif}:{ligne} — `forge {commande}` : COMMANDE INCONNUE du CLI"
                    )

    print(f"Imports Forge vérifiés : {total_imports}")
    print(f"Commandes `forge` vérifiées : {total_commandes} "
          f"(le CLI en déclare {len(connues)})")
    for ligne in problemes:
        print(f"  [FAIL] {ligne}")
    if problemes:
        print(f"ÉCHEC : {len(problemes)} élément(s) que le code ne porte pas")
        return 1
    print("OK : chaque import et chaque commande documentés existent")
    return 0


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", metavar="NOM", default=None,
                        help="ne vérifier qu'un opt-in (nom court, ex. « images »)")
    parser.add_argument("--welcome", action="store_true",
                        help="ne vérifier que les parcours d'accueil")
    args = parser.parse_args(argv)
    return verifier(args.package, welcome_seul=args.welcome)


if __name__ == "__main__":
    sys.exit(main())
