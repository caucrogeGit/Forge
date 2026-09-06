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

# Les fences peuvent être INDENTÉES : dans un encart `!!! note` ou un bloc à
# onglets, le contenu est décalé de quatre espaces. Mesuré sur les pages de
# référence : 181 blocs `bash` indentés contre 85 en marge, soit plus des deux
# tiers invisibles à un motif ancré en colonne zéro. La fermeture doit être au
# MÊME retrait, sans quoi un bloc imbriqué avalerait la suite de la page.
BLOC_BASH = re.compile(r"^([ \t]*)```bash[ \t]*$(.*?)^\1```[ \t]*$",
                       re.MULTILINE | re.DOTALL)
BLOC_QUELCONQUE = re.compile(r"^([ \t]*)```(\w+)[ \t]*$(.*?)^\1```[ \t]*$",
                             re.MULTILINE | re.DOTALL)

#: Première ligne d'un bloc nommant le fichier où le lecteur le pose.
#: Convention déjà suivie par 187 des 279 blocs `python` des parcours.
#: Le nom peut être suivi d'une précision, « # worker.py, à la racine de
#: l'application ». Il doit venir EN PREMIER après le dièse, sans quoi une
#: phrase citant un fichier serait prise pour une consigne de pose.
#: Trois façons de nommer la destination, toutes légitimes : le dièse
#: Python, le commentaire HTML, et le commentaire **Jinja** `{# … #}`.
#: Ce dernier est le bon choix pour un gabarit : un commentaire HTML
#: serait envoyé au client, un commentaire Jinja est retiré au rendu.
#: L'ignorer laissait les gabarits non posés, et les pages du parcours
#: échouaient alors sur `TemplateNotFound`.
CHEMIN_DU_BLOC = re.compile(
    r"^\s*(?:\{#|#|<!--)\s*([\w./-]+\.(?:py|html|json))"
    r"(?:[,:( ].*?)?\s*(?:#\}|-->)?$")

#: Langages dont un bloc est un FICHIER que le lecteur écrit.
LANGAGES_FICHIER = ("python", "html", "json")

#: Un `<nom>` que le lecteur remplace : la commande n'est pas exécutable telle quelle.
PLACEHOLDER = re.compile(r"<[a-zA-Zà-ÿ][\w à-ÿ'-]*>")

#: Commandes qui ne rendent jamais la main. Les lancer figerait le harnais.
# `docker run` d'un serveur de base occupe le terminal tant qu'il tourne :
# les parcours des backends l'emploient pour proposer une instance jetable.
BLOQUANTES = ("forge run", "mkdocs serve", "npm run dev", "python -m http.server",
              "docker run", "podman run", "worker.py",
              # Un observateur de fichiers ne rend pas la main non plus, et
              # `welcome-design` en ouvre un des sa premiere page.
              "npm run watch")

#: Gestes qui sortent du terminal, donc hors de portée d'une exécution.
#:
#: `sudo` en fait partie : les parcours des backends serveur font ouvrir une
#: session d'administration pour y coller le SQL de provisioning que `db:init`
#: affiche (ADR-067). C'est un geste d'administrateur, distinct du projet, et
#: la session ainsi ouverte attend une saisie humaine.
#: Gestes hors du terminal. Le motif désigne une **commande**, donc en tête de
#: ligne ou après un opérateur de shell : `"code "` cherché n'importe où
#: classait « manuelle » toute ligne citant `forge-mvc-qrcode`, dont le nom se
#: termine par « code » (`WELCOME-PREREQUIS-ACTIONNABLE-001`). Un bloc écarté à
#: tort n'est pas joué, et le parcours passe sans avoir rien prouvé.
MANUELLES = ("$EDITOR", "nano", "vim", "code", "sudo")

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


#: Parcours d'accueil du **cœur**, qui vivent à la racine et non dans un paquet.
#:
#: Ils étaient hors de portée de ce harnais (`WELCOME-CORE-EXECUTION-001`), qui
#: résolvait `packages/forge-mvc-<nom>/`. Les vingt-sept parcours d'opt-ins
#: étaient donc joués, et les six du cœur jamais, `welcome-forge` compris,
#: c'est à dire le premier que lit un débutant. Cet outil existe précisément
#: parce que lire un parcours ne dit pas s'il marche.
PARCOURS_DU_COEUR = (
    "welcome-forge", "welcome-design", "welcome-events",
    "welcome-helpers", "welcome-markdown", "welcome-outils",
)


