"""`JOBS-WORKER-GRACEFUL-STOP-001` — un worker s'arrête entre deux tâches.

`run_worker` acceptait `stop`, mais ne la consultait qu'entre deux **passes**,
c'est à dire une fois la file vidée. Sur une file chargée, elle était donc sans
effet.

Mesuré avant correction : un worker recevant l'ordre d'arrêt après trois tâches
en traitait cinquante avant de le remarquer.

Ce n'est pas théorique. Sous systemd, `TimeoutStopSec` vaut quatre-vingt-dix
secondes par défaut : passé ce délai le worker est tué, au milieu d'une tâche,
qui repart ensuite par `jobs:reclaim`. Un déploiement se fait justement quand la
file est pleine, et c'est le seul moment où ce défaut se voit.
"""
from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

pytest.importorskip("forge_mvc_jobs")

from forge_mvc_jobs.queue import drain, run_worker  # noqa: E402


class _File:
    """File en mémoire, qui note l'ordre d'arrêt et ce qui a été traité."""

    def __init__(self, taille: int, arret_apres: "int | None" = None) -> None:
        self.restantes = list(range(taille))
        self.traitees: list[int] = []
        self._arret_apres = arret_apres
        self.arret_demande = False

    def process_one(
        self, handlers: Any, *, queue: str = "default", db: Any = None
    ) -> bool:
        if not self.restantes:
            return False
        self.traitees.append(self.restantes.pop(0))
        if self._arret_apres is not None and len(self.traitees) == self._arret_apres:
            self.arret_demande = True
        return True

    def stop(self) -> bool:
        return self.arret_demande


class TestArretSousCharge:

    def test_le_worker_s_arrete_a_la_tache_suivante(self) -> None:
        """Le cas qui échouait, et qui motive le ticket."""
        file = _File(taille=50, arret_apres=3)

        with patch("forge_mvc_jobs.queue.process_one", file.process_one):
            run_worker({}, stop=file.stop)

        assert len(file.traitees) == 3
        assert len(file.restantes) == 47

    def test_drain_honore_l_arret(self) -> None:
        """`drain` est publique et sert aussi seule, dans un `oneshot`."""
        file = _File(taille=20, arret_apres=2)

        with patch("forge_mvc_jobs.queue.process_one", file.process_one):
            traitees = drain({}, stop=file.stop)

        assert traitees == 2

    def test_la_tache_en_cours_va_a_son_terme(self) -> None:
        """L'arrêt est consulté entre deux tâches, jamais pendant l'une d'elles.

        Interrompre une tâche en cours ne serait qu'un autre nom pour
        l'interruption brutale, et laisserait la moitié d'un envoi fait.
        """
        terminees: list[str] = []
        arret = {"demande": False}

        def _process_one(handlers: Any, *, queue: str = "default", db: Any = None) -> bool:
            if terminees:
                return False
            arret["demande"] = True       # l'ordre arrive pendant la tâche
            terminees.append("faite")     # elle se termine quand même
            return True

        with patch("forge_mvc_jobs.queue.process_one", _process_one):
            run_worker({}, stop=lambda: arret["demande"])

        assert terminees == ["faite"]


class TestAucuneRegression:

    def test_sans_stop_la_file_est_videe(self) -> None:
        file = _File(taille=7)

        with patch("forge_mvc_jobs.queue.process_one", file.process_one):
            traitees = drain({})

        assert traitees == 7

    def test_un_stop_deja_vrai_ne_traite_rien(self) -> None:
        """Un worker qui reçoit l'ordre avant de commencer ne commence pas."""
        file = _File(taille=5)
        file.arret_demande = True

        with patch("forge_mvc_jobs.queue.process_one", file.process_one):
            traitees = drain({}, stop=file.stop)

        assert traitees == 0
        assert file.traitees == []

    def test_max_jobs_reste_respecte(self) -> None:
        file = _File(taille=10)

        with patch("forge_mvc_jobs.queue.process_one", file.process_one):
            traitees = drain({}, max_jobs=4)

        assert traitees == 4

    def test_le_worker_dort_quand_la_file_est_vide(self) -> None:
        """Sans tâche, il ne tourne pas à vide sur le processeur."""
        file = _File(taille=0)
        dodos: list[float] = []

        def _sleep(duree: float) -> None:
            dodos.append(duree)
            file.arret_demande = True

        with patch("forge_mvc_jobs.queue.process_one", file.process_one), \
             patch("forge_mvc_jobs.queue.time.sleep", _sleep):
            run_worker({}, poll_interval=0.25, stop=file.stop)

        assert dodos == [0.25]
