"""MFA-KEY-ROTATION-001 : faire tourner la clé Fernet sans fermer les comptes.

Avant ce ticket, `FORGE_MFA_SECRET_KEY` n'avait aucune procédure de rotation.
Changer la clé rendait tous les secrets TOTP illisibles d'un coup, donc tous
les porteurs d'un facteur perdaient leur second facteur au même instant. La
seule issue était de désactiver le MFA de tout le monde, ce qui transforme une
mesure d'hygiène en panne d'authentification.

`FORGE_MFA_SECRET_KEY_PREVIOUS` déclare les clés retirées, acceptées au
déchiffrement seulement. Le chiffrement utilise toujours la clé courante.
"""
from __future__ import annotations

import pytest

pytest.importorskip("forge_mvc_mfa")
pytest.importorskip("cryptography")

from cryptography.fernet import Fernet  # noqa: E402

from forge_mvc_mfa.secret_crypto import (  # noqa: E402
    MfaSecretInvalidKey,
    MfaSecretKeyPlaceholder,
    MfaSecretNotEncrypted,
    decrypt_totp_secret,
    encrypt_totp_secret,
    previous_keys,
    rotate_totp_secret,
    uses_current_key,
)

CLE_COURANTE = "FORGE_MFA_SECRET_KEY"
CLES_RETIREES = "FORGE_MFA_SECRET_KEY_PREVIOUS"

SECRET = "JBSWY3DPEHPK3PXP"


@pytest.fixture
def ancienne_cle() -> str:
    return Fernet.generate_key().decode()


@pytest.fixture
def nouvelle_cle() -> str:
    return Fernet.generate_key().decode()


def _poser(monkeypatch: pytest.MonkeyPatch, courante: str, retirees: str = "") -> None:
    monkeypatch.setenv(CLE_COURANTE, courante)
    if retirees:
        monkeypatch.setenv(CLES_RETIREES, retirees)
    else:
        monkeypatch.delenv(CLES_RETIREES, raising=False)


class TestRotationSansCoupure:
    """Le scénario réel : la clé change, personne ne perd son facteur."""

    def test_un_secret_ancien_reste_lisible_apres_rotation(
        self, monkeypatch: pytest.MonkeyPatch, ancienne_cle: str, nouvelle_cle: str
    ) -> None:
        """Le cas qui motivait le ticket."""
        _poser(monkeypatch, ancienne_cle)
        stocke = encrypt_totp_secret(SECRET)

        # L'exploitant tourne la clé et déclare l'ancienne.
        _poser(monkeypatch, nouvelle_cle, retirees=ancienne_cle)

        assert decrypt_totp_secret(stocke) == SECRET

    def test_sans_declarer_l_ancienne_cle_le_secret_est_perdu(
        self, monkeypatch: pytest.MonkeyPatch, ancienne_cle: str, nouvelle_cle: str
    ) -> None:
        """Ne pas déclarer l'ancienne clé reste une erreur, dite clairement."""
        _poser(monkeypatch, ancienne_cle)
        stocke = encrypt_totp_secret(SECRET)

        _poser(monkeypatch, nouvelle_cle)

        with pytest.raises(MfaSecretInvalidKey):
            decrypt_totp_secret(stocke)

    def test_le_rechiffrement_rend_le_secret_lisible_par_la_seule_cle_courante(
        self, monkeypatch: pytest.MonkeyPatch, ancienne_cle: str, nouvelle_cle: str
    ) -> None:
        """Après rechiffrement, l'ancienne clé peut être retirée de l'environnement."""
        _poser(monkeypatch, ancienne_cle)
        stocke = encrypt_totp_secret(SECRET)

        _poser(monkeypatch, nouvelle_cle, retirees=ancienne_cle)
        tourne = rotate_totp_secret(stocke)

        # L'ancienne clé disparaît : c'est la fin de la procédure.
        _poser(monkeypatch, nouvelle_cle)
        assert decrypt_totp_secret(tourne) == SECRET

    def test_plusieurs_cles_retirees_sont_acceptees(
        self, monkeypatch: pytest.MonkeyPatch, nouvelle_cle: str
    ) -> None:
        """Deux rotations rapprochées ne perdent pas les secrets les plus anciens."""
        tres_ancienne = Fernet.generate_key().decode()
        ancienne = Fernet.generate_key().decode()

        _poser(monkeypatch, tres_ancienne)
        vieux = encrypt_totp_secret(SECRET)
        _poser(monkeypatch, ancienne)
        recent = encrypt_totp_secret(SECRET)

        _poser(monkeypatch, nouvelle_cle, retirees=f"{ancienne},{tres_ancienne}")

        assert decrypt_totp_secret(vieux) == SECRET
        assert decrypt_totp_secret(recent) == SECRET