def _source(paquet: str) -> "tuple[Path, Path, str]":
    """Config mkdocs, dossier des pages, et préfixe des chemins du parcours.

    Deux emplacements, une seule règle de lecture : le `nav` fait autorité,
    parce que c'est l'ordre que le lecteur voit dans le menu.
    """
    if paquet in PARCOURS_DU_COEUR:
        return (PROJECT_ROOT / "mkdocs.yml", PROJECT_ROOT / "docs", f"starters/{paquet}/")
    dossier = PROJECT_ROOT / "packages" / f"forge-mvc-{paquet}"
    return (dossier / "mkdocs.yml", dossier / "docs", "welcome/")


def nav_pages(paquet: str, *, welcome_seul: bool = True) -> "list[Path]":
    """Pages du paquet, dans l'ordre du menu du site.

    `welcome_seul=False` ajoute la présentation et la référence, jamais
    jouées jusqu'ici alors qu'elles portent 113 blocs `bash` et qu'on les
    consulte pour une commande précise, souvent sans lire le parcours.

    Le `nav` est lu comme du texte plutôt que comme du YAML : seul l'ordre des
    chemins `welcome/...` importe, et une dépendance à PyYAML pour cela serait
    disproportionnée.
    """
    config, docs, prefixe = _source(paquet)
    if not config.is_file():
        raise SystemExit(f"Erreur : {config} est introuvable.")
    pages: "list[Path]" = []
    motif = (rf"({prefixe}[\w/-]+\.md)\s*$" if welcome_seul
             else r"([\w/-]*\.md)\s*$")
    for ligne in config.read_text(encoding="utf-8").splitlines():
        trouve = re.search(motif, ligne)
        if trouve:
            page = docs / trouve.group(1)
            if page.is_file():
                pages.append(page)
    return pages


def _sans_retrait(contenu: str, retrait: str) -> str:
    """Rend le bloc tel que le lecteur le colle, sans le décalage de l'encart."""
    if not retrait:
        return contenu
    lignes = [l[len(retrait):] if l.startswith(retrait) else l
              for l in contenu.splitlines()]
    return "\n".join(lignes)


SECTION = re.compile(r'^\?\?\? note "(?:\d+\.\s*)?([^"]+)"', re.MULTILINE)


def decouper_section(texte: str, titre: str) -> str:
    """Rend la seule section nommée, ou une chaîne vide.

    Une page de référence n'est **pas** une séquence : elle catalogue des
    alternatives. Mesuré sur la référence SQLite, la jouer de haut en bas
    installerait depuis PyPI **puis** depuis Git, puis défairait la
    configuration avec `db:config --remove`. Seul « Mise en service » est un
    ordre à suivre, et 26 paquets sur 27 en portent un.
    """
    debuts = [(m.start(), m.group(1).strip()) for m in SECTION.finditer(texte)]
    for index, (position, nom) in enumerate(debuts):
        if nom.lower() != titre.lower():
            continue
        fin = debuts[index + 1][0] if index + 1 < len(debuts) else len(texte)
        return texte[position:fin]
    return ""


def blocs(page: Path) -> "list[tuple[int, str]]":
    texte = page.read_text(encoding="utf-8")
    return [(texte[: m.start()].count("\n") + 1,
             _sans_retrait(m.group(2), m.group(1)))
            for m in BLOC_BASH.finditer(texte)]


def blocs_ordonnes(page: Path) -> "list[tuple[int, str, str]]":
    """Tous les blocs de la page, dans l'ordre, avec leur langage.

    Un parcours alterne « posez ce fichier » et « lancez cette commande ».
    Ne lire que les blocs `bash` revenait à jouer la seconde moitié d'un
    dialogue : la commande qui lance un fichier échouait, faute du fichier.
    """
    texte = page.read_text(encoding="utf-8")
    return [(texte[: m.start()].count("\n") + 1, m.group(2),
             _sans_retrait(m.group(3), m.group(1)))
            for m in BLOC_QUELCONQUE.finditer(texte)]


