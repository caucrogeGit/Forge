"""`MSSQL-TLS-VERIFICATION-001` — la vérification du certificat se choisit.

`TrustServerCertificate=yes` était écrit **en dur** dans les deux chaînes de
connexion, celle d'exécution et celle d'administration. Cette option demande de
se fier au certificat sans la vérification habituelle : le chiffrement et
l'authentification du serveur sont deux garanties différentes, et Forge
n'offrait que la première sur son chemin normal.

Aucune connexion n'a été ouverte pour l'établir, et ce n'est pas la preuve
qu'une attaque réseau a eu lieu. C'est un défaut de configuration, sur le chemin
que tout le monde suit.

Le défaut vérifie désormais, et l'assouplissement de développement se déclare.
Mesuré contre le SQL Server local, à certificat auto-signé : sans la variable la
connexion est refusée sur `certificate verify failed`, avec elle les 167 tests
d'intégration passent.
"""
from __future__ import annotations

import pytest

pytest.importorskip("forge_mvc_mssql")

from forge_mvc_mssql import backend  # noqa: E402

CLES = (backend.ENV_ENCRYPT, backend.ENV_TRUST_CERTIFICATE)


@pytest.fixture(autouse=True)
def env_propre(monkeypatch: pytest.MonkeyPatch):
    """Les deux clés sont retirées : le test décrit ce qu'il pose, pas l'ambiant."""
    for cle in CLES:
        monkeypatch.delenv(cle, raising=False)


class TestLeDefautVerifie:
    """Sécuriser par défaut (principe 7)."""

    def test_sans_rien_poser_le_certificat_est_verifie(self) -> None:
        assert "TrustServerCertificate=no" in backend._options_tls()

    def test_le_chiffrement_est_demande(self) -> None:
        assert "Encrypt=yes" in backend._options_tls()

    def test_la_confiance_aveugle_n_est_plus_ecrite_en_dur(self) -> None:
        """Le défaut d'avant ne doit pas pouvoir revenir par une chaîne figée."""
        from pathlib import Path

        source = Path(backend.__file__).read_text(encoding="utf-8")

        assert 'f"TrustServerCertificate=yes"' not in source


class TestLAssouplissementSeDeclare:
    """Un serveur local à certificat auto-signé reste un cas légitime."""

    @pytest.mark.parametrize("valeur", ["yes", "true", "1", "oui", "YES", " yes "])
    def test_les_formes_affirmatives_sont_reconnues(
        self, valeur: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(backend.ENV_TRUST_CERTIFICATE, valeur)

        assert "TrustServerCertificate=yes" in backend._options_tls()

    @pytest.mark.parametrize("valeur", ["no", "false", "0", "non"])
    def test_les_formes_negatives_aussi(
        self, valeur: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(backend.ENV_TRUST_CERTIFICATE, valeur)

        assert "TrustServerCertificate=no" in backend._options_tls()

    @pytest.mark.parametrize("valeur", ["peutetre", "y", "", "  ", "vrai"])
    def test_une_valeur_inconnue_garde_le_defaut_sur(
        self, valeur: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Une faute de frappe ne doit pas désactiver une vérification."""
        monkeypatch.setenv(backend.ENV_TRUST_CERTIFICATE, valeur)

        assert "TrustServerCertificate=no" in backend._options_tls()


class TestLeModeStrict:
    """Les pilotes récents l'exigent, et il change le sens de la confiance."""

    @pytest.mark.parametrize("valeur", ["strict", "STRICT", " Strict "])
    def test_il_est_passe_tel_quel(self, valeur: str, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(backend.ENV_ENCRYPT, valeur)

        assert "Encrypt=strict" in backend._options_tls()

    def test_le_chiffrement_peut_etre_refuse_explicitement(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(backend.ENV_ENCRYPT, "no")

        assert "Encrypt=no" in backend._options_tls()


class TestLesDeuxChainesDeConnexion:
    """Exécution et administration doivent porter la même politique."""

    def test_les_deux_lisent_le_meme_helper(self) -> None:
        """L'une des deux oubliée laisserait `db:init` sans vérification."""
        from pathlib import Path

        source = Path(backend.__file__).read_text(encoding="utf-8")

        assert source.count('f"{_options_tls()}"') == 2
