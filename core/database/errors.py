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


class DatabaseConfigurationError(DatabaseError):
    """La configuration ne permet pas d'atteindre la base.

    Rien n'est en panne et aucune requête n'est fautive : il manque un
    renseignement que seul l'utilisateur peut fournir, un `DB_NAME` absent, un
    chemin qui ne désigne rien, un couple hôte et port introuvable dans l'env.

    Elle se distingue de `DatabaseUnavailableError`, qui décrit une condition
    passagère où réessayer suffit. Ici réessayer ne changera rien tant que
    l'environnement n'est pas corrigé, ce qui appelle un message et non un 503.

    Le message doit nommer **ce qui manque et où le poser**, la frontière CLI
    l'affichant tel quel à l'utilisateur, sans trace d'exécution
    (`CLI-ERROR-BOUNDARY-001`).
    """


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


class DatabaseUnavailableError(DatabaseError):
    """Pas de connexion utilisable : condition passagère, pas une panne.

    Deux situations, de même nature du point de vue de l'appelant.

    **Le pool est saturé.** Le backend ne peut fournir aucune connexion dans le
    délai imparti, toutes étant occupées. La demande n'a rien d'invalide et
    l'application n'a aucun défaut : elle est simplement arrivée pendant une
    pointe.

    **La connexion était morte.** Le serveur l'avait fermée de son côté
    (``wait_timeout``, redémarrage, bascule) et le pilote l'a remise en
    circulation sans le savoir. L'emprunt suivant réussira, le pilote
    rétablissant la connexion.

    Dans les deux cas la requête n'a rien de fautif et réessayer suffit, ce qui
    appelle une réponse HTTP ``503 Service Unavailable`` avec ``Retry-After``,
    jamais un ``500``. Un 500 annonce un bug du serveur et envoie chercher une
    erreur dans le code, là où le remède est d'élargir le pool
    (``DB_POOL_SIZE``), de raccourcir les requêtes, ou simplement d'attendre
    que le serveur ait fini de redémarrer.

    Forge ne rejoue **pas** la requête à la place de l'appelant : réémettre en
    silence une écriture dont on ignore si le serveur l'a reçue serait la magie
    que le principe 3 refuse. Le réessai appartient au client HTTP, que
    ``Retry-After`` renseigne.

    Le cœur la traduit en 503 dans `core.app.application`. Une application
    peut aussi l'attraper pour dégrader un écran plutôt que le refuser :

        from core.database.errors import DatabaseUnavailableError

        try:
            lignes = derniers_articles()
        except DatabaseUnavailableError:
            lignes = []      # la page s'affiche sans sa liste

    Ce que cette erreur ne dit **pas** : combien de temps attendre, ni laquelle
    des deux situations s'est produite. Seul le fait qu'aucune connexion
    utilisable n'a pu servir la requête est établi.
    """
