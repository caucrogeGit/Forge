# pyright: strict
"""Lecture d'un code source sans sa prose, pour les garde-fous de structure.

Un garde-fou qui cherche un motif dans un fichier source cherche presque
toujours une propriété du **code** : « ce module n'importe pas la base », « ce
générateur ne délègue plus l'horodatage au moteur », « cette détection ne passe
pas par le message d'erreur ».

Or `Path.read_text()` rend aussi les docstrings et les commentaires. Un
garde-fou naïf juge donc la prose qui **explique** la règle au même titre que le
code qui l'applique. C'est un faux positif systématique, et il frappe au pire
moment : lorsqu'on documente précisément ce que le code ne fait plus.

Le motif s'est produit cinq fois dans un seul cycle de pré-mortem :

    tests/test_auth_session.py            le mot « forme » d'une docstring
    forge-mvc-images                      un commentaire citant CURRENT_TIMESTAMP
    forge-mvc-entities                    un commentaire citant NOW()
    forge-mvc-iot (deux garde-fous)       une docstring citant l'errno 1146

D'où ce module : une seule façon de lire un source pour le juger.

    from forge_mvc_testing.source_scan import code_sans_prose

    assert "1146" not in code_sans_prose(chemin.read_text(encoding="utf-8"))

Les lignes retirées sont **remplacées par des lignes vides**, jamais
supprimées : les numéros de ligne restent ceux du fichier, ce qui garde les
messages d'échec utilisables.
"""
from __future__ import annotations

import ast
import textwrap

__all__ = ["code_sans_prose", "lignes_de_prose"]


def lignes_de_prose(source: str) -> set[int]:
    """Numéros de ligne (1-indexés) occupés par une docstring ou un commentaire.

    Les docstrings sont trouvées par l'arbre syntaxique, ce qui couvre celles
    des modules, des classes et des fonctions, y compris sur plusieurs lignes.
    Les commentaires sont trouvés par lecture directe, l'arbre ne les gardant
    pas.

    Le source d'une **méthode**, tel que `inspect.getsource` le rend, porte
    l'indentation de sa classe et ne s'analyse donc pas tel quel. Il est
    dédenté au besoin, par `textwrap.dedent` qui ne retire que la marge
    commune. `inspect.cleandoc` ne convient pas ici : il aligne toutes les
    lignes sur la première et aplatit le corps, ce qui casse la syntaxe.
    `dedent` conserve le nombre de lignes, donc la numérotation reste juste.

    Un source syntaxiquement invalide ne fait pas échouer l'appel : seules les
    lignes de commentaire sont alors relevées. Un garde-fou n'a pas à se
    transformer en analyseur de syntaxe.
    """
    lignes: set[int] = set()

    arbre: ast.Module | None
    try:
        arbre = ast.parse(source)
    except SyntaxError:
        try:
            arbre = ast.parse(textwrap.dedent(source))
        except SyntaxError:
            arbre = None

    if arbre is not None:
        for noeud in ast.walk(arbre):
            # `getattr` rend `Any` : l'annotation explicite garde le typage
            # strict du paquet, et `body` est bien une liste d'instructions
            # partout où il existe (module, classe, fonction).
            corps: list[ast.stmt] | None = getattr(noeud, "body", None)
            if not isinstance(corps, list) or not corps:
                continue
            premier: ast.stmt = corps[0]
            if (
                isinstance(premier, ast.Expr)
                and isinstance(premier.value, ast.Constant)
                and isinstance(premier.value.value, str)
            ):
                fin = premier.end_lineno or premier.lineno
                lignes.update(range(premier.lineno, fin + 1))

    for numero, ligne in enumerate(source.splitlines(), start=1):
        if ligne.lstrip().startswith("#"):
            lignes.add(numero)

    return lignes


def code_sans_prose(source: str) -> str:
    """Le source privé de ses docstrings et de ses commentaires.

    Les lignes retirées deviennent vides plutôt que de disparaître, afin que la
    numérotation reste celle du fichier d'origine.
    """
    prose = lignes_de_prose(source)
    return "\n".join(
        "" if numero in prose else ligne
        for numero, ligne in enumerate(source.splitlines(), start=1)
    )
