#!/usr/bin/env python3
"""WELCOME-EXECUTION-001 — exécuter un parcours d'accueil comme un lecteur le suit.

Lire un parcours ne dit pas s'il marche. Mesuré sur le plus simple des vingt-sept,
SQLite, deux paliers sur deux : le second échouait, faute de citer deux prérequis.
Aucune relecture ne l'aurait montré, les deux commandes étant justes prises une à
une, et le manque n'existant qu'entre elles.

Ce script suit le parcours **dans l'ordre du site**, celui du `nav` de
`mkdocs.yml`, qui fait autorité et que le lecteur voit dans le menu. Il exécute
les blocs `bash` dans un projet Forge réel et s'arrête au premier qui refuse.

Trois raisons de ne pas exécuter un bloc, toutes déclarées et comptées.

    PLACEHOLDER   le bloc contient un `<nom>` à remplacer par le lecteur
    BLOQUANT      le bloc lance un serveur qui ne rend jamais la main
    MANUEL        le bloc demande un geste hors du terminal

Un bloc sauté est **annoncé**, jamais passé sous silence : un harnais qui tait
ce qu'il n'a pas fait se lit comme une couverture complète (principe 3).

Usage :
    python tools/run_welcome_parcours.py --package sqlite --project /chemin/projet
    python tools/run_welcome_parcours.py --package sqlite --list
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

BLOC_BASH = re.compile(r"^```bash\s*$(.*?)^```\s*$", re.MULTILINE | re.DOTALL)

#: Un `<nom>` que le lecteur remplace : la commande n'est pas exécutable telle quelle.
PLACEHOLDER = re.compile(r"<[a-zA-Zà-ÿ][\w à-ÿ'-]*>")

#: Commandes qui ne rendent jamais la main. Les lancer figerait le harnais.
BLOQUANTES = ("forge run", "mkdocs serve", "npm run dev", "python -m http.server")

#: Gestes qui sortent du terminal, donc hors de portée d'une exécution.
MANUELLES = ("$EDITOR", "nano ", "vim ", "code ")

#: Commandes qui interrogent le lecteur, et l'option documentée qui s'en passe.
#:
#: Le parcours a raison de montrer la forme interactive, celle qu'un humain
#: emploie. Le harnais, lui, n'a pas de terminal : sans cette table il
#: s'arrêterait au premier `make:entity` et laisserait le reste du parcours,
#: quatorze blocs pour le moteur d'entités, sans aucune vérification.
#: La substitution est **annoncée** à chaque fois, car elle change ce qui est
#: éprouvé : `--no-input` pose une entité minimale là où le lecteur aurait
#: décrit ses champs.
EQUIVALENTS: "dict[str, str]" = {
    "forge make:entity": "--no-input",
}

#: Commandes interactives SANS option documentée pour s'en passer.
#:
#: Constat, et non choix de conception du harnais : `make:entity` expose
#: `--no-input`, `make:relation` n'expose rien d'équivalent. Une relation ne peut
#: donc être créée ni par un script, ni en intégration continue, ni par un agent,
#: alors que Forge écrit lui-même la guidance des agents (ADR-047).
INTERACTIVES = ("forge make:relation",)

#: Délai au-delà duquel une commande est tenue pour bloquée.
DELAI = 180


def nav_welcome(paquet: str) -> "list[Path]":
    """Pages de parcours du paquet, dans l'ordre du menu du site.

    Le `nav` est lu comme du texte plutôt que comme du YAML : seul l'ordre des
    chemins `welcome/...` importe, et une dépendance à PyYAML pour cela serait
    disproportionnée.
    """
    config = PROJECT_ROOT / "packages" / f"forge-mvc-{paquet}" / "mkdocs.yml"
    if not config.is_file():
        raise SystemExit(f"Erreur : {config} est introuvable.")
    docs = config.parent / "docs"
    pages: "list[Path]" = []
    for ligne in config.read_text(encoding="utf-8").splitlines():
        trouve = re.search(r"(welcome/[\w/-]+\.md)\s*$", ligne)
        if trouve:
            page = docs / trouve.group(1)
            if page.is_file():
                pages.append(page)
    return pages


def blocs(page: Path) -> "list[tuple[int, str]]":
    texte = page.read_text(encoding="utf-8")
    return [(texte[: m.start()].count("\n") + 1, m.group(1))
            for m in BLOC_BASH.finditer(texte)]


def raison_de_sauter(script: str) -> "str | None":
    if PLACEHOLDER.search(script):
        return "PLACEHOLDER"
    if any(motif in script for motif in BLOQUANTES):
        return "BLOQUANT"
    if any(motif in script for motif in MANUELLES):
        return "MANUEL"
    if any(motif in script for motif in INTERACTIVES):
        return "INTERACTIF"
    return None


def substituer(script: str) -> "tuple[str, str | None]":
    """Rend le script à jouer et, le cas échéant, la substitution opérée."""
    for commande, option in EQUIVALENTS.items():
        lignes = script.splitlines()
        for index, ligne in enumerate(lignes):
            if commande in ligne and option not in ligne:
                lignes[index] = f"{ligne.rstrip()} {option}"
                return "\n".join(lignes), f"{commande} + {option}"
    return script, None


def executer(script: str, projet: Path) -> "tuple[int, str]":
    """Joue le bloc dans le projet, comme un lecteur collant dans son terminal."""
    env = dict(os.environ)
    env["PATH"] = f"{projet / '.venv' / 'bin'}{os.pathsep}{env.get('PATH', '')}"
    env["VIRTUAL_ENV"] = str(projet / ".venv")
    env.pop("PYTHONPATH", None)
    try:
        fini = subprocess.run(
            ["bash", "-euo", "pipefail", "-c", script],
            cwd=projet, env=env, capture_output=True, text=True, timeout=DELAI,
        )
    except subprocess.TimeoutExpired:
        return 124, f"aucune réponse après {DELAI} s"
    return fini.returncode, (fini.stdout + fini.stderr)


def parcourir(paquet: str, projet: "Path | None", *, lister: bool) -> int:
    pages = nav_welcome(paquet)
    if not pages:
        raise SystemExit(f"Erreur : aucun parcours dans le nav de forge-mvc-{paquet}.")

    joues = 0
    substitutions = 0
    sautes: "dict[str, int]" = {}
    print(f"=== Parcours {paquet} : {len(pages)} page(s), dans l'ordre du site ===")

    for page in pages:
        relatif = page.relative_to(PROJECT_ROOT)
        for ligne, script in blocs(page):
            raison = raison_de_sauter(script)
            premiere = script.strip().splitlines()[0] if script.strip() else ""
            if raison:
                sautes[raison] = sautes.get(raison, 0) + 1
                print(f"  [SAUTÉ {raison}] {relatif}:{ligne} — {premiere}")
                continue
            if lister:
                print(f"  [À JOUER] {relatif}:{ligne} — {premiere}")
                joues += 1
                continue
            assert projet is not None
            script, substitution = substituer(script)
            if substitution:
                substitutions += 1
                print(f"  [SUBSTITUÉ] {relatif}:{ligne} — {substitution}")
            code, sortie = executer(script, projet)
            joues += 1
            if code != 0:
                print(f"  [ÉCHEC] {relatif}:{ligne} — code {code}")
                print(f"          commande : {premiere}")
                for l in sortie.strip().splitlines()[-12:]:
                    print(f"          | {l}")
                print(f"ARRÊT : le lecteur se serait arrêté ici, à la page {relatif}.")
                return 1
            print(f"  [OK] {relatif}:{ligne} — {premiere}")

    detail = ", ".join(f"{n} {r.lower()}" for r, n in sorted(sautes.items())) or "aucun"
    print(f"Blocs joués : {joues} ; sautés : {detail} ; substitués : {substitutions}")
    if lister:
        print("Recensement seul : rien n'a été exécuté.")
        return 0
    print(f"OK : le parcours {paquet} se déroule de bout en bout.")
    return 0


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", required=True, metavar="NOM",
                        help="nom court de l'opt-in (ex. « sqlite »)")
    parser.add_argument("--project", metavar="CHEMIN", default=None, type=Path,
                        help="projet Forge où jouer le parcours")
    parser.add_argument("--list", action="store_true", dest="lister",
                        help="recenser les blocs sans rien exécuter")
    args = parser.parse_args(argv)
    if not args.lister and args.project is None:
        parser.error("--project est requis pour exécuter (ou utilisez --list)")
    return parcourir(args.package, args.project, lister=args.lister)


if __name__ == "__main__":
    sys.exit(main())
