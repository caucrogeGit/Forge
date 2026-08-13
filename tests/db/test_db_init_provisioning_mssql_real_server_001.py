"""Le script de provisionnement SQL Server s'exécute réellement (DB-INIT-PROVISION-MSSQL-001).

Pendant de `DB-INIT-PROVISION-REAL-001`, qui a exercé le rendu PostgreSQL.
Le rendu SQL Server avait le même statut : vérifié par comparaison de chaînes,
jamais soumis à un serveur, alors qu'il conditionne la toute première commande
d'un projet.

## Une limite à déclarer

Le script est écrit pour `sqlcmd`, dont il emploie le séparateur de lots `GO`.
`GO` n'est **pas** du T-SQL : c'est une instruction de l'outil client, que le
pilote ne connaît pas. `sqlcmd` étant absent de cette machine, les lots sont
découpés ici comme `sqlcmd` les découpe, puis soumis un à un par le pilote.

C'est fidèle mais ce n'est pas l'outil de l'opérateur. Ce que ce fichier prouve
est donc que **le T-SQL du script est accepté par le serveur**, pas que
`sqlcmd` interprète correctement le fichier. Le second point reste hors de
portée tant que l'outil n'est pas installé, et il vaut mieux l'écrire que de
laisser croire à une couverture complète.

Les objets créés portent des noms jetables préfixés `forge_initprobe_`, et sont
supprimés dans tous les cas.
"""
from __future__ import annotations

import os
import re
from typing import Any

import pytest

pytest.importorskip("forge_mvc_entities")

from forge_mvc_entities.db_init import ProvisioningEnv, generate_provisioning_sql_mssql

pytestmark = pytest.mark.db_mssql

_PREFIXE = "forge_initprobe"
_BASE = f"{_PREFIXE}_base"
_ADMIN = f"{_PREFIXE}_admin"
_APP = f"{_PREFIXE}_app"

#: `GO` seul sur sa ligne, casse indifférente : la règle de découpage de sqlcmd.
_SEPARATEUR_DE_LOT = re.compile(r"^\s*GO\s*$", re.IGNORECASE | re.MULTILINE)


def _lots(script: str) -> list[str]:
    """Découpe le script en lots, comme `sqlcmd` le ferait."""
    return [lot.strip() for lot in _SEPARATEUR_DE_LOT.split(script) if lot.strip()]


def _connexion() -> Any:
    """Connexion d'administration au serveur, hors transaction.

    `CREATE DATABASE` est refusé dans une transaction : l'autocommit n'est pas
    un confort ici, il est nécessaire.
    """
    import pyodbc

    hote = os.environ.get("FORGE_TEST_MSSQL_HOST", "127.0.0.1")
    port = os.environ.get("FORGE_TEST_MSSQL_PORT", "1433")
    utilisateur = os.environ.get("FORGE_TEST_MSSQL_USER", "sa")
    motdepasse = os.environ.get("FORGE_TEST_MSSQL_PASSWORD", "Forge#Test#2026")
    connexion = pyodbc.connect(
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={hote},{port};DATABASE=master;UID={utilisateur};PWD={motdepasse};"
        "TrustServerCertificate=yes;",
        autocommit=True,
        timeout=15,
    )
    return connexion


def _purger(connexion: Any) -> None:
    """Supprime base et connexions, quel que soit l'état laissé par le test.

    Le `USE [master]` d'ouverture n'est pas décoratif. Le script de
    provisioning laisse la connexion **dans** la base du projet, et une base ne
    peut pas être supprimée depuis une session qui l'occupe. La suppression
    échouait donc, silencieusement.

    Le résultat était trompeur : la base survivait, les connexions serveur non.
    L'utilisateur de base devenait orphelin, son SID pointant vers une
    connexion disparue. Le script étant idempotent, son
    `IF DATABASE_PRINCIPAL_ID(...) IS NULL` voyait l'orphelin et sautait la
    création. Deux tests plus loin, l'usurpation échouait sur un principal qui
    « n'existe pas », et rien ne renvoyait à la purge.

    D'où la règle appliquée ici : une purge ne se tait pas. Elle revient à
    `master`, et le seul échec toléré est celui d'un objet déjà absent.
    """
    curseur = connexion.cursor()
    curseur.execute("USE [master]")
    for instruction in (
        f"IF DB_ID(N'{_BASE}') IS NOT NULL BEGIN "
        f"ALTER DATABASE [{_BASE}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE; "
        f"DROP DATABASE [{_BASE}]; END",
        f"IF SUSER_ID(N'{_APP}') IS NOT NULL DROP LOGIN [{_APP}]",
        f"IF SUSER_ID(N'{_ADMIN}') IS NOT NULL DROP LOGIN [{_ADMIN}]",
    ):
        curseur.execute(instruction)

    # Contrôle, faute de quoi la purge redeviendrait une formalité.
    curseur.execute(f"SELECT DB_ID(N'{_BASE}'), SUSER_ID(N'{_APP}'), SUSER_ID(N'{_ADMIN}')")
    restes = [nom for nom, valeur in zip((_BASE, _APP, _ADMIN), curseur.fetchone()) if valeur]
    assert not restes, f"la purge a laissé des objets sur le serveur : {', '.join(restes)}"


