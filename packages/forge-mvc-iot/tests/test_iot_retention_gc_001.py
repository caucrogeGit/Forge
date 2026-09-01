"""IOT-RETENTION-GC-001 : borner la table de mesures IoT.

`iot_events` reçoit une ligne par mesure publiée et rien ne la bornait. Un
capteur qui émet toutes les dix secondes y dépose plus de trois millions de
lignes par an, et un site en compte rarement un seul : la table grossissait
jusqu'à la panne de remplissage, alors que trois autres opt-ins adossés à la
base avaient déjà leur purge.
"""
from __future__ import annotations

import importlib
from datetime import datetime, timezone

import pytest

pytest.importorskip("forge_mvc_iot")

from forge_mvc_iot.cli.gc import ENV_KEEP_DAYS, resolve_keep_days  # noqa: E402
from forge_mvc_iot.storage.retention import (  # noqa: E402
    IotRetentionError,
    cutoff_for_days,
    get_iot_count_before_sql,
    get_iot_purge_sql,
)

INSTANT = datetime(2026, 9, 1, 12, 0, 0, tzinfo=timezone.utc)
BACKENDS = ["forge_mvc_sqlite", "forge_mvc_mariadb", "forge_mvc_postgres", "forge_mvc_mssql"]


class TestBorne:
    def test_la_borne_recule_du_nombre_de_jours(self) -> None:
        assert cutoff_for_days(30, now=INSTANT) == "2026-08-02 12:00:00"

    @pytest.mark.parametrize("jours", [0, -1, -365])
    def test_une_retention_nulle_ou_negative_est_refusee(self, jours: int) -> None:
        """Elle viderait toute la table, ce qui ne peut pas être une faute de frappe."""
        with pytest.raises(IotRetentionError, match=">= 1"):
            cutoff_for_days(jours, now=INSTANT)

    @pytest.mark.parametrize("valeur", ["30", 30.0, True, None])
    def test_une_retention_qui_n_est_pas_un_entier_est_refusee(self, valeur: object) -> None:
        with pytest.raises(IotRetentionError):
            cutoff_for_days(valeur, now=INSTANT)  # type: ignore[arg-type]

    def test_le_type_d_erreur_du_paquet_est_preserve(self) -> None:
        """Le calcul vient du cœur, mais l'API du paquet ne change pas."""
        assert issubclass(IotRetentionError, ValueError)


class TestSqlPortable:
    def test_la_borne_part_en_parametre_lie(self) -> None:
        """Aucune expression de date dans la requête, sans quoi elle ne tourne que sur MariaDB."""
        for sql in (get_iot_count_before_sql(), get_iot_purge_sql()):
            assert "?" in sql
            for interdit in ("NOW(", "GETDATE(", "CURRENT_TIMESTAMP", "DATE_SUB", "INTERVAL"):
                assert interdit not in sql.upper(), f"{interdit} rend la requête non portable"

    def test_la_purge_filtre_la_colonne_indexee(self) -> None:
        """`idx_iot_events_received_at` existe déjà : aucune migration requise."""
        from forge_mvc_iot.tables import IOT_EVENTS

        assert "received_at <" in get_iot_purge_sql()
        assert any(i.column_list == "received_at" for i in IOT_EVENTS.indexes)

    def test_la_purge_vise_la_table_declaree(self) -> None:
        from forge_mvc_iot.tables import IOT_EVENTS

        assert IOT_EVENTS.name in get_iot_purge_sql()


class TestResolutionDeLaRetention:
    @pytest.mark.parametrize("argv", [["--days", "90"], ["--days=90"]])
    def test_les_deux_ecritures_de_l_option(self, argv: list[str]) -> None:
        assert resolve_keep_days(argv, env={}) == 90

    def test_l_environnement_sert_de_repli(self) -> None:
        assert resolve_keep_days([], env={ENV_KEEP_DAYS: "45"}) == 45

    def test_l_argument_l_emporte_sur_l_environnement(self) -> None:
        """Une valeur tapée dit une intention plus précise qu'une valeur héritée."""
        assert resolve_keep_days(["--days", "7"], env={ENV_KEEP_DAYS: "45"}) == 7

    @pytest.mark.parametrize(
        ("argv", "env", "extrait"),
        [
            ([], {}, "Aucune rétention"),
            (["--days"], {}, "attend un nombre"),
            (["--days", "abc"], {}, "illisible"),
            (["--days", "0"], {}, "viderait toute la table"),
            (["--days", "-5"], {}, "viderait toute la table"),
            ([], {ENV_KEEP_DAYS: "   "}, "Aucune rétention"),
        ],
    )
    def test_les_refus_sont_expliques(
        self, argv: list[str], env: dict[str, str], extrait: str
    ) -> None:
        resultat = resolve_keep_days(argv, env=env)
        assert isinstance(resultat, str)
        assert extrait in resultat


class TestConventionPartagee:
    """La commande suit la forme des trois autres purges d'opt-in."""

    def test_la_commande_est_declaree(self) -> None:
        from forge_mvc_iot.commands import COMMANDS

        assert "iot:gc" in COMMANDS
        assert COMMANDS["iot:gc"]["config"] is True, "la purge ouvre une connexion BDD"

    def test_le_nom_suit_les_autres_opt_ins(self) -> None:
        """`:gc` et non `:purge` : une seule façon de dire le geste (principe 11)."""
        from forge_mvc_iot.commands import COMMANDS

        assert "iot:purge" not in COMMANDS

    def test_le_calcul_de_borne_vient_du_coeur(self) -> None:
        """Il était déjà écrit deux fois, dans audit et stats."""
        from core.database.retention import cutoff_for_days as coeur

        assert coeur(30, now=INSTANT) == cutoff_for_days(30, now=INSTANT)


class TestAffichageAvantSuppression:
    """La commande montre l'effet avant de l'appliquer (charte §7)."""

    def _faux_db(self, compte: int, journal: list[str]):
        module = importlib.import_module("core.database.db")

        class _Db:
            @staticmethod
            def fetch_one(sql: str, params: tuple[object, ...]):
                journal.append("fetch_one")
                return {"total": compte}

            @staticmethod
            def execute(sql: str, params: tuple[object, ...]) -> int:
                journal.append("execute")
                return compte

        return module, _Db

    def test_sans_run_rien_n_est_supprime(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from forge_mvc_iot.cli import gc

        journal: list[str] = []
        module, faux = self._faux_db(12, journal)
        monkeypatch.setattr(module, "fetch_one", faux.fetch_one)
        monkeypatch.setattr(module, "execute", faux.execute)

        assert gc.main(["--days", "90"]) == 0
        assert journal == ["fetch_one"], "aucune suppression sans --run"

    def test_avec_run_la_suppression_part(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from forge_mvc_iot.cli import gc

        journal: list[str] = []
        module, faux = self._faux_db(12, journal)
        monkeypatch.setattr(module, "fetch_one", faux.fetch_one)
        monkeypatch.setattr(module, "execute", faux.execute)

        assert gc.main(["--days", "90", "--run"]) == 0
        assert "execute" in journal

    def test_sans_retention_la_commande_refuse(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from forge_mvc_iot.cli import gc

        monkeypatch.delenv(ENV_KEEP_DAYS, raising=False)
        assert gc.main([]) == 1
