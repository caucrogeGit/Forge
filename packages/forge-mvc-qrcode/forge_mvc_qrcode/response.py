# pyright: strict
"""Réponse HTTP servant un QR Code depuis un contrôleur Forge.

`QrCodeResponse.from_text` renvoie une `core.http.Response` ordinaire : un
contrôleur la retourne telle quelle. Aucun stockage automatique, aucune route
imposée. La dépendance va de l'opt-in vers le cœur, jamais l'inverse.
"""
from __future__ import annotations

from core.http import Response

from forge_mvc_qrcode.errors import QrCodeError
from forge_mvc_qrcode.generator import PNG_MIME, SVG_MIME, QrCode


class QrCodeResponse:
    """Fabrique de réponses HTTP servant un QR Code.

    Classe sans état : uniquement une fabrique explicite, pas de magie cachée.
    """

    @staticmethod
    def from_text(
        text: str,
        *,
        fmt: str = "png",
        scale: int = 4,
        border: int = 4,
        headers: "dict[str, str] | None" = None,
    ) -> Response:
        """Construit une réponse servant le QR Code de `text`.

        `fmt` vaut ``"png"`` (défaut, ``Content-Type: image/png``) ou ``"svg"``
        (``Content-Type: image/svg+xml``). Lève :class:`QrCodeError` si le texte
        est vide ou si le format est inconnu.
        """
        qr = QrCode.from_text(text)
        if fmt == "png":
            return Response(200, qr.to_png(scale=scale, border=border), PNG_MIME, headers=headers or {})
        if fmt == "svg":
            return Response(200, qr.to_svg(scale=scale, border=border), SVG_MIME, headers=headers or {})
        raise QrCodeError(f"Format de QR Code inconnu : {fmt!r} (attendu 'png' ou 'svg').")