def fichier_du_bloc(contenu: str) -> "str | None":
    """Chemin annoncé en première ligne du bloc, s'il y en a un."""
    lignes = contenu.lstrip().splitlines()
    if not lignes:
        return None
    trouve = CHEMIN_DU_BLOC.fullmatch(lignes[0])
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


#: Fichiers dont un bloc est un FRAGMENT à ajouter, non un contenu complet.
#:
#: `mvc/routes/__init__.py` est nommé 92 fois dans les parcours, toujours pour
#: quelques lignes de câblage. Le lecteur les recopie à la main : Forge
#: n'injecte jamais de route (ADR-085). Le harnais joue son rôle et les ajoute
#: en fin de fichier, `router` y étant déjà construit et l'ordre
#: d'enregistrement étant sans effet sur des chemins distincts.
FICHIERS_A_FUSIONNER = ("mvc/routes/__init__.py",)


def fusionner_fragment(chemin: str, contenu: str, projet: Path) -> str:
    """Ajoute le fragment en fin de fichier, sans toucher à ce qui existe."""
    cible = projet / chemin
    lignes = contenu.strip().splitlines()
    # La première ligne nomme le fichier : elle n'est pas du code.
    corps = "\n".join(lignes[1:]).strip()
    if not corps or corps in cible.read_text(encoding="utf-8"):
        return "DÉJÀ FUSIONNÉ"
    with cible.open("a", encoding="utf-8") as fichier:
        fichier.write(f"\n\n{corps}\n")
    return "FUSIONNÉ"


def poser_fichier(chemin: str, contenu: str, projet: Path) -> str:
    """Écrit le bloc à sa place, sans jamais écraser (principe 9).

    Le refus d'écraser n'est pas une prudence de harnais mais la seule
    lecture correcte : `mvc/routes/__init__.py` est nommé 92 fois dans les
    parcours, toujours pour un FRAGMENT à fusionner. L'écrire entier
    détruirait le câblage que `forge new` a posé.
    """
    cible = projet / chemin
    if chemin in FICHIERS_A_FUSIONNER and cible.exists():
        return fusionner_fragment(chemin, contenu, projet)
    if cible.exists():
        return "FRAGMENT"
    cible.parent.mkdir(parents=True, exist_ok=True)
    cible.write_text(contenu.lstrip("\n"), encoding="utf-8")
    return "ÉCRIT"


#: Mots-clés qui ouvrent une construction shell sur plusieurs lignes.
_CONSTRUCTIONS_SHELL = ("if ", "for ", "while ", "case ", "until ", "function ")


def _lignes_logiques(script: str) -> "list[str]":
    """Lignes du bloc, continuations `\\` réunies en une seule.

    Le tri et l'exécution se font ligne par ligne ; une commande étalée sur
    plusieurs lignes doit donc rester d'un seul tenant, faute de quoi sa suite
    est prise pour une commande (`WELCOME-HARNAIS-LIGNE-A-LIGNE-001`).
    """
    logiques: "list[str]" = []
    courante = ""
    for brute in script.splitlines():
        if not brute.strip():
            continue
        courante = f"{courante}\n{brute}" if courante else brute
        if not brute.rstrip().endswith("\\"):
            logiques.append(courante)
            courante = ""
    if courante:
        logiques.append(courante)
    return logiques


def _porte_une_construction_shell(script: str) -> bool:
    """Vrai si le bloc ne peut pas être coupé ligne par ligne.

    Un `if ... then ... fi`, une boucle ou un heredoc forment un tout : les
    jouer séparément fait rendre à `bash` « fin de fichier prématurée », et le
    harnais accuserait alors le parcours de son propre découpage
    (`WELCOME-HARNAIS-LIGNE-A-LIGNE-001`).
    """
    if "<<" in script:
        return True
    for ligne in script.splitlines():
        nue = ligne.strip()
        if any(nue.startswith(mot) for mot in _CONSTRUCTIONS_SHELL):
            return True
        if nue.endswith("\\"):
            return True
    return False


