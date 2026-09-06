# pyright: strict
"""core/app/wiring_guard.py — Le chemin WSGI refuse une application désarmée.

Ticket : `WSGI-UNARMED-APP-GUARD-001`. Décision : ADR-092.

Forge a deux points d'entrée, et ils ne construisent pas la même application.
`app.py` porte le câblage, le squelette le prescrit ainsi. `build_application()`
lit `config.py` et les routes, jamais `app.py`, et `config.py` ne porte que des
valeurs, jamais des objets construits. Un middleware câblé dans `app.py` est donc
invisible du chemin WSGI, et rien ne le signalait.

L'authentification survivait, `Application` posant `AuthMiddleware` par défaut.
Tout ce qui venait après tombait, magasin de sessions compris. L'application
démarrait, répondait 200, authentifiait, et laissait passer ce que les gardes
suivantes auraient refusé.

Ce module lit le câblage déclaré dans `app.py` **sans jamais l'exécuter** :

- l'importer serait exécuter précisément ce que le chemin WSGI cherche à éviter,
  y compris l'analyse d'arguments en tête de fichier, qui pose `APP_ENV=dev`
  quand `--env` est absent, ce qui est le cas sous Gunicorn ;
- une recherche de texte prendrait pour une déclaration l'exemple de câblage que
  le squelette livre **en commentaire**, et refuserait alors de démarrer tout
  projet nu.

D'où l'analyse de l'arbre syntaxique, qui ignore les commentaires par
construction et ne lance rien.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import NamedTuple


class AppWiring(NamedTuple):
    """Ce que `app.py` déclare et que la fabrique générique ne verra pas.

    `middlewares` compte les entrées de la liste passée à `Application(...)`,
    `-1` quand l'argument est présent sous une forme qui ne se compte pas
    (une variable, un appel). `names` nomme celles qui sont identifiables, pour
    que le message d'erreur dise ce qui manque plutôt que combien.
    """

    middlewares: int
    session_store: bool
    names: tuple[str, ...]
    unreadable: bool = False
    """`app.py` existe mais ne s'analyse pas : ce qu'il câble est **inconnu**.

    Distinct de « rien de câblé » (`WSGI-WIRING-GUARD-UNPARSABLE-001`). Une
    erreur de syntaxe se lisait auparavant comme un fichier vide, ce qui
    désarmait la garde chargée de détecter une application désarmée.
    """

    @property
    def is_empty(self) -> bool:
        """Rien de câblé : les deux chemins construisent la même application.

        Faux quand le fichier ne s'analyse pas : on ne sait alors rien, et
        l'ignorance ne vaut pas l'absence.
        """
        if self.unreadable:
            return False
        return self.middlewares == 0 and not self.session_store


_EMPTY = AppWiring(middlewares=0, session_store=False, names=())

#: `app.py` présent et illisible : ce qu'il câble reste inconnu.
_ILLISIBLE = AppWiring(middlewares=0, session_store=False, names=(), unreadable=True)


def _appelle(node: ast.Call, nom: str) -> bool:
    """L'appel vise-t-il `nom`, écrit directement ou par attribut ?

    Couvre `Application(...)` comme `core.app.application.Application(...)`.
    """
    cible = node.func
    if isinstance(cible, ast.Name):
        return cible.id == nom
    if isinstance(cible, ast.Attribute):
        return cible.attr == nom
    return False


def _nom_lisible(node: ast.expr) -> str | None:
    """Nom du middleware tel qu'un humain le reconnaîtra dans le message."""
    if isinstance(node, ast.Call):
        cible = node.func
        if isinstance(cible, ast.Name):
            return cible.id
        if isinstance(cible, ast.Attribute):
            return cible.attr
        return None
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def read_app_wiring(source: str) -> AppWiring:
    """Lit le câblage déclaré dans le source de `app.py`, sans l'exécuter.

    Un source illisible (syntaxe invalide, encodage cassé) rend un câblage vide :
    ce module décide d'un refus de démarrage, il ne doit jamais être la cause
    d'un refus qu'il aurait lui même inventé.
    """
    try:
        arbre = ast.parse(source)
    except (SyntaxError, ValueError):
        # Surtout pas `_EMPTY` : un fichier qui ne s'analyse pas ne dit pas
        # qu'il ne câble rien, il ne dit rien du tout. Mesuré avant correction :
        # le même `app.py` câblant deux middlewares était refusé quand il
        # s'analysait, et servi avec une parenthèse en trop
        # (`WSGI-WIRING-GUARD-UNPARSABLE-001`). Le chemin WSGI n'important
        # jamais `app.py`, rien d'autre n'aurait vu l'erreur.
        return _ILLISIBLE

    middlewares = 0
    session_store = False
    noms: list[str] = []

    for node in ast.walk(arbre):
        if not isinstance(node, ast.Call):
            continue

        if _appelle(node, "Application"):
            for argument in node.keywords:
                if argument.arg != "middlewares":
                    continue
                valeur = argument.value
                if isinstance(valeur, (ast.List, ast.Tuple)):
                    middlewares = max(middlewares, len(valeur.elts))
                    for element in valeur.elts:
                        nom = _nom_lisible(element)
                        if nom is not None and nom not in noms:
                            noms.append(nom)
                elif middlewares == 0:
                    # Une variable ou un appel : présent, mais pas comptable.
                    middlewares = -1

        if _appelle(node, "configure"):
            if any(argument.arg == "session_store" for argument in node.keywords):
                session_store = True

    return AppWiring(middlewares=middlewares, session_store=session_store,
                     names=tuple(noms))