@pytest.fixture
def terrain():
    pytest.importorskip("pyodbc", reason="pyodbc (backend forge-mvc-mssql) absent")
    connexion = _connexion()
    _purger(connexion)
    try:
        yield connexion
    finally:
        _purger(connexion)
        connexion.close()


def _migrations_ddl() -> str:
    from forge_mvc_mssql.dialect import MSSQLDialect

    return MSSQLDialect().forge_migrations_ddl()


def _config() -> ProvisioningEnv:
    return ProvisioningEnv(
        db_name=_BASE,
        admin_login=_ADMIN,
        admin_password="Sonde#Admin#2026",
        app_login=_APP,
        app_password="Sonde#App#2026",
        app_privileges=["SELECT", "INSERT", "UPDATE", "DELETE"],
        # Propres à MariaDB, ignorés par le rendu SQL Server, mais exigés par
        # le contrat commun de `ProvisioningEnv`.
        db_charset="utf8mb4",
        db_collation="utf8mb4_general_ci",
        host=os.environ.get("FORGE_TEST_MSSQL_HOST", "127.0.0.1"),
    )


def test_le_decoupage_en_lots_trouve_bien_des_separateurs() -> None:
    """Un découpage qui ne découperait rien ferait passer le test suivant.

    Le script entier serait alors soumis en une fois, `GO` compris, et le
    serveur le refuserait. Ce serait visible. Mais un découpage qui rendrait un
    seul lot **sans** `GO` passerait pour un succès, et c'est ce cas que ce
    test écarte.
    """
    script = generate_provisioning_sql_mssql(_config(), "CREATE TABLE t (id int)")

    lots = _lots(script)

    assert len(lots) >= 4, f"découpage suspect, {len(lots)} lot(s) obtenu(s)"
    assert not any("GO" == ligne.strip() for lot in lots for ligne in lot.splitlines()), (
        "un séparateur `GO` a survécu au découpage, le serveur le refusera"
    )


def test_le_script_de_provisionnement_s_execute_sans_erreur(terrain: Any) -> None:
    """LE test : le T-SQL rendu par `forge db:init` doit être accepté."""
    script = generate_provisioning_sql_mssql(_config(), _migrations_ddl())
    curseur = terrain.cursor()

    for numero, lot in enumerate(_lots(script), start=1):
        try:
            curseur.execute(lot)
        except Exception as erreur:  # noqa: BLE001 — le message importe plus que le type
            pytest.fail(f"lot {numero} refusé par SQL Server :\n{lot}\n\n{erreur}")


def test_le_script_cree_bien_ce_qu_il_annonce(terrain: Any) -> None:
    """Un script idempotent tolère les erreurs par construction.

    Son succès ne prouve donc rien sur le résultat, et c'est le résultat qui
    décide si le projet démarre.
    """
    script = generate_provisioning_sql_mssql(_config(), _migrations_ddl())
    curseur = terrain.cursor()
    for lot in _lots(script):
        curseur.execute(lot)

    curseur.execute(f"SELECT DB_ID(N'{_BASE}')")
    assert curseur.fetchone()[0] is not None, "la base du projet n'a pas été créée"

    for connexion_attendue in (_ADMIN, _APP):
        curseur.execute(f"SELECT SUSER_ID(N'{connexion_attendue}')")
        assert curseur.fetchone()[0] is not None, (
            f"la connexion serveur « {connexion_attendue} » manque"
        )


def test_le_compte_applicatif_ne_peut_pas_creer_de_table(terrain: Any) -> None:
    """La preuve par l'échec, celle qui a servi côté PostgreSQL.

    Le contrôle homologue y avait montré qu'une lecture de catalogue laissait
    passer un élargissement des droits, quand la tentative réelle le voyait.
    """
    script = generate_provisioning_sql_mssql(_config(), _migrations_ddl())
    curseur = terrain.cursor()
    for lot in _lots(script):
        curseur.execute(lot)

    curseur.execute(f"USE [{_BASE}]")
    curseur.execute(f"EXECUTE AS USER = N'{_APP}'")
    try:
        with pytest.raises(Exception) as refus:
            curseur.execute("CREATE TABLE tentative_interdite (id int)")
        assert "permission" in str(refus.value).lower() or "autoris" in str(refus.value).lower(), (
            f"refus attendu pour cause de droits, obtenu : {refus.value}"
        )
    finally:
        curseur.execute("REVERT")


def test_le_compte_applicatif_a_bien_le_dml(terrain: Any) -> None:
    """L'autre moitié : trop peu de droits bloque l'application au démarrage.

    Un provisioning qui n'accorderait rien passerait le test précédent sans
    difficulté, en refusant tout.
    """
    script = generate_provisioning_sql_mssql(_config(), _migrations_ddl())
    curseur = terrain.cursor()
    for lot in _lots(script):
        curseur.execute(lot)

    curseur.execute(f"USE [{_BASE}]")
    curseur.execute(f"EXECUTE AS USER = N'{_APP}'")
    try:
        for droit in ("SELECT", "INSERT", "UPDATE", "DELETE"):
            curseur.execute(f"SELECT HAS_PERMS_BY_NAME(N'dbo', N'SCHEMA', N'{droit}')")
            assert curseur.fetchone()[0] == 1, (
                f"le compte applicatif n'a pas {droit} sur dbo, il ne pourra pas tourner"
            )
    finally:
        curseur.execute("REVERT")
