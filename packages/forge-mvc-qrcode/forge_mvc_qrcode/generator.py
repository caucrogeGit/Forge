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
        ``q``, ``h``). Lève :class:`QrCodeError` si le texte est vide ou ne
        contient que des espaces.
        """
        if not text or not text.strip():
            raise QrCodeError("Le texte du QR Code ne peut pas être vide.")
        qr = segno.make(text, error=error)
        return cls(qr, text)

    def to_png(self, *, scale: int = 4, border: int = 4) -> bytes:
        """Rend le QR Code en PNG et renvoie les octets bruts (non vides)."""
        buffer = io.BytesIO()
        self._qr.save(buffer, kind="png", scale=scale, border=border)
        return buffer.getvalue()

    def to_svg(self, *, scale: int = 4, border: int = 4) -> str:
        """Rend le QR Code en SVG et renvoie le document comme texte (non vide)."""
        buffer = io.BytesIO()
        self._qr.save(buffer, kind="svg", scale=scale, border=border)
        return buffer.getvalue().decode("utf-8")
