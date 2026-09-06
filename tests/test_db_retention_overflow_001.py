"""DB-RETENTION-OVERFLOW-001 : une rétention absurde ne sort plus en trace.

`core/database/retention.py` promet dans sa docstring que « les erreurs sont
des `ValueError` », et les trois opt-ins qui l'emploient enveloppent ce type
dans le leur pour ne pas rompre leur API publique.

`timedelta` ne lève pas une `ValueError` mais une `OverflowError`, qui n'en est
pas une sous-classe. Elle traversait donc les trois enveloppes, et le contrôle
de rétention de la commande la laissait passer : `forge audit:gc --days
99999999999` sortait en trace Python nue, là où `--days 0`, `--days -5` et
`--days abc` étaient proprement refusés.

Une commande n'a pas à montrer de trace pour une faute de frappe, et les trois
purges partagent la même cause : elle est retirée dans le cœur, une fois.
"""
from __future__ import annotations

import pytest

from core.database.retention import cutoff_for_days

#: Au delà de ce que `timedelta` sait porter, mais qu'un doigt peut taper.
TROP_GRAND = [10**9, 10**11, 99999999999, 2**63]


class TestLeCoeur:

    @pytest.mark.parametrize("jours", TROP_GRAND)
    def test_une_retention_hors_bornes_leve_une_valueerror(self, jours: int) -> None:
        """Et non une OverflowError, que les enveloppes ne rattrapent pas."""
        with pytest.raises(ValueError):
            cutoff_for_days(jours)

    @pytest.mark.parametrize("jours", TROP_GRAND)
    def test_ce_n_est_pas_une_overflowerror_nue(self, jours: int) -> None:
        try:
            cutoff_for_days(jours)
        except ValueError:
            pass
        except OverflowError:  # pragma: no cover — c'est le défaut corrigé
            pytest.fail("OverflowError nue : les enveloppes des opt-ins la laissent passer")

    def test_le_message_dit_pourquoi_c_est_sans_effet(self) -> None:
        """Refuser sans expliquer ferait chercher une limite inventée par Forge."""
        with pytest.raises(ValueError, match="trop grand"):
            cutoff_for_days(10**9)

    @pytest.mark.parametrize("jours", [1, 30, 365, 3650, 36500])
    def test_les_retentions_plausibles_passent(self, jours: int) -> None:
        """Une garde qui refuse un usage réel finit désactivée : cent ans passent."""
        assert cutoff_for_days(jours)


class TestLesTroisCommandes:
    """La cause est unique, les portes sont trois : chacune est vérifiée."""

    @staticmethod
    def _resolveur(module: str):
        import importlib

        return importlib.import_module(module).resolve_keep_days

    @pytest.mark.parametrize("module", [
        "forge_mvc_audit.cli.gc",
        "forge_mvc_stats.cli.gc",
        "forge_mvc_iot.cli.gc",
    ])
    def test_la_commande_refuse_sans_lever(self, module: str) -> None:
        """`resolve_keep_days` rend un message, jamais une exception.

        C'est son contrat : l'appelant décide seul du code de sortie et du flux.
        """
        pytest.importorskip(module.split(".")[0])

        resultat = self._resolveur(module)(["--days", "99999999999"], {})

        assert isinstance(resultat, str), "une rétention absurde doit rendre un message"
        assert "trop grand" in resultat

    @pytest.mark.parametrize("module", [
        "forge_mvc_audit.cli.gc",
        "forge_mvc_stats.cli.gc",
        "forge_mvc_iot.cli.gc",
    ])
    def test_une_retention_plausible_reste_acceptee(self, module: str) -> None:
        pytest.importorskip(module.split(".")[0])

        assert self._resolveur(module)(["--days", "90"], {}) == 90

    @pytest.mark.parametrize("module", [
        "forge_mvc_audit.cli.gc",
        "forge_mvc_stats.cli.gc",
        "forge_mvc_iot.cli.gc",
    ])
    @pytest.mark.parametrize("mauvais", ["0", "-5", "abc", ""])
    def test_les_refus_deja_en_place_le_restent(
        self, module: str, mauvais: str
    ) -> None:
        """Ajouter un refus ne doit pas en perdre un autre au passage."""
        pytest.importorskip(module.split(".")[0])

        assert isinstance(self._resolveur(module)(["--days", mauvais], {}), str)