def _invoque_une_commande(script: str, motifs: "tuple[str, ...]") -> bool:
    """Vrai si l'un des motifs est INVOQUÉ, et non simplement cité.

    Une commande occupe le début d'une ligne, ou suit un opérateur de shell.
    La chercher n'importe où confond `code monfichier` avec
    `forge-mvc-qrcode`, dont le nom se termine par les mêmes quatre lettres :
    toute ligne citant cet opt-in était classée « manuelle », donc jamais
    jouée, et le parcours passait sans avoir rien prouvé
    (`WELCOME-PREREQUIS-ACTIONNABLE-001`).
    """
    for ligne in script.splitlines():
        for morceau in re.split(r"\|\||&&|[|;&]", ligne):
            mots = morceau.strip().split()
            if mots and mots[0] in motifs:
                return True
    return False


FICHIER_LANCE = re.compile(r"^\s*python3?\s+([\w./-]+\.py)", re.MULTILINE)

#: Parcours dont les blocs de code sont **montrés**, jamais à jouer.
#:
#: `welcome-markdown` enseigne le Markdown : ses blocs `bash` illustrent une
#: syntaxe de clôture, et la même commande y figure deux fois, littérale puis
#: rendue. Les exécuter n'apprend rien et échoue au second passage, le premier
#: ayant déjà créé le dossier (`WELCOME-CORE-EXECUTION-001`).
#:
#: Le saut est **déclaré et compté**, comme les autres : un harnais qui tait ce
#: qu'il n'a pas fait se lit comme une couverture complète (principe 3).
PARCOURS_ILLUSTRATIFS = ("welcome-markdown",)


def raison_de_sauter(
    script: str, projet: "Path | None" = None, *, paquet: str = ""
) -> "str | None":
    if paquet in PARCOURS_ILLUSTRATIFS:
        return "ILLUSTRATION"
    if PLACEHOLDER.search(script):
        return "PLACEHOLDER"
    if any(motif in script for motif in BLOQUANTES):
        return "BLOQUANT"
    if _invoque_une_commande(script, MANUELLES):
        return "MANUEL"
    if any(motif in script for motif in INTERACTIVES):
        return "INTERACTIF"
    # `forge make:relation` NU ouvre un dialogue ; muni de ses options il est
    # parfaitement jouable. La regle les confondait, et sautait une ligne qui
    # portait deja tout ce qu'il faut (`WELCOME-HARNAIS-LIGNE-A-LIGNE-001`).
    for motif in SANS_ARGUMENTS_INFERABLES:
        for ligne in script.splitlines():
            nue = ligne.split("#")[0].strip()
            if nue.startswith(motif) and nue == motif:
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


def blocs_de_section(page: Path, titre: str) -> "list[tuple[int, str]]":
    """Blocs `bash` de la seule section nommée, aux lignes de la page."""
    texte = page.read_text(encoding="utf-8")
    section = decouper_section(texte, titre)
    if not section:
        return []
    decalage = texte[: texte.index(section)].count("\n")
    return [(decalage + section[: m.start()].count("\n") + 1,
             _sans_retrait(m.group(2), m.group(1)))
            for m in BLOC_BASH.finditer(section)]


ROUTE_DECLAREE = re.compile(
    r"""\.add\(\s*["']([A-Z]+)["']\s*,\s*["']([^"']+)["']""")

#: Sonde exécutée DANS le venv du projet : elle appelle l'application par son
#: point d'entrée WSGI de production, celui que Gunicorn utilise. Pas de
#: serveur à démarrer, pas de port à réserver, pas d'attente de disponibilité.
SONDE_HTTP = """\
import json, sys
from io import BytesIO
from core.app.wsgi import create_configured_wsgi_app
app = create_configured_wsgi_app()
capture = {}
def start_response(statut, entetes, exc_info=None):
    capture["statut"] = statut
resultats = []
for methode, chemin in json.loads(sys.argv[1]):
    environ = {"REQUEST_METHOD": methode, "PATH_INFO": chemin, "QUERY_STRING": "",
               "wsgi.input": BytesIO(b""), "CONTENT_LENGTH": "0",
               "SERVER_NAME": "t", "SERVER_PORT": "80", "wsgi.url_scheme": "http"}
    try:
        corps = b"".join(app(environ, start_response))
        resultats.append([methode, chemin, capture.get("statut", "?"), len(corps)])
    except Exception as exc:
        resultats.append([methode, chemin, type(exc).__name__ + ": " + str(exc)[:80], 0])
print(json.dumps(resultats))
"""


