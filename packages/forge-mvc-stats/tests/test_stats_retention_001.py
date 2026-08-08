"""STATS-RETENTION-001 : la table d'événements gagne une politique de rétention.

`forge_stats_events` reçoit une ligne par événement suivi et rien ne la bornait.
Une application qui trace consciencieusement y accumule des millions de lignes,
et les agrégats ralentissent d'autant sans que rien ne prévienne.

Ces tests n'ouvrent aucune connexion, conformément à la convention du paquet :
`forge-mvc-stats` n'accède jamais à la base de lui-même, l'appelant injecte
l'exécuteur. C'est ce qui les rend possibles sans serveur, et c'est aussi ce que
la commande `stats:gc` respecte en fournissant `core.database.db`.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest

pytest.importorskip("forge_mvc_stats")

from forge_mvc_stats.cli.gc import ENV_KEEP_DAYS, resolve_keep_days
from forge_mvc_stats.retention import (
    StatsRetentionError,
    count_stats_events_before,
    cutoff_for_days,
    get_stats_purge_sql,
    purge_stats_events_before,
)

_MAINTENANT = datetime(2026, 8, 8, 12, 0, 0, tzinfo=timezone.utc)


class _ExecuteurEspion:
    """Capture le SQL et les paramètres reçus, sans base."""

    def __init__(self, rendu: Any = 3) -> None:
        self.appels: list[tuple[str, tuple[Any, ...]]] = []
        self._rendu = rendu

    def __call__(self, sql: str, params: tuple[Any, ...]) -> Any:
        self.appels.append((sql, params))
        return self._rendu


def test_la_borne_recule_du_nombre_de_jours_demande() -> None:
    assert cutoff_for_days(365, now=_MAINTENANT) == "2025-08-08 12:00:00"
    assert cutoff_for_days(1, now=_MAINTENANT) == "2026-08-07 12:00:00"


@pytest.mark.parametrize("jours", [0, -1, -365])
def test_une_retention_nulle_ou_negative_est_refusee(jours: int) -> None:
    with pytest.raises(StatsRetentionError, match="viderait"):
        cutoff_for_days(jours, now=_MAINTENANT)


def test_le_sql_de_purge_n_emploie_aucune_expression_de_date() -> None:
    """La borne part en paramètre lié, ce qui rend la purge portable d'emblée.

    Une expression de date dans le SQL exigerait un rendu par dialecte, et
    l'audit `OPTIN-DML-DIALECT-001` a mesuré ce que coûte de l'oublier.
    """
    sql = get_stats_purge_sql().upper()

    assert "CREATED_AT < ?" in sql
    for interdit in ("NOW()", "CURRENT_TIMESTAMP", "DATEADD", "INTERVAL", "DATETIME("):
        assert interdit not in sql, f"expression de date dans le SQL : {interdit}"


def test_la_purge_passe_la_borne_en_parametre_lie() -> None:
    espion = _ExecuteurEspion(rendu=7)

    supprimes = purge_stats_events_before(espion, "2025-01-01 00:00:00")

    assert supprimes == 7
    sql, params = espion.appels[0]
    assert params == ("2025-01-01 00:00:00",)
    assert "?" in sql


def test_le_comptage_lit_sans_supprimer() -> None:
    """`stats:gc` affiche avant d'effacer : le comptage doit être inoffensif."""
    appels: list[tuple[str, tuple[Any, ...]]] = []

    def fetch_one(sql: str, params: tuple[Any, ...]) -> dict[str, Any]:
        appels.append((sql, params))
        return {"total": 42}

    assert count_stats_events_before(fetch_one, "2025-01-01 00:00:00") == 42
    assert "SELECT" in appels[0][0].upper()
    assert "DELETE" not in appels[0][0].upper()


def test_un_comptage_sans_ligne_rend_zero() -> None:
    assert count_stats_events_before(lambda _s, _p: None, "2025-01-01 00:00:00") == 0


@pytest.mark.parametrize("borne", ["", "   "])
def test_une_borne_vide_est_refusee(borne: str) -> None:
    with pytest.raises(StatsRetentionError):
        purge_stats_events_before(_ExecuteurEspion(), borne)


def test_la_retention_vient_de_l_option_puis_de_l_environnement() -> None:
    assert resolve_keep_days(["--days", "365"], env={}) == 365
    assert resolve_keep_days(["--days=365"], env={}) == 365
    assert resolve_keep_days([], env={ENV_KEEP_DAYS: "90"}) == 90
    assert resolve_keep_days(["--days", "7"], env={ENV_KEEP_DAYS: "90"}) == 7


def test_aucune_retention_n_est_supposee() -> None:
    """Forge ne choisit pas à la place de l'exploitant ce qu'il détruit."""
    probleme = resolve_keep_days([], env={})

    assert isinstance(probleme, str)
    assert "Aucune rétention" in probleme


@pytest.mark.parametrize("brut", ["", "trois-cent", "365j", "1.5"])
def test_une_retention_illisible_est_signalee(brut: str) -> None:
    assert isinstance(resolve_keep_days([], env={ENV_KEEP_DAYS: brut}), str)


def test_une_retention_negative_en_option_est_signalee() -> None:
    probleme = resolve_keep_days(["--days", "0"], env={})

    assert isinstance(probleme, str)
    assert "viderait" in probleme


def test_la_commande_est_declaree_avec_sa_config() -> None:
    """`stats:gc` ouvre une connexion, il lui faut l'amorçage de config (ADR-072)."""
    from forge_mvc_stats.commands import COMMANDS

    assert COMMANDS["stats:gc"]["config"] is True
    assert COMMANDS["stats:init"].get("config") is None, (
        "stats:init n'ouvre aucune connexion, il ne doit pas amorcer la config"
    )
