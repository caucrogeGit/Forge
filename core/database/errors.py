# pyright: strict
"""
core/database/errors.py — Erreurs de base de données portables (ADR-054)
========================================================================
Le cœur est agnostique BDD : une application ne doit jamais avoir à
attraper une exception propre à un pilote (`mariadb.IntegrityError`,
`psycopg.errors.UniqueViolation`, ...) sous peine de n'être portable sur
aucun autre backend.

Ce module expose les erreurs que `core.database.db` lève à la place, une
fois le backend actif consulté (`DatabaseBackend.is_unique_violation`).

Seules les erreurs ayant un **usage métier évident** sont traduites. Les
autres exceptions de pilote remontent inchangées : le cœur n'enveloppe pas
ce qu'il ne sait pas qualifier.
"""


class DatabaseError(Exception):
    """Racine des erreurs de base de données qualifiées par Forge."""


class UniqueViolationError(DatabaseError):
    """Une contrainte d'unicité a été violée (doublon).

    Levée par `core.database.db` quand le backend actif reconnaît la
    violation dans l'exception de son pilote. L'exception d'origine reste
    accessible via ``__cause__``.

    Usage dans un contrôleur :

        from core.database.errors import UniqueViolationError

        try:
            user_id = create_user(form.value("email"))
        except UniqueViolationError:
            form.add_error("email", "Cette adresse est déjà utilisée.")

    Ce que cette erreur ne dit **pas** : quelle contrainte a sauté. Sur une
    unicité composite, le nom de la contrainte n'est pas normalisé entre
    SGBD ; si l'application doit le distinguer, elle vérifie elle-même
    avant d'insérer.
    """
