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
from core.database.errors import (
    DatabaseUnavailableError,
    ForeignKeyViolationError,
    UniqueViolationError,
)


def is_unique_violation(error: Exception) -> bool:
    """Demande au backend actif si `error` est un doublon.

    Enveloppé : un backend tiers qui n'implémenterait pas la méthode ne doit
    jamais masquer l'erreur d'origine, laquelle remonte alors telle quelle.
    """
    try:
        return bool(get_backend().is_unique_violation(error))
    except Exception:  # noqa: BLE001 — un backend muet ne masque rien
        return False


def is_undefined_table_error(error: Exception) -> bool:
    """Demande au backend actif si `error` signale une table absente.

    Même enveloppe que `is_unique_violation`, pour la même raison : un backend
    tiers qui n'implémenterait pas la méthode ne doit jamais masquer l'erreur
    d'origine.

    Ne participe pas à `qualify` : une table absente relève du diagnostic et de
    l'outillage, pas du chemin de requête applicatif. Le cœur n'enveloppe que
    ce qui a un usage métier, le doublon et l'indisponibilité.
    """
    try:
        return bool(get_backend().is_undefined_table_error(error))
    except Exception:  # noqa: BLE001 — un backend muet ne masque rien
        return False


def is_foreign_key_violation(error: Exception) -> bool:
    """Demande au backend actif si `error` est une violation de clé étrangère.

    Même enveloppe que `is_unique_violation`, pour la même raison
    (`DB-ERROR-MESSAGES-HOMOGENES-001`).
    """
    try:
        return bool(get_backend().is_foreign_key_violation(error))
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

    L'ordre suit la spécificité, du plus actionnable au moins actionnable.

    Le doublon et la clé étrangère s'affichent dans un formulaire, en face d'un
    champ ou en tête de page ; l'indisponibilité fait une page d'erreur et un
    503. Une condition spécifique qualifiée en indisponibilité enverrait
    attendre là où il faut corriger une saisie.

    Doublon et clé étrangère ne se recouvrent pas : aucun backend ne rend le
    même signal pour les deux, et l'ordre entre eux n'a donc pas d'effet. Il
    est fixé pour que deux lectures du code donnent la même réponse.
    """
    if is_unique_violation(error):
        return UniqueViolationError(str(error))
    if is_foreign_key_violation(error):
        return ForeignKeyViolationError(str(error))
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
