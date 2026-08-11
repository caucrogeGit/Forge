"""Les deux chemins d'écriture de `users` s'accordent sur la casse (AUTH-CASE-ASYMMETRY-001).

Forge écrit dans la table `users` par deux chemins, et ils ne suivaient pas la
même convention.

La CLI `forge auth:user:*` abaissait la casse, à l'écriture comme à la lecture :
prise seule, elle était cohérente. Le contrôleur et le modèle engendrés par
`forge make:auth` ne normalisent rien, ils passent la saisie du formulaire
telle quelle à `WHERE login = ?`.

Deux chemins d'écriture, une seule table, deux conventions.

## Pourquoi cela ne se voyait pas

Sur MariaDB, la collation `utf8mb4_unicode_ci` compare sans égard à la casse, si
bien que l'écart n'a aucun effet observable. Sur SQLite, où `TEXT` compare en
binaire, il ferme une porte : un compte créé par la CLI, donc stocké en
minuscules, **ne peut pas se connecter** dès que l'utilisateur tape une
majuscule dans le formulaire.

Les deux moteurs sont au niveau plein depuis l'ADR-084. Le défaut a été expédié
jusqu'à la 1.0.0-rc.5 incluse.

## Ce que ce fichier vérifie

Il exerce les deux chemins contre un **vrai** SQLite, monté depuis la DDL rendue
par le dialecte, et non contre un faux objet : c'est la seule façon de voir une
comparaison binaire se comporter comme telle.

Les tests unitaires de `tests/test_auth_admin_cli.py` figent la conservation de
casse côté CLI ; celui-ci prouve que les deux chemins se rejoignent réellement
dans la base.
"""
from __future__ import annotations

import sqlite3
from typing import Any

import pytest

pytestmark = pytest.mark.meta

#: Identité mêlant capitales et minuscules. Depuis l'ADR-089, ce n'est plus
#: forcément une adresse : `2TNE1-01` illustre mieux ce que la colonne porte.
IDENTITE = "2TNE1-01"

#: Requête du modèle engendré par `make:auth`, recopiée telle quelle. La figer
#: ici rend le test aveugle à toute normalisation que le générateur
#: introduirait sans le dire.
SELECT_ENGENDRE = (
    "SELECT id, login, email, password_hash, is_active FROM users WHERE login = ?"
)


def _sqlite_avec_users() -> sqlite3.Connection:
    """Base SQLite en mémoire portant la table `users`, DDL rendue par le dialecte."""
    from cli.security.auth_sql import render_auth_sql
    from forge_mvc_sqlite.dialect import SQLiteDialect

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    for instruction in render_auth_sql("users", SQLiteDialect()).split(";"):
        if instruction.strip():
            conn.execute(instruction)
    conn.commit()
    return conn


def _creer_par_la_cli(conn: sqlite3.Connection, identite: str) -> int:
    """Crée un compte par le chemin CLI, sur la connexion donnée."""
    from cli.security.auth import create_auth_user

    def fetch_one(sql: str, params: Any) -> "dict[str, Any] | None":
        row = conn.execute(sql, tuple(params)).fetchone()
        return dict(row) if row else None

    def insert(sql: str, params: Any) -> int:
        cur = conn.execute(sql, tuple(params))
        conn.commit()
        return int(cur.lastrowid or 0)

    return create_auth_user(
        login=identite, password="secret123", fetch_one=fetch_one, insert=insert
    )


def _charger_par_le_modele_engendre(
    conn: sqlite3.Connection, identite: str
) -> "dict[str, Any] | None":
    """Lit par la requête que `make:auth` engendre, sans normalisation."""
    row = conn.execute(SELECT_ENGENDRE, (identite,)).fetchone()
    return dict(row) if row else None


def test_un_compte_cree_par_la_cli_se_connecte_par_le_formulaire() -> None:
    """LE test du ticket : sans lui, la porte reste fermée sur SQLite.

    Il échoue sur le code d'avant, la CLI ayant stocké `2tne1-01` quand le
    formulaire cherche `2TNE1-01`.
    """
    conn = _sqlite_avec_users()
    try:
        user_id = _creer_par_la_cli(conn, IDENTITE)
        trouve = _charger_par_le_modele_engendre(conn, IDENTITE)

        assert trouve is not None, (
            "le compte créé par la CLI est introuvable par la requête que "
            "make:auth engendre : les deux chemins ne s'accordent pas sur la casse"
        )
        assert trouve["id"] == user_id
        assert trouve["login"] == IDENTITE
    finally:
        conn.close()


def test_la_cli_retrouve_ce_qu_elle_a_ecrit() -> None:
    """La cohérence interne de la CLI ne doit pas être perdue en chemin.

    Elle existait avant le correctif, par les deux bouts de la normalisation.
    Elle doit tenir maintenant que la normalisation a disparu.
    """
    from cli.security.auth import show_auth_user

    conn = _sqlite_avec_users()
    try:
        user_id = _creer_par_la_cli(conn, IDENTITE)

        def fetch_one(sql: str, params: Any) -> "dict[str, Any] | None":
            row = conn.execute(sql, tuple(params)).fetchone()
            return dict(row) if row else None

        vu = show_auth_user(login=IDENTITE, fetch_one=fetch_one)

        assert vu is not None
        assert vu["id"] == user_id
        assert vu["login"] == IDENTITE
    finally:
        conn.close()


def test_la_casse_est_conservee_en_base() -> None:
    """Ce que la CLI écrit est ce que l'utilisateur a saisi.

    Abaisser la casse d'une identité la déforme. Rien dans le paquet ne vérifie
    que cette colonne contient une adresse : le cœur n'exige qu'une chaîne non
    vide (`core/auth/user.py`), et une application y met légitimement un
    identifiant de classe ou un nom de compte.
    """
    conn = _sqlite_avec_users()
    try:
        _creer_par_la_cli(conn, IDENTITE)
        stocke = conn.execute("SELECT login FROM users").fetchone()

        assert stocke is not None
        assert stocke["login"] == IDENTITE
    finally:
        conn.close()


def test_la_cli_n_abaisse_plus_la_casse() -> None:
    """Garde-fou direct sur la fonction, pour que le motif ne revienne pas.

    Une seule ligne suffisait à rouvrir le défaut, et elle portait un nom qui
    la rendait naturelle : `_normalize_email`.
    """
    import inspect

    from cli.security import auth

    source = inspect.getsource(auth._validate_login_value)

    assert ".lower()" not in source, (
        "la normalisation de casse est revenue sur l'identité : elle appartient "
        "au contact, pas à l'identifiant de connexion"
    )
    assert not hasattr(auth, "_normalize_email"), (
        "l'ancien nom est de retour : il donnait à croire que cette colonne est "
        "une adresse, ce que rien ne vérifie"
    )
