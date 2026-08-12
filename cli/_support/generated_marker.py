# pyright: strict
"""Empreinte de contrat des fichiers engendrés (ADR-090).

Forge engendre du code puis ne le retouche plus, et c'est le principe 9.
La conséquence est qu'un correctif livré dans un générateur **n'atteint aucune
application déjà engendrée**, et que son auteur ne l'apprend pas.

Ce module porte le format de l'empreinte qui rend cet écart visible, et le
registre par générateur qui dit ce qui a changé à chaque montée.

## Ce que l'empreinte porte, et pourquoi

Elle porte le **numéro de contrat du générateur**, et rien d'autre.

Pas un condensat du contenu : un fichier engendré est fait pour être édité, si
bien qu'un condensat serait faux dès la première ligne ajoutée par l'auteur, et
l'avertissement deviendrait permanent, donc invisible.

Pas la version du framework : elle ferait crier à chaque montée, y compris
celles qui n'ont rien changé au générateur concerné, et on apprendrait à
ignorer l'avertissement.

Un contrat monte quand la **sortie du générateur change de façon signifiante**,
à ce moment seulement, et la montée est décrite dans `CONTRATS`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "MARQUEUR",
    "CONTRATS",
    "Montee",
    "GeneratorContract",
    "ligne_de_marqueur",
    "contrat_du_fichier",
    "montees_manquees",
]

#: Forme de la ligne d'en-tête posée en tête de chaque fichier engendré.
#: Volontairement lisible et commentée : le principe 3 refuse la magie cachée,
#: et un auteur doit pouvoir comprendre cette ligne sans documentation.
MARQUEUR = "# forge:generated {commande} contrat={contrat}"

# `fullmatch` et non `match` : sur une expression ancrée, `match` laisse
# passer un saut de ligne final, `$` s'y accordant. Les ancres sont donc
# retirées, `fullmatch` les rendant redondantes.
_MOTIF = re.compile(r"#\s*forge:generated\s+(?P<commande>[\w:.-]+)\s+contrat=(?P<contrat>\d+)\s*")


@dataclass(frozen=True)
class Montee:
    """Une montée de contrat : ce qui a changé, et si cela touche la sécurité."""

    contrat: int
    resume: str
    securite: bool = False


@dataclass(frozen=True)
class GeneratorContract:
    """Contrat d'un générateur : son numéro courant et l'histoire de ses montées."""

    commande: str
    contrat: int
    montees: tuple[Montee, ...]


#: Registre des contrats. C'est le vrai travail de l'ADR-090 : sans lui,
#: l'avertissement dit « en retard » sans dire de quoi, et un avertissement
#: qu'on ne sait pas traduire en geste se désapprend en trois semaines.
CONTRATS: dict[str, GeneratorContract] = {
    "make:auth": GeneratorContract(
        commande="make:auth",
        contrat=2,
        montees=(
            Montee(
                contrat=2,
                resume=(
                    "l'identité de connexion passe de la colonne `email` à la colonne "
                    "`login`, et `email` devient un contact facultatif (ADR-089). Le "
                    "contrôleur lit `request.form(\"login\")`, le modèle expose "
                    "`load_user_by_login`, et la casse de l'identifiant est conservée, "
                    "ce qui rouvre la connexion sur SQLite"
                ),
                securite=True,
            ),
        ),
    ),
}


def ligne_de_marqueur(commande: str) -> str:
    """Ligne d'en-tête à poser en tête du fichier engendré par `commande`."""
    contrat = CONTRATS[commande].contrat
    return MARQUEUR.format(commande=commande, contrat=contrat)


def contrat_du_fichier(chemin: Path) -> "tuple[str, int] | None":
    """Lit l'empreinte d'un fichier, ou `None` s'il n'en porte pas.

    `None` ne veut pas dire « en retard » : il veut dire « on ne sait pas ».
    Toutes les applications antérieures à l'ADR-090 sont dans ce cas, et un
    fichier dont l'auteur a effacé l'en-tête aussi. Le contrôle le dit plutôt
    que d'accuser.
    """
    try:
        texte = chemin.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    # L'empreinte est cherchée dans les premières lignes seulement : un fichier
    # applicatif peut contenir n'importe quoi plus bas, y compris un exemple.
    for ligne in texte.splitlines()[:10]:
        trouve = _MOTIF.fullmatch(ligne.strip())
        if trouve:
            return (trouve.group("commande"), int(trouve.group("contrat")))
    return None


def montees_manquees(commande: str, contrat_du_projet: int) -> tuple[Montee, ...]:
    """Montées livrées depuis le contrat que porte le fichier du projet.

    Vide quand le fichier est à jour, ce qui est le cas ordinaire et doit
    rester silencieux.
    """
    connu = CONTRATS.get(commande)
    if connu is None:
        return ()
    return tuple(m for m in connu.montees if m.contrat > contrat_du_projet)
