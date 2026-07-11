# pyright: strict
"""Primitives de rendu de littéraux SQL (ADR-075).

Servent aux dialectes (contrat ``Dialect``, ADR-054) à rendre une valeur Python
en littéral SQL, pour **générer** du SQL visible et relu (fixtures, clauses
``DEFAULT`` de DDL).

Ne JAMAIS utiliser pour construire une requête à l'exécution : la DML applicative
reste **paramétrée** (placeholders de ``core.database.db``), sous peine
d'injection SQL (charte principe 7). Le rendu de littéral ne s'applique qu'à des
données maîtrisées par le développeur, dans des artefacts qu'il relit.
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime
from decimal import Decimal


class LiteralError(TypeError):
    """Type Python non rendu en littéral SQL par ce dialecte."""


def escape_string(value: str, *, national: bool = False) -> str:
    """Chaîne SQL : guillemets simples, ``'`` doublé en ``''``.

    ``national=True`` préfixe ``N`` (SQL Server, pour l'Unicode : ``N'...'``).
    """
    doubled = value.replace("'", "''")
    prefix = "N" if national else ""
    return f"{prefix}'{doubled}'"


def render_literal_value(
    value: object,
    *,
    bool_true: str,
    bool_false: str,
    render_string: Callable[[str], str],
    render_date: Callable[[date], str],
    render_datetime: Callable[[datetime], str],
) -> str:
    """Rendu commun d'un littéral SQL, paramétré par les traits du dialecte.

    Ordre des tests significatif : ``bool`` avant ``int`` (``bool`` est un
    ``int``), ``datetime`` avant ``date`` (``datetime`` est un ``date``).
    Lève ``LiteralError`` sur un type non couvert (jamais de ``str()`` silencieux).
    """
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return bool_true if value else bool_false
    if isinstance(value, int):
        return str(value)
    if isinstance(value, (float, Decimal)):
        return str(value)
    if isinstance(value, str):
        return render_string(value)
    if isinstance(value, datetime):
        return render_datetime(value)
    if isinstance(value, date):
        return render_date(value)
    raise LiteralError(
        f"Type non rendu en littéral SQL : {type(value).__name__}. "
        "Types couverts : None, bool, int, float, Decimal, str, date, datetime."
    )