def routes_declarees(fragments: "list[str]") -> "list[tuple[str, str]]":
    """Routes que le parcours déclare lui-même, dans ses fragments de câblage.

    Plus sûr que de deviner des URL dans la prose : ce sont exactement les
    routes que le lecteur vient d'ajouter, donc exactement celles qui doivent
    répondre. Les chemins paramétrés sont écartés, faute de valeur à donner.
    """
    trouvees: "list[tuple[str, str]]" = []
    for fragment in fragments:
        for methode, chemin in ROUTE_DECLAREE.findall(fragment):
            # Seuls les GET : un POST sans jeton CSRF est refusé en 403, et
            # c'est le comportement voulu (principe 7). Forger un jeton pour
            # le contourner ferait mesurer autre chose que la page.
            if methode != "GET" or "{" in chemin or (methode, chemin) in trouvees:
                continue
            trouvees.append((str(methode), str(chemin)))
    return trouvees


def appeler_routes(routes: "list[tuple[str, str]]", projet: Path) -> "tuple[bool, list[str]]":
    """Appelle chaque route et rend (tout va bien, lignes de rapport)."""
    import json

    python = projet / ".venv" / "bin" / "python"
    if not python.exists() or not routes:
        return True, []
    fini = subprocess.run([str(python), "-c", SONDE_HTTP, json.dumps(routes)],
                          cwd=projet, capture_output=True, text=True, timeout=DELAI)
    if fini.returncode != 0:
        return False, ["l'application ne se charge pas :",
                       *fini.stderr.strip().splitlines()[-8:]]
    lignes: "list[str]" = []
    propre = True
    for methode, chemin, statut, taille in json.loads(fini.stdout):
        # Un 4xx prouve que la route est câblée et que le contrôleur tourne :
        # il refuse une requête incomplète, ce qui est son travail. Seul un
        # 5xx est un plantage. Les confondre ferait tenir pour cassée une
        # route qui se défend correctement (`/file-serve/download` sans son
        # paramètre `path`, par exemple).
        ok = isinstance(statut, str) and statut[:1] in "23"
        refus = isinstance(statut, str) and statut[:1] == "4"
        propre = propre and (ok or refus)
        marque = "OK" if ok else ("REFUS" if refus else "ÉCHEC")
        lignes.append(f"  [{marque}] {methode} {chemin} -> {statut} ({taille} o)")
    return propre, lignes


