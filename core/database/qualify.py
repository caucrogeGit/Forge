# pyright: strict
"""
core/database/qualify.py — Qualification des erreurs de pilote (ADR-054)
========================================================================
API interne. Le code applicatif ne s'en sert pas : il attrape les erreurs
portables de `core.database.errors`, que ce module produit.

Le cœur est agnostique BDD : une application ne doit jamais avoir à attraper
une exception propre à un pilote (`mariadb.InterfaceError`,
`psycopg.OperationalError`, ...) sous peine de n'être portable sur aucun autre
backend. Deux conditions seulement sont qualifiées, celles qui ont un usage
métier évident : le doublon et l'indisponibilité passagère. Tout le reste
remonte inchangé, le cœur n'enveloppant pas ce qu'il ne sait pas nommer.

Cette traduction a **deux** appelants, d'où ce module plutôt qu'un détail privé
de l'un d'eux. `core.database.db` qualifie l'échec d'une requête ;
`core.database.transaction` qualifie celui de la validation du bloc, et relaie
celui du corps. Tant que la traduction vivait dans `db`, le chemin
transactionnel rendait l'exception du pilote telle quelle : mesuré sur les
trois backends serveur, un bloc `transaction()` coupé en cours rendait
`mariadb.InterfaceError`, `psycopg.OperationalError` ou `pyodbc.OperationalError`
là où la requête simple rendait un 503 (CORE-TX-LOST-CONNECTION-001).
"""
from typing import NoReturn

from core.database.backend import get_backend
from core.database.errors import DatabaseUnavailableError, UniqueViolationError


def is_unique_violation(error: Exception) -> bool:
    """Demande au backend actif si `error` est un doublon.

    Enveloppé : un backend tiers qui n'implémenterait pas la méthode ne doit
    jamais masquer l'erreur d'origine, laquelle remonte alors telle quelle.
    """
    try:
        return bool(get_backend().is_unique_violation(error))
    except Exception:  # noqa: BLE001 — un backend muet ne masque rien
        return False


def is_unavailable(error: Exception) -> bool:
    """Demande au backend actif si `error` invite à réessayer.

    Même enveloppe que `is_unique_violation`, pour la même raison.
    """
    try:
        return bool(get_backend().is_unavailable(error))
    except Exception:  # noqa: BLE001 — un backend muet ne masque rien
        return False


def qualify(error: Exception) -> Exception:
    """Rend l'erreur portable correspondante, ou `error` inchangée.

    Le doublon a la priorité sur l'indisponibilité : c'est la condition la plus
    spécifique et la plus actionnable, celle qui s'affiche dans un formulaire
    là où l'indisponibilité fait une page d'erreur.
    """
    if is_unique_violation(error):
        return UniqueViolationError(str(error))
    if is_unavailable(error):
        return DatabaseUnavailableError(str(error))
    return error


def raise_qualified(error: Exception) -> NoReturn:
    """Relève `error` sous sa forme portable, en conservant sa cause.

    Point de sortie commun aux deux appelants : ce qui n'est pas qualifiable
    est relevé tel quel, sans cause ajoutée à soi-même.
    """
    qualified = qualify(error)
    if qualified is not error:
        raise qualified from error
    raise error
