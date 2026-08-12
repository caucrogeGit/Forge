"""Les horodatages du socle sont posés par Python (AUTH-TIMESTAMPS-EXPLICIT-001, ADR-081).

L'ADR-081 a tranché que l'autorité sur les horodatages est **Python**, jamais le
moteur SQL, et que le DDL reste `DATETIME NOT NULL` sans `DEFAULT` ni
`ON UPDATE`. Il l'a fait après avoir **examiné et refusé** les défauts SQL,
proposés par le retour terrain, au motif qu'ils introduisent une double horloge.

Les entités engendrées suivent cette règle. Les sept tables du socle
d'authentification, non : elles sont les seules de Forge à s'en écarter, et
c'est là que la double horloge coûte le plus, `users` étant la seule table que
toute application Forge possède.

## L'ordre, qui est tout le ticket

Aucune écriture ne nommait ces colonnes. Retirer les `DEFAULT` d'abord aurait
donc rendu `NOT NULL` sans valeur, et **plus aucun compte n'aurait pu être
créé**, ni par l'application, ni par la CLI, ni par les fixtures.

Cette livraison rend donc les écritures explicites, et **ne retire rien**. Le
retrait des défauts vient ensuite, quand plus personne ne s'appuie dessus.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any

import pytest

pytestmark = pytest.mark.meta


def _sqlite_avec(table: str, *, sans_defauts: bool = True) -> sqlite3.Connection:
    """Base en mémoire portant une table du socle, DDL rendue par le dialecte.

    La DDL est **conforme à l'ADR-081 depuis `AUTH-TIMESTAMPS-REMOVE-DEFAULTS-001`**,
    donc `NOT NULL` sans défaut : une insertion qui ne nomme pas ses
    horodatages échoue, ce qui est exactement la propriété recherchée.

    Le paramètre est conservé pour mémoire. Tant que le moteur remplissait la
    colonne, une assertion « created_at non vide » passait aussi sur du code
    qui ne l'écrivait pas, ce qui a été vérifié en rejouant les insertions
    d'avant : le test ne prouvait rien.
    """
    from cli.security.auth_sql import render_auth_sql
    from forge_mvc_sqlite.dialect import SQLiteDialect

    ddl = render_auth_sql(table, SQLiteDialect())
    assert "DEFAULT CURRENT_TIMESTAMP" not in ddl, (
        "la DDL du socle porte de nouveau un défaut SQL : l'autorité repasse "
        "au moteur, contre l'ADR-081"
    )
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    for instruction in ddl.split(";"):
        if instruction.strip():
            conn.execute(instruction)
    conn.commit()
    return conn


def test_la_cli_pose_elle_meme_les_horodatages_d_un_compte() -> None:
    """LE test du ticket : sans lui, la CLI dépendrait du défaut SQL sans le savoir.

    Il échoue sur le code d'avant, dont l'INSERT ne nommait pas ces colonnes.
    """
    from cli.security.auth import create_auth_user

    conn = _sqlite_avec("users", sans_defauts=True)
    try:
        def fetch_one(sql: str, params: Any) -> "dict[str, Any] | None":
            row = conn.execute(sql, tuple(params)).fetchone()
            return dict(row) if row else None

        def insert(sql: str, params: Any) -> int:
            cur = conn.execute(sql, tuple(params))
            conn.commit()
            return int(cur.lastrowid or 0)

        create_auth_user(
            login="2TNE1-01", password="secret123", fetch_one=fetch_one, insert=insert
        )

        ligne = conn.execute("SELECT created_at, updated_at FROM users").fetchone()
        assert ligne is not None
        assert ligne["created_at"], "created_at doit être posé par Python, pas par le moteur"
        assert ligne["updated_at"]
        assert ligne["created_at"] == ligne["updated_at"], (
            "à la création, les deux horodatages sont le même instant"
        )
    finally:
        conn.close()


def test_l_insertion_nomme_les_colonnes_d_horodatage() -> None:
    """Le contrôle direct : la requête doit nommer `created_at` et `updated_at`.

    C'est ce qui distingue une valeur posée par Python d'une valeur posée par
    le moteur. Sans lui, le défaut SQL remplit la colonne et toute assertion
    sur son contenu passe des deux côtés.
    """
    from cli.security.auth import create_auth_user

    vues: "list[str]" = []

    def insert(sql: str, params: Any) -> int:
        vues.append(sql)
        return 1

    create_auth_user(
        login="admin", password="secret123", fetch_one=lambda *_: None, insert=insert
    )

    assert len(vues) == 1
    sql = vues[0]
    assert "created_at" in sql, "l'INSERT ne nomme pas created_at : le moteur décide"
    assert "updated_at" in sql, "l'INSERT ne nomme pas updated_at : le moteur décide"


def test_la_valeur_posee_est_un_datetime_python() -> None:
    """Un `datetime` Python, pas une chaîne ni une expression SQL."""
    from cli.security.auth import create_auth_user

    vues: "list[Any]" = []

    def insert(sql: str, params: Any) -> int:
        vues.extend(params)
        return 1

    avant = datetime.now(timezone.utc)
    create_auth_user(
        login="admin", password="secret123", fetch_one=lambda *_: None, insert=insert
    )

    horodatages = [v for v in vues if isinstance(v, datetime)]
    assert len(horodatages) == 2, "created_at et updated_at doivent être passés en paramètres"
    assert all(h >= avant for h in horodatages)


def test_l_attribution_de_role_pose_aussi_son_horodatage() -> None:
    """`user_roles` est la seconde et dernière écriture du framework dans le socle."""
    from cli.security.auth import add_auth_user_role

    conn = _sqlite_avec("user_roles", sans_defauts=True)
    try:
        vues: "list[tuple[str, Any]]" = []

        def fetch_one(sql: str, params: Any) -> "dict[str, Any] | None":
            # Le rôle existe, l'attribution n'existe pas encore : sans cette
            # seconde branche, la fonction sort avant d'insérer.
            if "FROM user_roles" in sql:
                return None
            return {"id": 3}

        def execute(sql: str, params: Any) -> int:
            vues.append((sql, params))
            conn.execute(sql, tuple(params))
            conn.commit()
            return 1

        add_auth_user_role(user_id=7, role="admin", fetch_one=fetch_one, execute=execute)

        ligne = conn.execute("SELECT created_at FROM user_roles").fetchone()
        assert ligne is not None
        assert ligne["created_at"], "created_at doit être posé par Python"
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# L'inventaire pour la seconde livraison
# ---------------------------------------------------------------------------

#: **Vide depuis `AUTH-TIMESTAMPS-REMOVE-DEFAULTS-001`.** Les sept tables du
#: socle déléguaient leur horodatage au moteur, quatre portant aussi
#: `ON UPDATE CURRENT_TIMESTAMP`. Le relevé initial ne nommait que `users`.
#:
#: La liste est conservée vide plutôt que supprimée : elle documente le
#: mécanisme et fait échouer le cliquet si un défaut réapparaît.
_DEFAUTS_A_RETIRER: "dict[str, tuple[list[str], list[str]]]" = {}


def test_l_inventaire_des_defauts_est_exact() -> None:
    """Un cliquet sur l'écart restant, pour que la seconde livraison ait sa liste.

    Il échoue dans les deux sens : si un défaut est retiré sans mettre la liste
    à jour, et si un défaut apparaît sur une table qui n'y figure pas.
    """
    from cli.security.auth_sql import AUTH_TABLE_SPECS

    reel: "dict[str, tuple[list[str], list[str]]]" = {}
    for nom, spec in AUTH_TABLE_SPECS.items():
        defauts = [c.name for c in spec.columns if getattr(c, "timestamp_default", False)]
        on_update = [c.name for c in spec.columns if getattr(c, "timestamp_on_update", False)]
        if defauts or on_update:
            reel[nom] = (defauts, on_update)

    assert reel == _DEFAUTS_A_RETIRER, (
        "L'écart avec l'ADR-081 a changé : mettez _DEFAUTS_A_RETIRER à jour.\n"
        f"  relevé : {reel}\n  attendu : {_DEFAUTS_A_RETIRER}"
    )


def test_aucune_table_d_entite_ne_porte_de_defaut() -> None:
    """La règle de l'ADR-081 tient ailleurs, et c'est ce qui rend l'écart anormal.

    Le socle est la seule exception de Forge, et il est aussi le seul endroit
    que toute application possède.
    """
    from core.database.table_ddl import Column

    # Le socle d'entités n'expose aucun mécanisme de défaut d'horodatage : la
    # colonne du contrat commun ne porte pas ces attributs, contrairement à
    # l'`AuthColumn` du socle d'authentification.
    assert not hasattr(Column("x", "datetime"), "timestamp_default")
    assert not hasattr(Column("x", "datetime"), "timestamp_on_update")
