"""DEPLOY-ENVFILE-READABLE-001 — le compte de service peut lire ses secrets.

Mesuré à la première mise en production réelle (retour terrain SéquenCiel,
2026-08-24). L'unité générée déclarait `User=www-data` et
`EnvironmentFile={project_dir}/env/prod`.

`env/prod` porte le mot de passe de la base. Un fichier de secrets se pose en
`600`, appartenant à celui qui déploie : `www-data` ne le lit pas, et le service
ne démarre pas. `www-data` mérite d'ailleurs d'être discuté en soi, c'est le
compte du serveur web, qui n'a aucune raison d'être celui de l'application.

Ce qui rend ce défaut coûteux n'est pas la panne, franche, mais la sortie de
secours qu'elle suggère : élargir les droits du fichier, ou ceux du projet
entier. C'est le geste qu'on fait sans réfléchir un soir de mise en service, et
c'est exactement le mauvais. Le contrôle nomme donc le geste juste dans son
message.

Le pré-vol se lance souvent depuis un poste qui n'est pas la machine de
production : quand la question n'est pas tranchable ici, le contrôle se tait ou
avertit, il n'invente jamais un refus.
"""
from __future__ import annotations

import getpass
import os
from pathlib import Path

import pytest

from forge_mvc_deploy.cli.deploy import (
    _peut_lire,
    _systemd_service,
    _valeur_de_la_cle,
    _verifier_lecture_env_prod,
)

MOI = getpass.getuser()


@pytest.fixture
def projet(tmp_path: Path):
    """Rend une fabrique de projet : unité + env/prod, aux droits voulus."""
    def _poser(*, utilisateur: str = MOI, mode: int = 0o600,
               avec_env: bool = True, env_file: "str | None" = None) -> Path:
        dossier = tmp_path / "deploy" / "systemd"
        dossier.mkdir(parents=True, exist_ok=True)
        chemin_env = env_file if env_file is not None else str(tmp_path / "env" / "prod")
        (dossier / "forge-app.service").write_text(
            "[Unit]\nDescription=X\n\n"
            "[Service]\nType=simple\n"
            f"User={utilisateur}\n"
            f"EnvironmentFile={chemin_env}\n",
            encoding="utf-8")
        if avec_env:
            (tmp_path / "env").mkdir(exist_ok=True)
            fichier = tmp_path / "env" / "prod"
            fichier.write_text("DB_NAME=x\n", encoding="utf-8")
            fichier.chmod(mode)
        return tmp_path
    return _poser


# ── Le gabarit écrit ─────────────────────────────────────────────────────────

class TestGabarit:

    def test_le_compte_du_serveur_web_n_est_plus_propose(self) -> None:
        """`www-data` sert Nginx ; il n'a pas à exécuter l'application."""
        assert "User=www-data" not in _systemd_service(Path("/srv/app"))

    def test_un_compte_de_service_dedie_est_propose(self) -> None:
        assert "User=forge-app" in _systemd_service(Path("/srv/app"))

    def test_la_creation_du_compte_est_ecrite_dans_l_unite(self) -> None:
        """La commande doit être là où on lit le fichier, pas ailleurs."""
        rendu = _systemd_service(Path("/srv/app"))

        assert "useradd" in rendu
        assert "chmod 600 /srv/app/env/prod" in rendu

    def test_la_mauvaise_sortie_de_secours_est_nommee(self) -> None:
        assert "Elargir les droits" in _systemd_service(Path("/srv/app"))


# ── La lecture des clés d'unité ──────────────────────────────────────────────

class TestValeurDeLaCle:

    def test_lit_la_cle_de_la_bonne_section(self) -> None:
        texte = "[Unit]\nUser=piege\n\n[Service]\nUser=forge-app\n"

        assert _valeur_de_la_cle(texte, "User", "Service") == "forge-app"

    def test_cle_absente_de_la_section_rend_none(self) -> None:
        assert _valeur_de_la_cle("[Unit]\nUser=x\n", "User", "Service") is None

    def test_ignore_les_commentaires(self) -> None:
        texte = "[Service]\n# User=fantome\nUser=forge-app\n"

        assert _valeur_de_la_cle(texte, "User", "Service") == "forge-app"


