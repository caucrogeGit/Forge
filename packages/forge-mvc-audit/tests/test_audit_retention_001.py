"""AUDIT-RETENTION-001 : le journal d'audit gagne une politique de rétention.

`audit_log` grossissait sans borne, seule table d'opt-in adossé à la base à
n'avoir aucune purge alors que `sessions:gc` avait posé le précédent.

Ces tests ne touchent pas la base. Ils portent sur trois choses.

Le **calcul de la borne**, qui se fait en Python et part en paramètre lié, de
sorte qu'aucune expression de date n'entre dans le SQL. C'est ce qui rend la
purge portable sur les quatre backends sans effort, le piège inverse ayant été
mesuré par `OPTIN-DML-DIALECT-001`.

Le **refus d'une rétention absurde**, une valeur nulle ou négative vidant la
table entière et ne pouvant pas être le résultat d'une faute de frappe.

La **résolution de la rétention**, qui doit être dite et jamais supposée.

La preuve que la purge supprime réellement les bonnes lignes est ailleurs, elle
exige un serveur : `test_audit_db_integration_001.py`.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

pytest.importorskip("forge_mvc_audit")

from forge_mvc_audit.cli.gc import ENV_KEEP_DAYS, resolve_keep_days
from forge_mvc_audit.errors import AuditError
from forge_mvc_audit.store import cutoff_for_days


_MAINTENANT = datetime(2026, 8, 8, 12, 0, 0, tzinfo=timezone.utc)


def test_la_borne_recule_du_nombre_de_jours_demande() -> None:
    assert cutoff_for_days(90, now=_MAINTENANT) == "2026-05-10 12:00:00"
    assert cutoff_for_days(1, now=_MAINTENANT) == "2026-08-07 12:00:00"


def test_la_borne_a_le_format_des_horodatages_de_forge() -> None:
    """Même format que `forge-mvc-sessions-db`, sans quoi la comparaison dérape."""
    borne = cutoff_for_days(30, now=_MAINTENANT)

    assert datetime.strptime(borne, "%Y-%m-%d %H:%M:%S")


@pytest.mark.parametrize("jours", [0, -1, -365])
def test_une_retention_nulle_ou_negative_est_refusee(jours: int) -> None:
    """Elle viderait tout le journal : ce ne peut pas être une étourderie acceptée."""
    with pytest.raises(AuditError, match="viderait"):
        cutoff_for_days(jours, now=_MAINTENANT)


def test_une_retention_non_entiere_est_refusee() -> None:
    with pytest.raises(AuditError):
        cutoff_for_days("90", now=_MAINTENANT)  # pyright: ignore[reportArgumentType]


def test_la_retention_vient_de_l_option() -> None:
    assert resolve_keep_days(["--days", "90"], env={}) == 90
    assert resolve_keep_days(["--days=90"], env={}) == 90


def test_la_retention_vient_de_l_environnement_a_defaut() -> None:
    assert resolve_keep_days([], env={ENV_KEEP_DAYS: "180"}) == 180


def test_l_option_l_emporte_sur_l_environnement() -> None:
    """Une valeur tapée à la main dit une intention plus précise que l'héritée."""
    assert resolve_keep_days(["--days", "7"], env={ENV_KEEP_DAYS: "180"}) == 7


def test_aucune_retention_n_est_supposee() -> None:
    """Forge ne choisit pas à la place de l'exploitant ce qu'il détruit."""
    probleme = resolve_keep_days([], env={})

    assert isinstance(probleme, str)
    assert "Aucune rétention" in probleme


@pytest.mark.parametrize("brut", ["", "   ", "quatre-vingt-dix", "90j", "9.5"])
def test_une_retention_illisible_est_signalee(brut: str) -> None:
    probleme = resolve_keep_days([], env={ENV_KEEP_DAYS: brut})

    assert isinstance(probleme, str)


def test_days_sans_valeur_est_signale() -> None:
    probleme = resolve_keep_days(["--days"], env={})

    assert isinstance(probleme, str)
    assert "--days" in probleme


def test_une_retention_negative_en_option_est_signalee() -> None:
    probleme = resolve_keep_days(["--days", "0"], env={})

    assert isinstance(probleme, str)
    assert "viderait" in probleme
