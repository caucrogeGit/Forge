"""DEPLOY-CHECK-SECRETS-001 : le pré-vol refuse un secret laissé à sa valeur d'amorçage.

`deploy:check` vérifiait `DB_HOST`, `DB_NAME` et `DB_APP_LOGIN`, jamais les mots
de passe ni les jetons. Un `DB_APP_PWD=change-me` recopié d'un exemple passait
donc le contrôle, et la panne n'apparaissait qu'au premier accès à la base, en
production.

Le repérage porte sur le nom de la variable et non sur une liste figée, pour
qu'un opt-in ajouté demain soit couvert sans toucher au module.
"""
from __future__ import annotations

import pytest

pytest.importorskip("forge_mvc_deploy")

from forge_mvc_deploy.cli.deploy import _verifier_secrets_amorces  # noqa: E402

SECRET_REEL = "xK9$mP2vL7qR4nT8"


def _statuts(cfg: dict[str, str]) -> list[str]:
    return [r.status for r in _verifier_secrets_amorces(cfg)]


def _details(cfg: dict[str, str]) -> str:
    return " | ".join(r.detail for r in _verifier_secrets_amorces(cfg))


class TestValeursRefusees:
    @pytest.mark.parametrize(
        "valeur",
        ["change-me", "changeme", "CHANGE-ME", "  change_me  ", "default",
         "secret", "password", "todo", "xxx", "placeholder", "", "   "],
    )
    def test_une_valeur_d_amorcage_est_refusee(self, valeur: str) -> None:
        assert "error" in _statuts({"DB_APP_PWD": valeur})

    def test_un_secret_reel_passe(self) -> None:
        assert _statuts({"DB_APP_PWD": SECRET_REEL}) == ["ok"]

    def test_le_nom_fautif_est_nomme(self) -> None:
        detail = _details({"DB_APP_PWD": "change-me", "DB_ADMIN_PWD": SECRET_REEL})
        assert "DB_APP_PWD" in detail

    def test_la_valeur_n_est_jamais_rendue(self) -> None:
        """Le rapport peut être collé dans un ticket : un secret réel y fuirait."""
        detail = _details({"DB_APP_PWD": SECRET_REEL, "MAIL_PASSWORD": "change-me"})
        assert SECRET_REEL not in detail


class TestVariablesRepérées:
    @pytest.mark.parametrize(
        "nom",
        ["DB_APP_PWD", "DB_ADMIN_PWD", "MAIL_PASSWORD", "FORGE_MFA_SECRET_KEY",
         "FORGE_IOT_API_TOKEN", "FORGE_VIDEO_API_TOKEN", "FORGE_AUDIO_API_TOKEN"],
    )
    def test_les_secrets_connus_de_forge_sont_couverts(self, nom: str) -> None:
        assert "error" in _statuts({nom: "change-me"})

    def test_un_opt_in_futur_est_couvert_sans_changer_le_module(self) -> None:
        """Le repérage porte sur le nom, pas sur une liste figée."""
        assert "error" in _statuts({"FORGE_TOTALEMENT_NOUVEAU_TOKEN": "change-me"})

    @pytest.mark.parametrize(
        "nom", ["SSL_KEYFILE", "SSL_CERTFILE", "DB_NAME", "DB_HOST", "APP_HOST",
                "APP_CSP_NONCE_ENABLED", "UPLOAD_ROOT", "APP_ENV"],
    )
    def test_ce_qui_n_est_pas_un_secret_est_laisse_tranquille(self, nom: str) -> None:
        """Un contrôle qui crie à tort finit désactivé."""
        assert _statuts({nom: "dev"}) == []

    def test_un_chemin_de_cle_n_est_pas_une_cle(self) -> None:
        """`SSL_KEYFILE` nomme un fichier, et sa valeur ressemble à un placeholder."""
        assert _statuts({"SSL_KEYFILE": "key.pem"}) == []


class TestRapport:
    def test_sans_secret_declare_le_pre_vol_se_tait(self) -> None:
        """Un projet sans opt-in à secret ne doit pas voir de ligne inutile."""
        assert _verifier_secrets_amorces({"DB_HOST": "localhost"}) == []

    def test_les_secrets_sains_sont_comptes(self) -> None:
        detail = _details({"DB_APP_PWD": SECRET_REEL, "DB_ADMIN_PWD": SECRET_REEL})
        assert "2 renseigné" in detail

    def test_un_melange_produit_les_deux_lignes(self) -> None:
        statuts = _statuts({"DB_APP_PWD": "change-me", "DB_ADMIN_PWD": SECRET_REEL})
        assert "error" in statuts and "ok" in statuts


class TestSourcePartagee:
    def test_la_liste_vient_du_coeur(self) -> None:
        """Elle était privée dans forge-mvc-mfa, un opt-in ne pouvant dépendre d'un autre."""
        from core.security.secrets import PLACEHOLDER_VALUES
        from forge_mvc_mfa.secret_crypto import _PLACEHOLDER_KEYS  # pyright: ignore[reportPrivateUsage]

        assert _PLACEHOLDER_KEYS is PLACEHOLDER_VALUES