# ── Le calcul de lisibilité ──────────────────────────────────────────────────

class TestPeutLire:

    def test_proprietaire_avec_600_peut_lire(self, tmp_path: Path) -> None:
        fichier = tmp_path / "prod"
        fichier.write_text("x")
        fichier.chmod(0o600)

        assert _peut_lire(fichier, MOI) is True

    def test_proprietaire_sans_bit_de_lecture_ne_peut_pas(self, tmp_path: Path) -> None:
        fichier = tmp_path / "prod"
        fichier.write_text("x")
        fichier.chmod(0o200)

        assert _peut_lire(fichier, MOI) is False

    def test_compte_inconnu_rend_none(self, tmp_path: Path) -> None:
        """Le pré-vol tourne souvent ailleurs qu'en production."""
        fichier = tmp_path / "prod"
        fichier.write_text("x")

        assert _peut_lire(fichier, "compte-qui-n-existe-pas-ici") is None

    def test_fichier_absent_rend_none(self, tmp_path: Path) -> None:
        assert _peut_lire(tmp_path / "absent", MOI) is None

    def test_le_compte_root_lit_tout(self, tmp_path: Path) -> None:
        fichier = tmp_path / "prod"
        fichier.write_text("x")
        fichier.chmod(0o000)

        assert _peut_lire(fichier, "root") is True


# ── Le contrôle complet ──────────────────────────────────────────────────────

class TestControle:

    def test_compte_qui_lit_valide(self, projet) -> None:
        resultat = _verifier_lecture_env_prod(projet())

        assert resultat is not None
        assert resultat.status == "ok"

    @pytest.mark.skipif(os.geteuid() == 0, reason="root lit tout : le cas ne se produit pas")
    def test_compte_qui_ne_lit_pas_est_une_erreur(self, projet) -> None:
        """La panne est franche : ce n'est pas un avertissement."""
        racine = projet(mode=0o600)
        (racine / "env" / "prod").chmod(0o200)

        resultat = _verifier_lecture_env_prod(racine)

        assert resultat is not None
        assert resultat.status == "error"

    @pytest.mark.skipif(os.geteuid() == 0, reason="root lit tout : le cas ne se produit pas")
    def test_le_message_nomme_le_geste_juste(self, projet) -> None:
        """Et pas celui qu'on ferait d'instinct."""
        racine = projet(mode=0o200)

        resultat = _verifier_lecture_env_prod(racine)

        assert resultat is not None
        assert "chown" in resultat.detail
        assert "élargir les droits" in resultat.detail

    def test_compte_inconnu_avertit_sans_conclure(self, projet) -> None:
        resultat = _verifier_lecture_env_prod(projet(utilisateur="compte-inconnu-ici"))

        assert resultat is not None
        assert resultat.status == "warn"
        assert "production" in resultat.detail

    def test_env_prod_absent_ne_dit_rien(self, projet) -> None:
        """Son absence est déjà signalée ailleurs."""
        assert _verifier_lecture_env_prod(projet(avec_env=False)) is None

    def test_unite_absente_ne_dit_rien(self, tmp_path: Path) -> None:
        assert _verifier_lecture_env_prod(tmp_path) is None

    def test_le_tiret_de_fichier_optionnel_est_ignore(self, projet, tmp_path: Path) -> None:
        """`EnvironmentFile=-/chemin` dit à systemd de tolérer l'absence."""
        racine = projet(env_file=f"-{tmp_path / 'env' / 'prod'}")

        resultat = _verifier_lecture_env_prod(racine)

        assert resultat is not None
        assert resultat.status == "ok"
