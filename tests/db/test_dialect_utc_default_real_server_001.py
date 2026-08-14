"""Les horodatages par défaut sont en UTC sur les quatre backends (DIALECT-UTC-DEFAULT-001).

Neuf colonnes réparties dans sept opt-ins laissent le **moteur** poser leur
horodatage, via `Column(..., default_now=True)`. Le dialecte rendait alors une
expression qui n'était pas la même partout :

    MariaDB      DEFAULT CURRENT_TIMESTAMP    heure LOCALE du serveur
    PostgreSQL   DEFAULT CURRENT_TIMESTAMP    heure LOCALE du serveur
    SQLite       DEFAULT CURRENT_TIMESTAMP    UTC
    SQL Server   DEFAULT SYSUTCDATETIME()     UTC

SQL Server employait déjà la forme UTC, ce qui montre que l'intention l'était
dès l'origine : les deux autres n'avaient simplement jamais été convertis. Une
même base portait donc deux référentiels selon le backend, et la rétention
d'audit comparait une borne calculée en UTC par Python à des valeurs locales.

Le contrôle porte sur l'**effet**, pas sur la chaîne rendue : c'est une
expression SQL, et seul le serveur dit ce qu'elle vaut.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest

from core.database.table_ddl import Column, TableDefinition
from forge_mvc_testing.real_db import tables_temporaires

pytestmark = pytest.mark.db

#: Deux minutes : large pour l'horloge d'un conteneur, mille fois trop étroit
#: pour laisser passer un décalage de fuseau, qui vaut au moins une heure.
_TOLERANCE_SECONDES = 120

TABLE = TableDefinition(
    name="sonde_defaut",
    columns=[Column("quand", "datetime", default_now=True)],
    primary_key=[],
)

#: Insérer une ligne SANS valeur : chaque moteur a sa forme.
_INSERTION_VIDE = {
    "mariadb": "INSERT INTO sonde_defaut () VALUES ()",
    "postgres": "INSERT INTO sonde_defaut (quand) VALUES (DEFAULT)",
    "mssql": "INSERT INTO sonde_defaut DEFAULT VALUES",
    "sqlite": "INSERT INTO sonde_defaut DEFAULT VALUES",
}


def _nom_du_backend() -> str:
    from core.database.backend import get_backend

    return get_backend().name


def test_le_defaut_du_moteur_est_en_utc(real_backend_db: str) -> None:
    """LE test : c'est le serveur qui pose la valeur, lui seul peut la démentir."""
    with tables_temporaires(TABLE) as base:
        base.execute(_INSERTION_VIDE[_nom_du_backend()])

        ligne = base.fetch_one('SELECT quand AS "quand" FROM sonde_defaut', ())
        assert ligne is not None
        valeur: Any = ligne["quand"]
        if isinstance(valeur, str):
            valeur = datetime.fromisoformat(valeur)
        ecart = abs(
            (valeur - datetime.now(timezone.utc).replace(tzinfo=None)).total_seconds()
        )

    assert ecart < _TOLERANCE_SECONDES, (
        f"le défaut du moteur s'écarte de {ecart:.0f} s de l'UTC : la base porte "
        "un second référentiel horaire, et toute comparaison avec une valeur "
        "écrite par Python dérive d'autant"
    )


def test_le_defaut_et_la_valeur_de_python_se_rejoignent(real_backend_db: str) -> None:
    """Les deux écrivains d'une base doivent parler du même instant.

    Sans ce contrôle, un dialecte pourrait rendre une expression stable mais
    décalée, et le test précédent seul ne le dirait pas si l'horloge de
    référence dérivait avec elle.
    """
    from core.database.timestamps import utc_now

    table = TableDefinition(
        name="sonde_deux_ecrivains",
        columns=[
            Column("par_le_moteur", "datetime", default_now=True),
            Column("par_python", "datetime"),
        ],
        primary_key=[],
    )
    with tables_temporaires(table) as base:
        base.execute(
            "INSERT INTO sonde_deux_ecrivains (par_python) VALUES (?)", (utc_now(),)
        )
        ligne = base.fetch_one(
            'SELECT par_le_moteur AS "m", par_python AS "p" FROM sonde_deux_ecrivains', ()
        )
        assert ligne is not None
        moteur, python = ligne["m"], ligne["p"]
        if isinstance(moteur, str):
            moteur = datetime.fromisoformat(moteur)
        if isinstance(python, str):
            python = datetime.fromisoformat(python)
        ecart = abs((moteur - python).total_seconds())

    assert ecart < _TOLERANCE_SECONDES, (
        f"le moteur et Python écrivent à {ecart:.0f} s d'écart dans la même "
        "ligne : les colonnes d'une même table ne sont pas comparables"
    )


