"""`TESTS-FORGE-REGISTRY-ISOLATION-001` — le registre du noyau ne fuit plus.

`forge.configure(...)` écrit dans un dictionnaire de module. Il n'a pas de
portée : ce qu'un test y pose, tous les suivants du même processus le lisent.

Mesuré, avec le message exact rendu par la suite :

    tests/test_e2e_upload_http.py pose upload_max_size=512
    puis les SEPT tests de forge-mvc-images tombent ensemble sur
    « Fichier trop volumineux : 2529 octets, maximum 512 »

La fixture de l'appelant isolait scrupuleusement ses trois variables
d'environnement par `monkeypatch`, et laissait le registre tel quel. Le plafond
de taille est justement celui que l'ADR-032 garde au noyau, hors environnement,
ce qui le rendait invisible à toute recherche menée du côté des variables.

Sous `-n --dist loadfile`, la panne ne se produit que si les deux fichiers
échoient au même worker. Deux chutes sur une dizaine de passages, aucune
reproduction à la demande, et huit hypothèses mortes avant celle-ci.

Ce que ce fichier fige est la **fin** : un test ne laisse pas le registre
modifié derrière lui. Il ne fige ni le nom de la fixture qui l'assure, ni sa
place, ni la clé employée pour la démonstration.
"""
from __future__ import annotations

import pytest

from core import forge

TEMOIN = 4242


class TestLeRegistreEstRenduIntact:
    """Deux tests successifs, dont le premier salit."""

    def test_1_salit_le_registre(self) -> None:
        """Ce test pose une valeur et ne la retire pas, exprès."""
        forge.configure(upload_max_size=TEMOIN)

        assert forge.get("upload_max_size") == TEMOIN

    def test_2_ne_voit_pas_la_salissure(self) -> None:
        """Le test précédent n'a rien laissé.

        L'ordre est garanti par la numérotation : pytest exécute les méthodes
        d'une classe dans leur ordre de définition.
        """
        assert forge.get("upload_max_size") != TEMOIN, (
            "le registre du noyau a fuité d'un test au suivant : "
            "l'isolation de conftest.py ne joue plus"
        )


class TestToutesLesClesSontRendues:
    """La restauration ne se limite pas à la clé de la démonstration."""

    def test_1_salit_plusieurs_cles(self) -> None:
        forge.configure(app_name="temoin-isolation", css_visible="temoin")

        assert forge.get("app_name") == "temoin-isolation"

    def test_2_les_retrouve_intactes(self) -> None:
        assert forge.get("app_name") != "temoin-isolation"
        assert forge.get("css_visible") != "temoin"


class TestLeStoreDeSessionAussi:
    """Le store a un effet de bord que réaffecter la clé ne défait pas.

    `forge.configure(session_store=...)` appelle `set_session_store` ; restaurer
    le dictionnaire seul rendrait la clé sans rendre le gestionnaire.
    """

    def test_1_pose_un_store(self) -> None:
        from core.sessions.memory_store import MemorySessionStore

        forge.configure(session_store=MemorySessionStore())

        assert forge.get("session_store") is not None

    def test_2_le_gestionnaire_est_rendu(self) -> None:
        from core.sessions.manager import get_session_store

        assert forge.get("session_store") is None, (
            "la clé session_store n'a pas été rendue"
        )
        # Le gestionnaire doit être revenu à son défaut, pas au store du test 1.
        assert get_session_store() is not None


class TestLaFuiteEtaitReelle:
    """Le scénario mesuré, réduit à ses deux gestes."""

    def test_un_plafond_pose_par_un_voisin_ne_refuse_plus_un_fichier(self) -> None:
        """512 octets était le plafond posé par le voisin ; le JPEG en fait 2529."""
        pytest.importorskip("forge_mvc_images")

        assert forge.get("upload_max_size") > 2529, (
            "un voisin a laissé un plafond d'upload qui refuse les fichiers "
            "d'essai des opt-ins images et files"
        )
