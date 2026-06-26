"""Contrat d'erreurs de forge-mvc-qrcode (QRCODE-ERROR-CONTRACT-001).

Les entrées invalides (niveau de correction inconnu, texte trop long pour la
capacité d'un QR Code, `scale`/`border` hors bornes) doivent remonter une
:class:`QrCodeError` actionnable, jamais une exception `segno` brute
(principe 10 : une API publique est un contrat de complétude).
"""
from __future__ import annotations

import pytest

import segno

forge_mvc_qrcode = pytest.importorskip("forge_mvc_qrcode")

from forge_mvc_qrcode import QrCode, QrCodeError, QrCodeResponse


@pytest.mark.parametrize("error", ["z", "x", "lm", "", "1", "ll"])
def test_niveau_correction_inconnu_leve_qrcodeerror(error: str) -> None:
    with pytest.raises(QrCodeError):
        QrCode.from_text("https://forgemvc.com", error=error)


@pytest.mark.parametrize("error", ["l", "m", "q", "h", "L", "M", "Q", "H"])
def test_niveaux_correction_valides_acceptes(error: str) -> None:
    qr = QrCode.from_text("https://forgemvc.com", error=error)
    assert qr.to_png()


def test_texte_trop_long_leve_qrcodeerror() -> None:
    with pytest.raises(QrCodeError):
        QrCode.from_text("x" * 3000)


def test_overflow_n_expose_pas_l_exception_segno_brute() -> None:
    with pytest.raises(QrCodeError):
        try:
            QrCode.from_text("x" * 3000)
        except segno.DataOverflowError:  # pragma: no cover
            pytest.fail("DataOverflowError segno brute remontée au lieu de QrCodeError")


@pytest.mark.parametrize("scale", [0, -1, -10])
def test_scale_hors_borne_leve_qrcodeerror_png(scale: int) -> None:
    qr = QrCode.from_text("https://forgemvc.com")
    with pytest.raises(QrCodeError):
        qr.to_png(scale=scale)


@pytest.mark.parametrize("scale", [0, -1, -10])
def test_scale_hors_borne_leve_qrcodeerror_svg(scale: int) -> None:
    qr = QrCode.from_text("https://forgemvc.com")
    with pytest.raises(QrCodeError):
        qr.to_svg(scale=scale)


@pytest.mark.parametrize("border", [-1, -5])
def test_border_negatif_leve_qrcodeerror_png(border: int) -> None:
    qr = QrCode.from_text("https://forgemvc.com")
    with pytest.raises(QrCodeError):
        qr.to_png(border=border)


@pytest.mark.parametrize("border", [-1, -5])
def test_border_negatif_leve_qrcodeerror_svg(border: int) -> None:
    qr = QrCode.from_text("https://forgemvc.com")
    with pytest.raises(QrCodeError):
        qr.to_svg(border=border)


def test_border_zero_accepte() -> None:
    qr = QrCode.from_text("https://forgemvc.com")
    assert qr.to_png(border=0)


def test_reponse_scale_hors_borne_leve_qrcodeerror() -> None:
    with pytest.raises(QrCodeError):
        QrCodeResponse.from_text("https://forgemvc.com", scale=0)


def test_reponse_texte_trop_long_leve_qrcodeerror() -> None:
    with pytest.raises(QrCodeError):
        QrCodeResponse.from_text("x" * 3000)