def test_mariadb_n_accepte_pas_un_on_update_en_utc(real_db: str) -> None:
    """La limite qui a décidé du correctif, consignée pour qu'on ne la retente pas.

    MariaDB refuse `ON UPDATE UTC_TIMESTAMP()` et n'accepte que
    `CURRENT_TIMESTAMP` dans cette clause. Tenir l'`ON UPDATE` aurait donc mis
    le défaut en UTC et la mise à jour en heure locale : **deux référentiels
    dans une seule colonne**, pire que le défaut d'origine.

    C'est pourquoi `on_update_now` a été retiré de `forge-mvc-settings` et la
    colonne confiée à Python (ADR-081).

    La fixture est `real_db`, propre à MariaDB, et non la fixture paramétrée :
    sauter sur les autres backends aurait produit deux sauts, et un saut n'est
    pas un succès. Un test qui ne concerne qu'un moteur demande ce moteur.
    """
    from core.database import db

    with pytest.raises(Exception) as refus:
        db.execute(
            "CREATE TABLE sonde_on_update ("
            "q DATETIME DEFAULT UTC_TIMESTAMP() ON UPDATE UTC_TIMESTAMP())"
        )

    assert "UTC_TIMESTAMP" in str(refus.value) or "syntax" in str(refus.value).lower(), (
        f"MariaDB accepte désormais un ON UPDATE en UTC : {refus.value}. "
        "Le correctif peut être revu, et ce test avec lui."
    )


def test_updated_at_des_settings_suit_la_modification(real_backend_db: str) -> None:
    """`updated_at` annonçait la date de CRÉATION sur deux backends sur trois.

    Mesuré avant correctif :

        mariadb    SUIT   grâce à son `ON UPDATE` déclaratif, mais en heure locale
        postgres   FIGÉ   jamais mis à jour
        mssql      FIGÉ   jamais mis à jour

    PostgreSQL et SQL Server n'ont pas d'`ON UPDATE` déclaratif, et le store
    n'écrivait pas la colonne. Un paramètre modifié y annonçait donc, à jamais,
    la date à laquelle il avait été créé : la colonne disait le contraire de son
    nom (`SETTINGS-UPDATED-AT-001`).

    Un commentaire du contrat de table affirmait pourtant que « l'application
    pose la date, comme le store le fait déjà ». Le store ne l'écrivait pas.
    """
    pytest.importorskip("forge_mvc_settings")

    import time

    from forge_mvc_settings.store import set_setting
    from forge_mvc_settings.tables import APP_SETTINGS

    with tables_temporaires(APP_SETTINGS) as base:
        set_setting("cle", "avant", db=base)
        premier = base.fetch_one('SELECT updated_at AS "u" FROM app_settings', ())
        assert premier is not None

        # Une seconde pleine : la colonne est un DATETIME, pas toujours
        # fractionnaire selon le moteur.
        time.sleep(1.1)
        set_setting("cle", "apres", db=base)
        second = base.fetch_one('SELECT updated_at AS "u" FROM app_settings', ())
        assert second is not None

    assert str(premier["u"]) != str(second["u"]), (
        f"`updated_at` n'a pas bougé après modification ({premier['u']}) : la "
        "colonne porte la date de création et ment sur ce qu'elle nomme"
    )
