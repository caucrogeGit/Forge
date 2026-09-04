"""`JOBS-HEARTBEAT-REACHABLE-001` — une tâche longue peut prolonger son bail.

`heartbeat(claim_token)` prolonge le bail d'une tâche en cours, pour qu'une
tâche longue ne soit pas reprise par `jobs:reclaim` alors qu'elle travaille
encore. Elle se garde par le jeton de réservation, et c'est juste : sans cette
garde, n'importe qui retiendrait une tâche qu'il ne traite pas.

Le worker appelait `handler(payload)`. Un gestionnaire n'avait donc **aucun
moyen** d'obtenir ce jeton, et `heartbeat` était inutilisable depuis le seul
endroit où elle sert.

## L'exemple documenté cassait la tâche

La référence montrait, et montre toujours :

    def transcoder(payload, *, claim_token):
        for etape in etapes:
            traiter(etape)
            heartbeat(claim_token)

Mesuré, un gestionnaire écrit ainsi levait `TypeError`, repartait en réessai au
bout de dix secondes, puis finissait `failed`. L'exemple ne se contentait pas
d'être inopérant : il cassait la tâche, et le motif inscrit dans `last_error`
parlait d'un argument manquant plutôt que du travail.

## Le gestionnaire demande ce qu'il reçoit

Ce n'est pas de la magie cachée : celui qui ne déclare rien continue de recevoir
la seule charge utile, et aucun projet existant n'a de geste à faire.
"""
from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("forge_mvc_jobs")

from forge_mvc_jobs.queue import _veut_le_jeton, process_one  # noqa: E402


class _File:
    """Une tâche à prendre, et le relevé de ce que le worker écrit."""

    def __init__(self) -> None:
        self.ecritures: "list[str]" = []

    def fetch_one(self, sql: str, params: Any) -> "dict[str, Any] | None":
        if sql.startswith("SELECT id FROM"):
            return {"id": 1}
        return {"id": 1, "task": "t", "payload": '{"chemin": "a.mp4"}',
                "attempts": 1, "max_attempts": 3}

    def execute(self, sql: str, params: Any) -> int:
        self.ecritures.append(sql)
        return 1

    @property
    def traitee(self) -> bool:
        return any("status='done'" in sql for sql in self.ecritures)

    @property
    def remise_en_file(self) -> bool:
        """Le réessai écrit `SET status='pending'`.

        Chercher `status='pending'` n'importe où viserait aussi la réservation,
        dont la clause `WHERE` porte la même égalité : deux ouvriers ne peuvent
        pas réserver la même ligne.
        """
        return any("SET status='pending'" in sql for sql in self.ecritures)


def _jouer(gestionnaire: Any) -> _File:
    file = _File()
    process_one({"t": gestionnaire}, db=file)
    return file


# ─────────────────────────────────────────────────────────────────────────────
# Le gestionnaire documenté fonctionne
# ─────────────────────────────────────────────────────────────────────────────


class TestGestionnaireQuiDemandeLeJeton:

    def test_il_recoit_le_jeton(self) -> None:
        """Le cas qui échouait, et qui motive le ticket."""
        vus: "list[Any]" = []

        def transcoder(payload: Any, *, claim_token: str) -> None:
            vus.append(claim_token)

        _jouer(transcoder)

        assert len(vus) == 1
        assert isinstance(vus[0], str) and len(vus[0]) == 32

    def test_la_tache_est_traitee(self) -> None:
        def transcoder(payload: Any, *, claim_token: str) -> None:
            return None

        file = _jouer(transcoder)

        assert file.traitee
        assert not file.remise_en_file

    def test_il_recoit_aussi_la_charge_utile(self) -> None:
        vus: "list[Any]" = []

        def transcoder(payload: Any, *, claim_token: str) -> None:
            vus.append(payload)

        _jouer(transcoder)

        assert vus == [{"chemin": "a.mp4"}]

    def test_le_jeton_est_celui_de_la_reservation(self) -> None:
        """Un autre jeton ne prolongerait rien : la requête de `heartbeat` est
        gardée par `claim_token`."""
        vus: "list[str]" = []

        def transcoder(payload: Any, *, claim_token: str) -> None:
            vus.append(claim_token)

        file = _File()
        process_one({"t": transcoder}, db=file)
        reservation = next(sql for sql in file.ecritures if "claim_token=?" in sql)

        assert "status='running'" in reservation


# ─────────────────────────────────────────────────────────────────────────────
# Rien ne change pour les autres
# ─────────────────────────────────────────────────────────────────────────────


class TestAucuneRupture:

    def test_un_gestionnaire_ordinaire_est_inchange(self) -> None:
        """Aucun projet existant n'a de geste à faire."""
        vus: "list[Any]" = []
        file = _jouer(lambda payload: vus.append(payload))

        assert vus == [{"chemin": "a.mp4"}]
        assert file.traitee

    def test_un_gestionnaire_a_kwargs_recoit_le_jeton(self) -> None:
        """`**kw` accepte tout : le lui refuser demanderait de deviner ce qu'il
        en fait."""
        vus: "list[Any]" = []
        _jouer(lambda payload, **kw: vus.append(kw))

        assert "claim_token" in vus[0]

    def test_une_erreur_du_gestionnaire_reste_un_reessai(self) -> None:
        """Le chemin d'échec ne doit pas changer de nature."""
        def casse(payload: Any, *, claim_token: str) -> None:
            raise RuntimeError("transcodage impossible")

        file = _jouer(casse)

        assert file.remise_en_file
        assert not file.traitee


# ─────────────────────────────────────────────────────────────────────────────
# La détection
# ─────────────────────────────────────────────────────────────────────────────


class TestDetection:

    @pytest.mark.parametrize(
        "gestionnaire",
        [
            lambda payload, *, claim_token: None,
            lambda payload, claim_token=None: None,
            lambda payload, **kw: None,
        ],
        ids=["mot-cle-seul", "avec-defaut", "kwargs"],
    )
    def test_une_declaration_est_vue(self, gestionnaire: Any) -> None:
        assert _veut_le_jeton(gestionnaire)

    @pytest.mark.parametrize(
        "gestionnaire",
        [lambda payload: None, lambda payload, *args: None],
        ids=["charge-seule", "varargs"],
    )
    def test_une_absence_de_declaration_est_vue(self, gestionnaire: Any) -> None:
        assert not _veut_le_jeton(gestionnaire)

    def test_un_appelable_opaque_ne_recoit_rien(self) -> None:
        """Deviner ferait échouer un gestionnaire qui marchait."""
        assert not _veut_le_jeton(len)  # type: ignore[arg-type]


# ─────────────────────────────────────────────────────────────────────────────
# La documentation et le code disent la même chose
# ─────────────────────────────────────────────────────────────────────────────


class TestDocEtCodeAccordes:

    def test_l_exemple_de_la_reference_est_jouable(self) -> None:
        """C'est l'écart entre les deux qui a fait le défaut : la doc montrait
        une signature que le worker n'appelait pas."""
        from pathlib import Path

        reference = (Path(__file__).resolve().parents[1] / "docs" / "reference.md")
        texte = reference.read_text(encoding="utf-8")

        assert "def transcoder(payload, *, claim_token):" in texte, (
            "l'exemple documenté a changé de forme : vérifier que le worker "
            "sait toujours l'appeler")

        def transcoder(payload: Any, *, claim_token: str) -> None:
            return None

        assert _jouer(transcoder).traitee
