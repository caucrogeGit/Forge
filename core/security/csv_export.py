# pyright: strict
"""
core/security/csv_export.py — Neutralisation de l'injection de formule CSV
==============================================================================

Un tableur (Excel, LibreOffice, Google Sheets) interprète comme une **formule**
toute cellule commençant par certains caractères. Une valeur enregistrée par un
utilisateur, par exemple ``=1+1`` ou ``@SUM(A1)``, redevient donc du code
exécutable à l'ouverture du fichier exporté. C'est l'injection de formule CSV,
aussi appelée injection CSV.

Le risque ne vit pas dans l'application qui exporte, mais chez la personne qui
ouvre le fichier : exfiltration de données vers une URL, exécution de commandes
via ``DDE`` sur certains tableurs. Le guillemetage CSV (``csv.QUOTE_ALL``) ne
protège pas : il garantit un fichier bien formé, pas une cellule inerte.

La parade retenue est celle de l'OWASP : préfixer la valeur d'une apostrophe
simple, que les tableurs traitent comme « le contenu qui suit est du texte ».

Caractères déclencheurs couverts
--------------------------------

- ``=`` ``+`` ``-`` ``@`` : ouvrent une formule ;
- ``\\t`` (tabulation) et ``\\r`` (retour chariot) : ignorés à l'affichage, ils
  laissent le caractère déclencheur suivant en tête réelle de cellule et
  contournent donc un filtre qui ne regarderait que les quatre premiers.

Cette primitive vit dans le cœur, et non dans le code généré, pour une raison
de fond : une règle de sécurité recopiée dans chaque contrôleur ne peut plus
être corrigée par une montée de version (charte, principe 9 — Forge ne réécrit
jamais le code utilisateur). Le CRUD généré l'**appelle** ; il ne la duplique
pas.

Ce module ne fabrique pas de CSV : il n'assainit qu'une valeur de cellule. Le
formatage reste à la charge de l'appelant, avec le module ``csv`` standard.
"""

from __future__ import annotations

#: Caractères qui, en tête de cellule, ouvrent une formule chez un tableur.
FORMULA_TRIGGERS = ("=", "+", "-", "@")

#: Caractères invisibles qui décalent la tête réelle de cellule. Un tableur les
#: ignore à l'affichage : ``"\\t=1+1"`` s'ouvre donc comme la formule ``=1+1``.
INVISIBLE_LEADERS = ("\t", "\r")


def escape_csv_field(value: str) -> str:
    """Rend `value` inerte pour un tableur, en préfixant une apostrophe si besoin.

    La valeur est renvoyée telle quelle quand elle ne peut pas être interprétée
    comme une formule, ce qui est le cas courant. Aucun caractère n'est retiré
    ni remplacé : seule une apostrophe peut être ajoutée en tête, ce qui reste
    lisible à la relecture du fichier.

    Les caractères invisibles de tête sont franchis avant l'examen : sans cela,
    ``"\\t=1+1"`` passerait le contrôle et redeviendrait une formule à
    l'ouverture.

    >>> escape_csv_field("Dupont")
    'Dupont'
    >>> escape_csv_field("=1+1")
    "'=1+1"
    >>> escape_csv_field("\\t=1+1")
    "'\\t=1+1"
    """
    if not value:
        return value

    first = value.lstrip("".join(INVISIBLE_LEADERS))[:1]
    if first and first in FORMULA_TRIGGERS:
        if _est_un_nombre(value):
            return value
        return "'" + value
    return value


def _est_un_nombre(value: str) -> bool:
    """Vrai si `value` est un nombre écrit tel quel, sans rien autour.

    Un nombre ne peut pas être une formule : un tableur affiche `-12` comme le
    nombre moins douze, pas comme un calcul. L'exempter ne retire donc aucune
    protection, et retire un défaut bien réel (`CSV-NOMBRE-NEGATIF-001`).

    Sans cette exemption, tout nombre négatif d'un export devenait `'-12` :

    - dans le tableur, la colonne des montants passait en **texte**, et les
      sommes cessaient silencieusement de compter les valeurs négatives ;
    - au réimport, la valeur revenait comme la chaîne `'-12`, qu'aucune
      conversion numérique n'accepte. L'aller-retour exporter, corriger dans un
      tableur, réimporter est pourtant la raison d'être du module d'import et
      d'export.

    Le contrôle est **strict**, et c'est voulu :

    - `float()` accepte les espaces de tête, `-1\t` ou ` -1` passeraient. On
      exige donc que la valeur soit égale à sa forme sans espaces ;
    - `-1+1` n'est pas un nombre et reste échappé, comme `=1+1` ;
    - `nan` et `inf` sont refusés : ce ne sont pas des nombres qu'un export
      légitime produit, et leur laisser une exemption ouvrirait la porte à
      des formes exotiques pour un gain nul.
    """
    if value != value.strip():
        return False
    try:
        nombre = float(value)
    except ValueError:
        return False
    # `float("nan")` et `float("inf")` réussissent : on les écarte.
    return nombre == nombre and nombre not in (float("inf"), float("-inf"))
