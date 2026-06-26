# pyright: strict
"""Génération de QR Codes PNG et SVG, sans logique métier.

`QrCode` enveloppe la bibliothèque `segno` (pur Python, sans dépendance, écriture
PNG et SVG natives). L'objet ne sait rien de ce qu'il encode : l'application
décide du contenu (URL, texte, identifiant…). Le module n'écrit aucun fichier et
ne touche ni au routeur ni à la base de données.
"""
from __future__ import annotations

import io

import segno

from forge_mvc_qrcode.errors import QrCodeError

#: Type MIME d'une sortie PNG.
PNG_MIME = "image/png"
#: Type MIME d'une sortie SVG.
SVG_MIME = "image/svg+xml"

#: Niveaux de correction d'erreur acceptés par segno (insensibles à la casse).
ERROR_LEVELS = frozenset({"l", "m", "q", "h"})


class QrCode:
    """QR Code prêt à être rendu en PNG ou en SVG.

    À construire via :meth:`from_text`. Une instance est réutilisable : on peut
    appeler :meth:`to_png` et :meth:`to_svg` autant de fois que voulu.
    """

    def __init__(self, qr: segno.QRCode, text: str) -> None:
        self._qr = qr
        self.text = text

    @classmethod
    def from_text(cls, text: str, *, error: str = "m") -> QrCode:
        """Construit un QR Code à partir d'un texte ou d'une URL.

        `error` est le niveau de correction d'erreur de segno (``l``, ``m``,
        ``q``, ``h``, insensible à la casse). Lève :class:`QrCodeError` si le
        texte est vide ou ne contient que des espaces, si `error` n'est pas un
        niveau connu, ou si le texte dépasse la capacité d'un QR Code.
        """
        if not text or not text.strip():
            raise QrCodeError("Le texte du QR Code ne peut pas être vide.")
        if error.lower() not in ERROR_LEVELS:
            raise QrCodeError(
                f"Niveau de correction d'erreur inconnu : {error!r} "
                "(attendu 'l', 'm', 'q' ou 'h')."
            )
        try:
            qr = segno.make(text, error=error)
        except segno.DataOverflowError as exc:
            raise QrCodeError(
                "Le texte est trop long pour tenir dans un QR Code."
            ) from exc
        return cls(qr, text)

    @staticmethod
    def _check_dimensions(scale: int, border: int) -> None:
        """Borne `scale` (≥ 1) et `border` (≥ 0) avant le rendu segno."""
        if scale < 1:
            raise QrCodeError(f"L'échelle (scale) doit être ≥ 1. Reçu : {scale}.")
        if border < 0:
            raise QrCodeError(f"La marge (border) doit être ≥ 0. Reçu : {border}.")

    def to_png(self, *, scale: int = 4, border: int = 4) -> bytes:
        """Rend le QR Code en PNG et renvoie les octets bruts (non vides).

        Lève :class:`QrCodeError` si `scale` < 1 ou `border` < 0.
        """
        self._check_dimensions(scale, border)
        buffer = io.BytesIO()
        self._qr.save(buffer, kind="png", scale=scale, border=border)
        return buffer.getvalue()

    def to_svg(self, *, scale: int = 4, border: int = 4) -> str:
        """Rend le QR Code en SVG et renvoie le document comme texte (non vide).

        Lève :class:`QrCodeError` si `scale` < 1 ou `border` < 0.
        """
        self._check_dimensions(scale, border)
        buffer = io.BytesIO()
        self._qr.save(buffer, kind="svg", scale=scale, border=border)
        return buffer.getvalue().decode("utf-8")