class TestReperageDuTravailRestant:
    """`uses_current_key` permet de balayer une table sans tout réécrire."""

    def test_un_secret_ancien_est_signale(
        self, monkeypatch: pytest.MonkeyPatch, ancienne_cle: str, nouvelle_cle: str
    ) -> None:
        _poser(monkeypatch, ancienne_cle)
        stocke = encrypt_totp_secret(SECRET)

        _poser(monkeypatch, nouvelle_cle, retirees=ancienne_cle)
        assert not uses_current_key(stocke)

    def test_un_secret_rechiffre_ne_l_est_plus(
        self, monkeypatch: pytest.MonkeyPatch, ancienne_cle: str, nouvelle_cle: str
    ) -> None:
        _poser(monkeypatch, ancienne_cle)
        stocke = encrypt_totp_secret(SECRET)

        _poser(monkeypatch, nouvelle_cle, retirees=ancienne_cle)
        assert uses_current_key(rotate_totp_secret(stocke))

    @pytest.mark.parametrize("valeur", ["", "en clair", "JBSWY3DPEHPK3PXP"])
    def test_une_valeur_non_chiffree_rend_faux_sans_lever(
        self, valeur: str, monkeypatch: pytest.MonkeyPatch, nouvelle_cle: str
    ) -> None:
        """Un balayage de table veut un tri, pas une interruption."""
        _poser(monkeypatch, nouvelle_cle)
        assert not uses_current_key(valeur)


class TestRefus:
    """Ce que la rotation refuse, et comment elle le dit."""

    def test_une_valeur_non_chiffree_est_refusee(
        self, monkeypatch: pytest.MonkeyPatch, nouvelle_cle: str
    ) -> None:
        _poser(monkeypatch, nouvelle_cle)
        with pytest.raises(MfaSecretNotEncrypted):
            rotate_totp_secret("en clair")

    def test_un_secret_inconnu_nomme_la_variable_a_renseigner(
        self, monkeypatch: pytest.MonkeyPatch, ancienne_cle: str, nouvelle_cle: str
    ) -> None:
        _poser(monkeypatch, ancienne_cle)
        stocke = encrypt_totp_secret(SECRET)
        _poser(monkeypatch, nouvelle_cle)

        with pytest.raises(MfaSecretInvalidKey, match=CLES_RETIREES):
            rotate_totp_secret(stocke)

    def test_une_cle_retiree_placeholder_est_refusee(
        self, monkeypatch: pytest.MonkeyPatch, nouvelle_cle: str
    ) -> None:
        """La liste des clés retirées est validée comme la clé courante."""
        _poser(monkeypatch, nouvelle_cle, retirees="change-me")
        with pytest.raises(MfaSecretKeyPlaceholder, match=CLES_RETIREES):
            decrypt_totp_secret(encrypt_totp_secret(SECRET))

    def test_une_cle_retiree_invalide_ne_fuit_pas_sa_valeur(
        self, monkeypatch: pytest.MonkeyPatch, nouvelle_cle: str
    ) -> None:
        secret_evident = "cle-invalide-mais-secrete"
        _poser(monkeypatch, nouvelle_cle, retirees=secret_evident)

        with pytest.raises(MfaSecretInvalidKey) as capture:
            decrypt_totp_secret(encrypt_totp_secret(SECRET))

        assert secret_evident not in str(capture.value)


class TestLectureDeLaListe:
    """Forme de `FORGE_MFA_SECRET_KEY_PREVIOUS`."""

    @pytest.mark.parametrize(
        ("brut", "attendu"),
        [
            ("", []),
            ("   ", []),
            ("a", ["a"]),
            ("a,b", ["a", "b"]),
            (" a , b ", ["a", "b"]),
            ("a,,b", ["a", "b"]),
            ("a,b,", ["a", "b"]),
            ("\na\n,\nb\n", ["a", "b"]),
        ],
    )
    def test_decoupage(
        self, brut: str, attendu: list[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Une virgule finale ou un retour à la ligne dans env/ ne casse rien."""
        monkeypatch.setenv(CLES_RETIREES, brut)
        assert previous_keys() == attendu

    def test_absente_vaut_liste_vide(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(CLES_RETIREES, raising=False)
        assert previous_keys() == []


def test_sans_cle_retiree_le_comportement_est_inchange(
    monkeypatch: pytest.MonkeyPatch, nouvelle_cle: str
) -> None:
    """Rétro-compatibilité : un projet qui ignore la rotation ne voit rien changer."""
    _poser(monkeypatch, nouvelle_cle)
    stocke = encrypt_totp_secret(SECRET)
    assert stocke.startswith("enc:")
    assert decrypt_totp_secret(stocke) == SECRET
    assert uses_current_key(stocke)
