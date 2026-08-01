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
BLOC_QUELCONQUE = re.compile(r"^```(\w+)\s*$(.*?)^```\s*$", re.MULTILINE | re.DOTALL)

#: Première ligne d'un bloc nommant le fichier où le lecteur le pose.
#: Convention déjà suivie par 187 des 279 blocs `python` des parcours.
#: Le nom peut être suivi d'une précision, « # worker.py, à la racine de
#: l'application ». Il doit venir EN PREMIER après le dièse, sans quoi une
#: phrase citant un fichier serait prise pour une consigne de pose.
CHEMIN_DU_BLOC = re.compile(
    r"^\s*(?:#|<!--)\s*([\w./-]+\.(?:py|html|json))(?:[,:( ].*)?\s*(?:-->)?$")

#: Langages dont un bloc est un FICHIER que le lecteur écrit.
LANGAGES_FICHIER = ("python", "html", "json")

#: Un `<nom>` que le lecteur remplace : la commande n'est pas exécutable telle quelle.
PLACEHOLDER = re.compile(r"<[a-zA-Zà-ÿ][\w à-ÿ'-]*>")

#: Commandes qui ne rendent jamais la main. Les lancer figerait le harnais.
# `docker run` d'un serveur de base occupe le terminal tant qu'il tourne :
# les parcours des backends l'emploient pour proposer une instance jetable.
BLOQUANTES = ("forge run", "mkdocs serve", "npm run dev", "python -m http.server",
              "docker run", "podman run", "worker.py")

#: Gestes qui sortent du terminal, donc hors de portée d'une exécution.
#:
#: `sudo` en fait partie : les parcours des backends serveur font ouvrir une
#: session d'administration pour y coller le SQL de provisioning que `db:init`
#: affiche (ADR-067). C'est un geste d'administrateur, distinct du projet, et
#: la session ainsi ouverte attend une saisie humaine.
MANUELLES = ("$EDITOR", "nano ", "vim ", "code ", "sudo ")

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

#: Options qui rendent DÉJÀ la commande non interactive.
#:
#: Sans elles, le harnais ajoutait `--no-input` à un `make:entity --field …`
#: qui décrivait pourtant ses champs, et annonçait une substitution là où il
#: n'y avait rien à substituer. Annoncer un geste qu'on ne fait pas est aussi
#: trompeur que taire celui qu'on fait.
DEJA_NON_INTERACTIF = ("--field", "--no-input")

#: Commandes interactives SANS option documentée pour s'en passer.
#:
#: Vide depuis `ENTITIES-NON-INTERACTIVE-001` et `-002`, qui ont ouvert
#: `make:entity` et `make:relation`. La catégorie reste, car le constat se
#: reproduira : elle nomme la limite au lieu de la laisser passer pour un échec.
INTERACTIVES: "tuple[str, ...]" = ()

#: Commandes dont le harnais ne peut pas DEVINER les arguments.
#:
#: `make:relation` est scriptable depuis `ENTITIES-NON-INTERACTIVE-002`, mais
#: elle exige les deux entités que le parcours a en tête, et le harnais ne les
#: connaît pas. Un remplacement figé produirait un faux échec sur un parcours
#: sain, ce qui est pire qu'un saut annoncé.
SANS_ARGUMENTS_INFERABLES = ("forge make:relation",)

#: Adresses qui désignent le serveur du projet, lancé par un bloc bloquant.
#:
#: Les parcours démarrent l'application avec `forge run`, que le harnais saute,
#: puis interrogent ses routes au `curl`. Ces appels dépendent donc d'un serveur
#: que le harnais n'a pas démarré : les jouer mesurerait son propre saut.
SERVEUR_LOCAL = ("localhost", "127.0.0.1")

#: Commandes exigeant un service externe que le harnais ne monte pas.
#:
#: `iot:listen` s'abonne à un broker MQTT. Son absence n'est pas un défaut du
#: parcours, et le refus qu'elle produit est d'ailleurs clair et juste.
SERVICES_EXTERNES = ("forge iot:listen", "forge iot:publish")

#: Commandes dont le code retour EST le rapport, pas un verdict.
#:
#: `deploy:check` documente lui-même que « la sortie vaut code 1 si au moins
#: une erreur bloquante est détectée ». Sur un projet non préparé pour la
#: production, ce 1 est le comportement annoncé, non un parcours cassé. Les
#: confondre ferait tenir une commande honnête pour un défaut.
#: Liste explicite et courte, non une règle sur « tout ce qui ressemble à un
#: diagnostic » : `forge doctor` sort en 0 et se vérifie très bien, une règle
#: large le sautait et retirait de la couverture un bloc qui marchait.
DIAGNOSTICS = ("forge deploy:check", "forge iot:doctor")

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


def blocs_ordonnes(page: Path) -> "list[tuple[int, str, str]]":
    """Tous les blocs de la page, dans l'ordre, avec leur langage.

    Un parcours alterne « posez ce fichier » et « lancez cette commande ».
    Ne lire que les blocs `bash` revenait à jouer la seconde moitié d'un
    dialogue : la commande qui lance un fichier échouait, faute du fichier.
    """
    texte = page.read_text(encoding="utf-8")
    return [(texte[: m.start()].count("\n") + 1, m.group(1), m.group(2))
            for m in BLOC_QUELCONQUE.finditer(texte)]


def fichier_du_bloc(contenu: str) -> "str | None":
    """Chemin annoncé en première ligne du bloc, s'il y en a un."""
    lignes = contenu.lstrip().splitlines()
    if not lignes:
        return None
    trouve = CHEMIN_DU_BLOC.match(lignes[0])
    return trouve.group(1) if trouve else None


