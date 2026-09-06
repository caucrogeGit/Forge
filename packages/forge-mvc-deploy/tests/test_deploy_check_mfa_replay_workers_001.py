"""DEPLOY-CHECK-MFA-REPLAY-WORKERS-001 : le rejeu TOTP sous plusieurs travailleurs.

Le pré-vol refusait déjà un magasin de **sessions** en mémoire sous plusieurs
travailleurs : chacun a le sien, et une connexion sur quatre aboutit.

Le registre anti-rejeu TOTP a exactement la même forme, et une conséquence plus
grave. La RFC 6238 §5.2 demande qu'un code accepté ne soit pas rejouable ; le
magasin par défaut vit dans la mémoire du processus. Quatre travailleurs, et un
code à six chiffres vaut quatre fois au lieu d'une.

Rien ne le signalait au moment où cela se décide, c'est à dire avant la mise en
service. Un avertissement et non une erreur : l'application fonctionne, la
seconde authentification protège toujours, et seule la fenêtre de rejeu
s'élargit. Le remède reste au choix de l'exploitant selon son modèle de menace.
"""
from __future__ import annotations

from pathlib import Path


from forge_mvc_deploy.cli.deploy import _verifier_rejeu_totp_multi_travailleurs

QUATRE = "[Service]\nExecStart=/srv/.venv/bin/gunicorn --workers 4 wsgi:application\n"
UN = "[Service]\nExecStart=/srv/.venv/bin/gunicorn --workers 1 wsgi:application\n"
CABLAGE = (
    "from forge_mvc_mfa import set_replay_store\n"
    "from forge_mvc_mfa.replay_store_db import DbTotpReplayStore\n"
    "set_replay_store(DbTotpReplayStore())\n"
)


def _projet(tmp_path: Path, unite: str, bootstrap: "str | None" = None) -> "tuple[Path, Path]":
    (tmp_path / "deploy" / "systemd").mkdir(parents=True)
    chemin = tmp_path / "deploy" / "systemd" / "forge-app.service"
    chemin.write_text(unite, encoding="utf-8")
    if bootstrap is not None:
        (tmp_path / "bootstrap.py").write_text(bootstrap, encoding="utf-8")
    return tmp_path, chemin


class TestLeSignalement:

    def test_plusieurs_travailleurs_sans_magasin_partage(self, tmp_path: Path) -> None:
        racine, unite = _projet(tmp_path, QUATRE)

        resultat = _verifier_rejeu_totp_multi_travailleurs(racine, unite)

        assert resultat is not None
        assert resultat.status == "warn"

    def test_le_message_chiffre_la_consequence(self, tmp_path: Path) -> None:
        """« Un code vaudra 4 fois » se comprend ; « magasin non partagé » non."""
        racine, unite = _projet(tmp_path, QUATRE)

        resultat = _verifier_rejeu_totp_multi_travailleurs(racine, unite)

        assert resultat is not None
        assert "4 fois" in resultat.detail
        assert "6238" in resultat.detail

    def test_le_message_nomme_le_geste(self, tmp_path: Path) -> None:
        racine, unite = _projet(tmp_path, QUATRE)

        resultat = _verifier_rejeu_totp_multi_travailleurs(racine, unite)

        assert resultat is not None
        assert "set_replay_store" in resultat.detail

    def test_c_est_un_avertissement_pas_une_erreur(self, tmp_path: Path) -> None:
        """L'application fonctionne ; seule la fenêtre de rejeu s'élargit."""
        racine, unite = _projet(tmp_path, QUATRE)

        resultat = _verifier_rejeu_totp_multi_travailleurs(racine, unite)

        assert resultat is not None
        assert resultat.status != "error"


class TestLeSilence:
    """Une garde qui parle à tort finit désactivée."""

    def test_un_seul_travailleur_ne_declenche_rien(self, tmp_path: Path) -> None:
        racine, unite = _projet(tmp_path, UN)

        assert _verifier_rejeu_totp_multi_travailleurs(racine, unite) is None

    def test_un_magasin_cable_passe(self, tmp_path: Path) -> None:
        racine, unite = _projet(tmp_path, QUATRE, CABLAGE)

        resultat = _verifier_rejeu_totp_multi_travailleurs(racine, unite)

        assert resultat is not None
        assert resultat.status == "ok"

    def test_sans_unite_le_controle_se_tait(self, tmp_path: Path) -> None:
        assert _verifier_rejeu_totp_multi_travailleurs(
            tmp_path, tmp_path / "absent.service") is None


class TestLaLectureEstSyntaxique:
    """Par `ast` et jamais par `grep` : le squelette livre des exemples commentés."""

    def test_un_exemple_commente_n_est_pas_un_cablage(self, tmp_path: Path) -> None:
        racine, unite = _projet(
            tmp_path, QUATRE, "# set_replay_store(DbTotpReplayStore())\n")

        resultat = _verifier_rejeu_totp_multi_travailleurs(racine, unite)

        assert resultat is not None
        assert resultat.status == "warn"

    def test_le_nom_dans_une_chaine_n_est_pas_un_cablage(self, tmp_path: Path) -> None:
        racine, unite = _projet(
            tmp_path, QUATRE, 'AIDE = "appelez set_replay_store(...)"\n')

        resultat = _verifier_rejeu_totp_multi_travailleurs(racine, unite)

        assert resultat is not None
        assert resultat.status == "warn"

    def test_un_bootstrap_illisible_n_est_pas_pris_pour_un_cablage(
        self, tmp_path: Path
    ) -> None:
        racine, unite = _projet(tmp_path, QUATRE, "def (((\n")

        resultat = _verifier_rejeu_totp_multi_travailleurs(racine, unite)

        assert resultat is not None
        assert resultat.status == "warn"