def read_app_wiring_from(app_py: Path) -> AppWiring:
    """Comme `read_app_wiring`, depuis un fichier.

    Un fichier **absent** est vide : un projet peut n'avoir pas d'`app.py`, et
    le chemin WSGI se suffit alors à lui même.

    Un fichier présent mais indécodable est **illisible**, comme un fichier qui
    ne s'analyse pas : ce qu'il câble reste inconnu.
    """
    try:
        texte = app_py.read_text(encoding="utf-8")
    except OSError:
        return _EMPTY
    except UnicodeDecodeError:
        return _ILLISIBLE
    return read_app_wiring(texte)


def format_unarmed_error(wiring: AppWiring, app_py: Path) -> str:
    """Message du refus : ce qui manque, pourquoi, et les deux voies de sortie."""
    if wiring.middlewares < 0:
        combien = "des middlewares"
    else:
        combien = f"{wiring.middlewares} middleware(s)"
    manquants = f" ({', '.join(wiring.names)})" if wiring.names else ""

    lignes = [
        "Le chemin WSGI construirait une application DÉSARMÉE.",
        "",
        f"  {app_py} câble {combien}{manquants}",
    ]
    if wiring.session_store:
        lignes.append("  et un magasin de sessions,")
        lignes.append("  que create_configured_wsgi_app() ne voit ni l'un ni l'autre.")
    else:
        lignes.append("  que create_configured_wsgi_app() ne voit pas.")
    lignes += [
        "",
        "La fabrique générique lit config.py et les routes, jamais app.py :",
        "config.py ne porte que des valeurs, jamais des objets construits.",
        "L'application démarrerait, répondrait 200, authentifierait, et laisserait",
        "passer tout ce que ces gardes auraient refusé (ADR-092).",
    ]
    if wiring.session_store:
        lignes += [
            "",
            "Le magasin de sessions tombe avec : chaque travailleur Gunicorn aurait",
            "le sien, en mémoire, et une session ouverte par l'un serait inconnue",
            "des autres.",
        ]
    lignes += [
        "",
        "Servir l'application déjà armée, dans wsgi.py :",
        "",
        "    from app import application",
        "    from core.app.wsgi import create_wsgi_app",
        "",
        "    application = create_wsgi_app(application)",
        "",
        "app.py doit alors exposer son Application sous un nom public.",
        "Sinon, construire la vôtre et la passer à create_wsgi_app(...).",
    ]
    return "\n".join(lignes)


class UnarmedApplicationError(RuntimeError):
    """Le chemin WSGI générique servirait une application privée de ses gardes."""


def assert_wiring_is_visible(app_py: Path) -> None:
    """Refuse de laisser construire quand `app.py` câble ce que la fabrique ignore.

    Une erreur au démarrage, jamais un avertissement : la panne étant silencieuse
    par nature, seule une panne bruyante la révèle. Un avertissement dans un
    journal de démarrage a déjà été essayé, et n'a rien empêché.
    """
    wiring = read_app_wiring_from(app_py)
    if wiring.is_empty:
        return
    if wiring.unreadable:
        raise UnarmedApplicationError(_message_illisible(app_py))
    raise UnarmedApplicationError(format_unarmed_error(wiring, app_py))


def _message_illisible(app_py: Path) -> str:
    """Refus d'un `app.py` qu'on ne sait pas lire, et pourquoi il est ferme."""
    return "\n".join([
        "Le chemin WSGI ne peut pas savoir si l'application serait ARMÉE.",
        "",
        f"  {app_py} ne s'analyse pas : erreur de syntaxe, ou encodage",
        "  qui n'est pas de l'UTF-8.",
        "",
        "Ce chemin n'importe jamais ce fichier : personne d'autre ne verrait",
        "l'erreur, et l'application partirait sans les gardes qu'il câble.",
        "",
        "  Corrigez le fichier : `python -m py_compile app.py` la nomme.",
    ])
