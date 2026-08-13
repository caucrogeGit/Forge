"""La chaîne de permission RBAC traverse les trois moteurs (RBAC-PERMISSION-CHAIN-REAL-001).

`forge-mvc-rbac` porte quinze fonctions touchant la base, et **aucune n'était
exercée contre un serveur réel** avant ce fichier. C'est l'opt-in qui décide si
un utilisateur a le droit de faire quelque chose : la question « ce SQL rend-il
la bonne réponse sur PostgreSQL » n'avait jamais été posée.

Le relevé est rassurant, et il faut le dire : les trois requêtes rendent le même
résultat sur MariaDB, PostgreSQL et SQL Server. Elles étaient écrites avec les
précautions qui comptent, colonnes en minuscules et alias explicites
(`p.code AS code`), là où d'autres paquets ont payé leur absence.

Ce fichier existe donc pour que cela **reste** vrai, la propriété n'ayant jusqu'ici
jamais été vérifiée ailleurs qu'en mémoire.

La chaîne complète est exercée : `user_roles` vers `roles`, puis
`role_permissions` vers `permissions`, soit trois jointures et un `DISTINCT`.
"""
from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("forge_mvc_rbac")

from forge_mvc_rbac.resolver import (
    get_user_permissions,
    get_user_role_ids,
    get_user_role_slugs,
)

from core.database.table_ddl import Column, TableDefinition
from core.database.timestamps import utc_now
from forge_mvc_testing.real_db import tables_temporaires

#: `user_roles` appartient au socle d'authentification, pas à l'opt-in : elle
#: est redéclarée ici pour que le test tienne sans dépendre de l'ordre
#: d'exécution d'un autre fichier.
USER_ROLES = TableDefinition(
    name="user_roles",
    columns=[
        Column("user_id", "integer"),
        Column("role_id", "integer"),
        Column("created_at", "datetime"),
    ],
    primary_key=["user_id", "role_id"],
)

_UTILISATEUR = 7


@pytest.fixture
def chaine(real_backend_db: str):
    """Un utilisateur, un rôle, une permission, et les liens entre eux."""
    from forge_mvc_rbac.tables import PERMISSIONS, ROLE_PERMISSIONS, ROLES

    # Ordre de création : parents d'abord, les clés étrangères en dépendent.
    with tables_temporaires(PERMISSIONS, ROLES, ROLE_PERMISSIONS, USER_ROLES) as db:
        maintenant = utc_now()
        db.execute(
            "INSERT INTO roles (name, slug, created_at) VALUES (?, ?, ?)",
            ("Administrateur", "admin", maintenant),
        )
        db.execute(
            "INSERT INTO permissions (code, label, created_at) VALUES (?, ?, ?)",
            ("article.edit", "Modifier un article", maintenant),
        )
        db.execute(
            "INSERT INTO permissions (code, label, created_at) VALUES (?, ?, ?)",
            ("article.delete", "Supprimer un article", maintenant),
        )
        db.execute("INSERT INTO role_permissions (role_id, permission_id) VALUES (1, 1)")
        db.execute("INSERT INTO role_permissions (role_id, permission_id) VALUES (1, 2)")
        db.execute(
            "INSERT INTO user_roles (user_id, role_id, created_at) VALUES (?, ?, ?)",
            (_UTILISATEUR, 1, maintenant),
        )
        yield db


def _fetch_all(db: Any):
    return lambda sql, params: db.fetch_all(sql, tuple(params))


def test_les_roles_d_un_utilisateur(chaine: Any) -> None:
    assert list(get_user_role_ids(_UTILISATEUR, fetch_all=_fetch_all(chaine))) == [1]


def test_les_slugs_passent_par_une_jointure(chaine: Any) -> None:
    """`roles` est jointe, et son alias `r.slug AS slug` doit survivre au moteur.

    C'est l'alias explicite qui protège du repli de casse de PostgreSQL, celui
    qui a vidé les tableaux du CRUD engendré (`CRUD-PG-COLUMN-CASE-001`).
    """
    assert list(get_user_role_slugs(_UTILISATEUR, fetch_all=_fetch_all(chaine))) == ["admin"]


def test_les_permissions_traversent_trois_jointures(chaine: Any) -> None:
    """Le chemin complet, avec `DISTINCT` et tri, sur lequel repose l'autorisation."""
    permissions = list(get_user_permissions(_UTILISATEUR, fetch_all=_fetch_all(chaine)))

    assert permissions == ["article.delete", "article.edit"]


def test_un_utilisateur_sans_role_n_a_aucune_permission(chaine: Any) -> None:
    """Le cas qui compte pour la sécurité : l'absence de droit doit être vide.

    Un défaut de jointure rendrait ici la liste complète des permissions plutôt
    qu'une liste vide, et personne ne le verrait avant l'incident.
    """
    inconnu = 999

    assert list(get_user_role_ids(inconnu, fetch_all=_fetch_all(chaine))) == []
    assert list(get_user_permissions(inconnu, fetch_all=_fetch_all(chaine))) == []