def parcourir(paquet: str, projet: "Path | None", *, lister: bool,
              welcome_seul: bool = True, section: "str | None" = None,
              pages_explicites: "list[Path] | None" = None) -> int:
    """Joue un parcours, résolu depuis le `nav` du paquet ou fourni tel quel.

    `pages_explicites` sert aux garde-fous du harnais lui-même. La propriété
    « un parcours sans rien de jouable annonce RIEN JOUÉ » était vérifiée sur
    un vrai paquet, choisi parce qu'il ne jouait rien : `iot`, puis `mail`,
    puis `import-export` l'ont tour à tour perdue en gagnant du contenu
    jouable. Adosser une propriété du harnais à l'état d'un paquet la rend
    fragile à toute amélioration de la documentation.
    """
    if pages_explicites is not None:
        pages = pages_explicites
    elif section is not None:
        reference = PROJECT_ROOT / "packages" / f"forge-mvc-{paquet}" / "docs" / "reference.md"
        if not reference.is_file():
            raise SystemExit(f"Erreur : {reference} est introuvable.")
        pages = [reference]
    else:
        pages = nav_pages(paquet, welcome_seul=welcome_seul)
    if not pages:
        raise SystemExit(f"Erreur : aucune page dans le nav de forge-mvc-{paquet}.")

    joues = 0
    substitutions = 0
    poses: "dict[str, int]" = {}
    ecrits_chemins: "list[Path]" = []
    fragments_routes: "list[str]" = []
    # Blocs de code que le harnais n'a pas su rattacher a un fichier : la page
    # nomme la cible en prose (« Ajoutez cette methode a la classe X »), motif
    # pedagogique assume. Le harnais ne sait pas fusionner une methode dans une
    # classe : le fichier qu'il pose differe donc de celui du lecteur, et le
    # controle des routes ne peut rien conclure (`WELCOME-CORE-EXECUTION-001`).
    non_attribues = 0
    sautes: "dict[str, int]" = {}
    print(f"=== Parcours {paquet} : {len(pages)} page(s), dans l'ordre du site ===")

    for page in pages:
        relatif = page.relative_to(PROJECT_ROOT)
        contenus = ([(l, "bash", sc) for l, sc in blocs_de_section(page, section)]
                    if section is not None else blocs_ordonnes(page))
        for ligne, langage, contenu in contenus:
            if langage in LANGAGES_FICHIER:
                chemin = fichier_du_bloc(contenu)
                if chemin is None:
                    non_attribues += 1
                if chemin is None or projet is None or lister:
                    continue
                verdict = poser_fichier(chemin, contenu, projet)
                poses[verdict] = poses.get(verdict, 0) + 1
                if verdict == "ÉCRIT":
                    ecrits_chemins.append(projet / chemin)
                if verdict in ("FUSIONNÉ", "DÉJÀ FUSIONNÉ"):
                    fragments_routes.append(contenu)
                print(f"  [{verdict}] {relatif}:{ligne} — {chemin}")
                continue
            if langage != "bash":
                continue
            script = contenu
            # Le tri se fait LIGNE PAR LIGNE, pas bloc par bloc. Un bloc qui
            # enchaîne `forge db:init` puis `forge run` était écarté en entier
            # parce qu'il se termine par un serveur : la commande utile, celle
            # qui crée la table, n'était jamais jouée. Les routes du parcours
            # répondaient alors 503, et le harnais concluait à un échec du
            # parcours au lieu du sien (`WELCOME-HARNAIS-LIGNE-A-LIGNE-001`).
            #
            # Chaque ligne est donc classée pour elle-même ; le bloc n'est
            # sauté en entier que si aucune de ses lignes n'est jouable.
            # Une commande peut s'étaler sur plusieurs lignes par `\\` : les
            # séparer enverrait sa suite au shell comme une commande à part
            # entière. Mesuré sur le `docker run` du parcours SQL Server, dont
            # la seconde ligne partait seule en « -p : commande introuvable ».
            lignes_du_bloc = _lignes_logiques(script)
            jouables = [l for l in lignes_du_bloc
                        if raison_de_sauter(l, projet, paquet=paquet) is None]
            # La commande annoncée est la première JOUÉE, pas la première du
            # bloc : afficher celle qu'on a écartée désignerait un coupable
            # innocent dans le message d'échec.
            premiere = (jouables or lignes_du_bloc or [""])[0]
            if not jouables:
                raison = raison_de_sauter(script, projet, paquet=paquet) or "BLOQUANT"
                sautes[raison] = sautes.get(raison, 0) + 1
                print(f"  [SAUTÉ {raison}] {relatif}:{ligne} — {premiere}")
                continue
            if len(jouables) < len(lignes_du_bloc):
                # Un saut partiel est ANNONCÉ : taire ce qu'on n'a pas fait,
                # c'est laisser lire une couverture complète (principe 3).
                for ecartee in lignes_du_bloc:
                    motif = raison_de_sauter(ecartee, projet, paquet=paquet)
                    if motif:
                        sautes[motif] = sautes.get(motif, 0) + 1
                        print(f"  [SAUTÉ {motif}] {relatif}:{ligne} — {ecartee.strip()}")
            script = "\n".join(jouables)
            if lister:
                print(f"  [À JOUER] {relatif}:{ligne} — {premiere}")
                joues += 1
                continue
            assert projet is not None
            script, substitution = substituer(script)
            if substitution:
                substitutions += 1
                print(f"  [SUBSTITUÉ] {relatif}:{ligne} — {substitution}")
            # Chaque ligne est jouée SÉPARÉMENT, pour que l'échec nomme la
            # commande fautive. Groupées dans un seul `bash -e`, elles ne
            # rendaient qu'un code, et le message accusait la première du
            # bloc : `forge stats:init` était désigné alors que
            # `forge migration:apply` avait échoué juste après.
            # Une construction shell multiligne ne se coupe pas : `if ... fi`,
            # une boucle ou un heredoc perdent leur sens ligne par ligne, et
            # `bash` rend « fin de fichier prématurée ». Ces blocs restent
            # joués d'un seul tenant, au prix d'un message moins précis.
            if _porte_une_construction_shell(script):
                code, sortie = executer(script, projet)
                fautive = premiere
                lignes_a_jouer: "list[str]" = []
            else:
                code, sortie, fautive = 0, "", premiere
                lignes_a_jouer = script.splitlines()
            for une_ligne in lignes_a_jouer:
                if not une_ligne.strip():
                    continue
                code, sortie = executer(une_ligne, projet)
                if code != 0:
                    fautive = une_ligne
                    break
            joues += 1
            if code != 0:
                print(f"  [ÉCHEC] {relatif}:{ligne} — code {code}")
                print(f"          commande : {fautive.strip()}")
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

    # Dernière marche : le code compile, mais la page répond-elle ? Les douze
    # parcours sans bloc `bash` se vérifiaient jusqu'ici au navigateur, donc
    # jamais. Les routes appelées sont celles que le parcours vient de déclarer.
    routes_appelees = 0
    indecis = False
    if projet is not None and fragments_routes:
        routes = routes_declarees(fragments_routes)
        if routes:
            routes_appelees = len(routes)
            print(f"Routes déclarées par le parcours : {len(routes)}")
            propre, lignes = appeler_routes(routes, projet)
            for ligne in lignes:
                print(ligne)
            if not propre and (fragments or non_attribues):
                # Un parcours qui fait AJOUTER une méthode à une classe laisse
                # un fragment que ce harnais ne sait pas fusionner : la classe
                # posée n'a donc pas la méthode que la route vise, et l'appel
                # échoue sur un parcours pourtant juste
                # (`WELCOME-CORE-EXECUTION-001`).
                #
                # Le dire plutôt que le compter comme un échec : un harnais qui
                # accuse à tort finit désactivé, et ne garde alors plus rien.
                laisses = fragments + non_attribues
                indecis = True
                print(f"INDÉCIS : {paquet} laisse {laisses} bloc(s) à recopier "
                      "à la main ; les routes ne peuvent pas être conclues ici.")
            elif not propre:
                print(f"ÉCHEC : le parcours {paquet} déclare des routes qui ne répondent pas.")
                return 1
    if lister:
        print("Recensement seul : rien n'a été exécuté.")
        return 0
    if indecis:
        # Ne JAMAIS conclure « les routes répondent » quand l'application ne se
        # charge pas : un harnais qui annonce un succès qu'il n'a pas constaté
        # vaut moins que pas de harnais du tout.
        print(f"INDÉCIS : le parcours {paquet} demande une relecture humaine ; "
              "le harnais ne peut pas conclure seul.")
        return 0
    if joues == 0 and routes_appelees:
        print(f"OK : le parcours {paquet} n'a aucune commande, mais ses "
              f"{routes_appelees} route(s) répondent.")
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
    parser.add_argument("--toutes-pages", action="store_true",
                        help="ajoute présentation et référence au parcours")
    parser.add_argument("--section", metavar="TITRE", default=None,
                        help="ne jouer que cette section de reference.md "
                             "(ex. « Mise en service », seule séquence de la page)")
    parser.add_argument("--list", action="store_true", dest="lister",
                        help="recenser les blocs sans rien exécuter")
    args = parser.parse_args(argv)
    if not args.lister and args.project is None:
        parser.error("--project est requis pour exécuter (ou utilisez --list)")
    return parcourir(args.package, args.project, lister=args.lister,
                     welcome_seul=not args.toutes_pages, section=args.section)


if __name__ == "__main__":
    sys.exit(main())


#: Ancien nom, conservé : les garde-fous et l'habitude s'y appuient.
nav_welcome = nav_pages
