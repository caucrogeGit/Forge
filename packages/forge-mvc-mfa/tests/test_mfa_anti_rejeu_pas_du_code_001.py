"""`MFA-ANTI-REJEU-PAS-DU-CODE-001` — un code accepté ne l'est qu'une fois.

L'anti-rejeu enregistrait le pas de l'**horloge serveur**, pas celui du code
présenté. Or la tolérance est de ±1 pas. Mesuré avec PyOTP, sur le code
inchangé :

    code du pas N, présenté pendant N-1  -> accepté, clé enregistrée N-1
    code du pas N, présenté pendant N    -> accepté, clé enregistrée N
    code du pas N, présenté pendant N+1  -> accepté, clé enregistrée N+1

Trois clés distinctes pour **un seul code** : il pouvait donc être consommé
trois fois. La RFC 6238 §5.2 demande qu'un OTP accepté ne soit pas rejouable.

Passer à un magasin partagé entre ouvriers ne corrigeait rien : il retenait
fidèlement la mauvaise clé. C'est une nuance qui compte, la limite documentée du
magasin en mémoire étant un autre sujet.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

pytest.importorskip("forge_mvc_mfa")
pyotp = pytest.importorskip("pyotp")

from forge_mvc_mfa.mfa import matching_totp_step, verify_totp_code  # noqa: E402
from forge_mvc_mfa.totp_replay import PERIODE_SECONDES, step_for_time  # noqa: E402

#: Milieu d'un pas, pour éviter les effets de bord d'une frontière.
INSTANT = 1788840015.0


@pytest.fixture
def secret() -> str:
    return pyotp.random_base32()


def _moment(decalage: float) -> datetime:
    return datetime.fromtimestamp(INSTANT + decalage, timezone.utc)


def _code_du_pas_courant(secret: str) -> str:
    return pyotp.TOTP(secret).at(_moment(0))


class TestLePasEstCeluiDuCode:
    """Le cœur du défaut."""

    @pytest.mark.parametrize(
        "decalage",
        [-PERIODE_SECONDES, 0, PERIODE_SECONDES],
        ids=["pas-precedent", "pas-courant", "pas-suivant"],
    )
    def test_un_meme_code_rend_toujours_le_meme_pas(self, decalage: float, secret: str) -> None:
        """Il rendait le pas de l'horloge, donc un pas différent à chaque fois."""
        code = _code_du_pas_courant(secret)

        assert matching_totp_step(secret, code, now=_moment(decalage)) == step_for_time(INSTANT)

    def test_un_seul_pas_pour_toute_la_fenetre(self, secret: str) -> None:
        """La propriété qui ferme le rejeu, formulée comme telle."""
        code = _code_du_pas_courant(secret)

        pas = {
            matching_totp_step(secret, code, now=_moment(d))
            for d in (-PERIODE_SECONDES, 0, PERIODE_SECONDES)
        }

        assert len(pas) == 1


class TestCeQuiEstRefuse:
    """Une fonction qui accepterait tout ne protégerait rien non plus."""

    @pytest.mark.parametrize(
        "code", ["000000", "", "abcdef", "12345", "1234567"],
        ids=["faux", "vide", "lettres", "trop-court", "trop-long"],
    )
    def test_un_code_invalide_ne_rend_aucun_pas(self, code: str, secret: str) -> None:
        assert matching_totp_step(secret, code, now=_moment(0)) is None

    def test_un_code_hors_fenetre_est_refuse(self, secret: str) -> None:
        """Deux pas d'écart sortent de la tolérance."""
        code = _code_du_pas_courant(secret)

        assert matching_totp_step(secret, code, now=_moment(2 * PERIODE_SECONDES)) is None

    @pytest.mark.parametrize("secret_invalide", ["", None, 42])
    def test_un_secret_invalide_ne_leve_pas(self, secret_invalide: object) -> None:
        assert matching_totp_step(secret_invalide, "123456", now=_moment(0)) is None  # type: ignore[arg-type]

    def test_une_fenetre_negative_est_refusee(self, secret: str) -> None:
        code = _code_du_pas_courant(secret)

        assert matching_totp_step(secret, code, valid_window=-1, now=_moment(0)) is None


class TestAccordAvecLaVerificationBooleenne:
    """Les deux fonctions doivent dire la même chose du même code."""

    @pytest.mark.parametrize(
        "decalage",
        [-2 * PERIODE_SECONDES, -PERIODE_SECONDES, 0, PERIODE_SECONDES, 2 * PERIODE_SECONDES],
    )
    def test_accepter_et_rendre_un_pas_vont_ensemble(self, decalage: float, secret: str) -> None:
        """Un désaccord ferait passer une authentification sans anti-rejeu."""
        code = _code_du_pas_courant(secret)
        moment = _moment(decalage)

        assert (matching_totp_step(secret, code, now=moment) is not None) is (
            verify_totp_code(secret, code, now=moment)
        )


class TestLeRejeuEstFerme:
    """Le scénario complet, avec le magasin anti-rejeu."""

    def test_le_meme_code_ne_passe_pas_deux_fois(self, secret: str) -> None:
        """Deux présentations à deux pas serveur différents, un seul succès."""
        from forge_mvc_mfa import totp_replay

        code = _code_du_pas_courant(secret)
        facteur = 987654

        premier = matching_totp_step(secret, code, now=_moment(0))
        assert premier is not None
        assert totp_replay.check_and_record(facteur, premier) is True

        second = matching_totp_step(secret, code, now=_moment(PERIODE_SECONDES))
        assert second == premier, "le pas doit être le même, c'est le même code"
        assert totp_replay.check_and_record(facteur, second) is False, (
            "un code déjà consommé ne doit pas l'être une seconde fois"
        )