def compiler(fichiers: "list[Path]", projet: Path) -> "tuple[bool, str]":
    """Le code posé par le parcours se parse-t-il vraiment.

    Douze parcours sur vingt-sept n'ont aucun bloc `bash` : ils se vérifient
    au navigateur. Leur code n'était donc soumis à rien, alors qu'il est ce
    que le lecteur recopie. Le compiler ne prouve pas quil fonctionne, mais
    prouve qu'il n'est pas périmé au point de ne plus se lire.
    """
    python = projet / ".venv" / "bin" / "python"
    cibles = [str(f) for f in fichiers if f.suffix == ".py" and f.is_file()]
    if not cibles or not python.exists():
        return True, ""
    fini = subprocess.run([str(python), "-m", "compileall", "-q", *cibles],
                          capture_output=True, text=True, cwd=projet)
    return fini.returncode == 0, (fini.stdout + fini.stderr)


def poser_fichier(chemin: str, contenu: str, projet: Path) -> str:
    """Écrit le bloc à sa place, sans jamais écraser (principe 9).

    Le refus d'écraser n'est pas une prudence de harnais mais la seule
    lecture correcte : `mvc/routes/__init__.py` est nommé 92 fois dans les
    parcours, toujours pour un FRAGMENT à fusionner. L'écrire entier
    détruirait le câblage que `forge new` a posé.
    """
    cible = projet / chemin
    if cible.exists():
        return "FRAGMENT"
    cible.parent.mkdir(parents=True, exist_ok=True)
    cible.write_text(contenu.lstrip("\n"), encoding="utf-8")
    return "ÉCRIT"


FICHIER_LANCE = re.compile(r"^\s*python3?\s+([\w./-]+\.py)", re.MULTILINE)


def raison_de_sauter(script: str, projet: "Path | None" = None) -> "str | None":
    if PLACEHOLDER.search(script):
        return "PLACEHOLDER"
    if any(motif in script for motif in BLOQUANTES):
        return "BLOQUANT"
    if any(motif in script for motif in MANUELLES):
        return "MANUEL"
    if any(motif in script for motif in INTERACTIVES):
        return "INTERACTIF"
    if any(motif in script for motif in SANS_ARGUMENTS_INFERABLES):
        return "ARGUMENTS"
    if any(hote in script for hote in SERVEUR_LOCAL):
        return "SERVEUR"
    if any(motif in script for motif in SERVICES_EXTERNES):
        return "SERVICE_EXTERNE"
    if any(motif in script for motif in DIAGNOSTICS):
        return "DIAGNOSTIC"
    if projet is not None:
        # Les parcours font écrire un script au lecteur dans un bloc `python`,
        # puis le lancent. Le harnais ne pose aucun fichier : le lancer
        # mesurerait ce qu'il n'a pas fait. Règle générale plutôt que liste
        # de noms de scripts à tenir à jour.
        for chemin in FICHIER_LANCE.findall(script):
            if not (projet / chemin).exists():
                return "FICHIER_ABSENT"
    return None


def substituer(script: str) -> "tuple[str, str | None]":
    """Rend le script à jouer et, le cas échéant, la substitution opérée."""
    for commande, option in EQUIVALENTS.items():
        lignes = script.splitlines()
        for index, ligne in enumerate(lignes):
            if commande in ligne and not any(o in ligne for o in DEJA_NON_INTERACTIF):
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
    poses: "dict[str, int]" = {}
    ecrits_chemins: "list[Path]" = []
    sautes: "dict[str, int]" = {}
    print(f"=== Parcours {paquet} : {len(pages)} page(s), dans l'ordre du site ===")

    for page in pages:
        relatif = page.relative_to(PROJECT_ROOT)
        for ligne, langage, contenu in blocs_ordonnes(page):
            if langage in LANGAGES_FICHIER:
                chemin = fichier_du_bloc(contenu)
                if chemin is None or projet is None or lister:
                    continue
                verdict = poser_fichier(chemin, contenu, projet)
                poses[verdict] = poses.get(verdict, 0) + 1
                if verdict == "ÉCRIT":
                    ecrits_chemins.append(projet / chemin)
                print(f"  [{verdict}] {relatif}:{ligne} — {chemin}")
                continue
            if langage != "bash":
                continue
            script = contenu
            raison = raison_de_sauter(script, projet)
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
    ecrits = poses.get("ÉCRIT", 0)
    fragments = poses.get("FRAGMENT", 0)
    print(f"Blocs joués : {joues} ; sautés : {detail} ; substitués : {substitutions}")
    if ecrits or fragments:
        print(f"Fichiers posés : {ecrits} ; fragments laissés au lecteur : {fragments}")
    if projet is not None and ecrits_chemins:
        propre, sortie = compiler(ecrits_chemins, projet)
        if not propre:
            print("  [ÉCHEC] le code posé par le parcours ne compile pas :")
            for l in sortie.strip().splitlines()[-10:]:
                print(f"          | {l}")
            return 1
        py = sum(1 for f in ecrits_chemins if f.suffix == ".py")
        if py:
            print(f"Code posé : {py} fichier(s) Python, tous compilés.")
    if lister:
        print("Recensement seul : rien n'a été exécuté.")
        return 0
    if joues == 0:
        # Annoncer « de bout en bout » sans avoir rien joué se lirait comme
        # une couverture, alors que c'est l'inverse. Même leçon que le
        # verdict pytest lu dans le texte plutôt que dans le code retour
        # (RELEASE-AUDIT-SHIPPED-SURFACE-001).
        print(f"RIEN JOUÉ : le parcours {paquet} n'a aucun bloc exécutable ; "
              "sa vérification reste entièrement manuelle.")
        return 0
    print(f"OK : le parcours {paquet} se déroule de bout en bout "
          f"({joues} bloc(s) joué(s)).")
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
