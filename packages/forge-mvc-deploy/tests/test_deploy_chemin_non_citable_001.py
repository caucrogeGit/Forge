"""`DEPLOY-CHEMIN-NON-CITABLE-001` — un chemin qu'on ne sait pas citer est refusé.

Le chemin du projet est inséré tel quel dans une unité systemd, une
configuration Nginx et un README de commandes shell. Les trois découpent
différemment :

    ExecStart=/srv/Mon projet/app/.venv/bin/gunicorn wsgi:application

systemd y lit l'exécutable `/srv/Mon` et un argument `projet/app/…`. Le service
ne démarre pas, et le message ne désigne pas la cause.

Poser trois syntaxes de citation, c'est se donner trois occasions d'en écrire
une fausse, et le fichier engendré est ensuite copié tel quel sur un serveur. Le
refus est explicite et dit quoi faire.

Ce constat venait d'une revue externe, qui l'avait établi **statiquement** : il
n'y avait pas de sonde pour lui, contrairement aux dix-sept autres. Il a donc
failli passer avec les deux autres constats statiques.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_deploy")

from forge_mvc_deploy.cli.deploy import (  # noqa: E402
    _refus_de_chemin,
    _systemd_service,
    cmd_deploy_init,
)


class TestCeQuiEstRefuse:
    """Les caractères qu'aucun des trois formats ne traite pareil."""

    @pytest.mark.parametrize(
        "chemin",
        [
            "/srv/Mon projet/app",
            "/srv/app avec espace",
            '/srv/a"b',
            "/srv/a'b",
            "/srv/a\\b",
            "/srv/a\tb",
        ],
        ids=["espace-milieu", "espace-fin", "guillemet", "apostrophe",
             "antislash", "tabulation"],
    )
    def test_le_chemin_est_refuse(self, chemin: str) -> None:
        assert _refus_de_chemin(Path(chemin)) is not None

    def test_le_motif_nomme_le_chemin_et_la_sortie(self) -> None:
        """Un refus qui ne dit pas quoi faire oblige à chercher."""
        motif = _refus_de_chemin(Path("/srv/Mon projet/app"))

        assert motif is not None
        assert "/srv/Mon projet/app" in motif
        assert "systemd" in motif
        assert "Déplacez le projet" in motif


class TestCeQuiPasse:
    """Un refus qui refuserait tout ne servirait à rien non plus."""

    @pytest.mark.parametrize(
        "chemin",
        ["/srv/mon-projet", "/srv/app_2026", "/home/roger/Projets/Forge", "/srv/a.b.c"],
    )
    def test_un_chemin_ordinaire_est_accepte(self, chemin: str) -> None:
        assert _refus_de_chemin(Path(chemin)) is None


class TestRienNEstEcritAvantLeRefus:
    """Un refus qui laisse des fichiers oblige à deviner lesquels sont bons."""

    def test_la_commande_s_arrete_sans_rien_poser(self, tmp_path: Path) -> None:
        racine = tmp_path / "Mon projet"
        racine.mkdir()

        with pytest.raises(SystemExit) as capture:
            cmd_deploy_init(racine)

        assert capture.value.code == 2
        assert not (racine / "deploy").exists()
        assert not (racine / "wsgi.py").exists()


class TestLUniteEngendreeResteJuste:
    """Sur un chemin accepté, le contenu ne change pas."""

    def test_l_executable_est_un_seul_mot(self) -> None:
        unite = _systemd_service(Path("/srv/mon-projet"))
        ligne = next(l for l in unite.splitlines() if l.startswith("ExecStart="))
        executable = ligne[len("ExecStart="):].split()[0]

        assert executable == "/srv/mon-projet/.venv/bin/gunicorn"
