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
        error: str = "m",
        headers: "dict[str, str] | None" = None,
    ) -> Response:
        """Construit une réponse servant le QR Code de `text`.

        `fmt` vaut ``"png"`` (défaut, ``Content-Type: image/png``) ou ``"svg"``
        (``Content-Type: image/svg+xml``).

        `error` est le niveau de correction d'erreur, ``l``, ``m``, ``q`` ou
        ``h`` (`QRCODE-ERROR-LEVEL-001`). Il existait sur `QrCode.from_text`
        mais **cette fabrique ne le transmettait pas**, si bien qu'un
        contrôleur, c'est à dire le chemin documenté pour servir un QR Code, ne
        pouvait pas le choisir.

        Ce n'est pas un réglage de confort : un code imprimé sur une étiquette
        ou une affiche, susceptible d'être rayé ou partiellement couvert,
        demande ``h``, qui tolère 30 % de perte. En ``m``, le défaut, qui en
        tolère 15 %, il devient illisible.

        Lève :class:`QrCodeError` si le texte est vide, si le format est
        inconnu, ou si le niveau de correction ne l'est pas.
        """
        qr = QrCode.from_text(text, error=error)
        if fmt == "png":
            return Response(200, qr.to_png(scale=scale, border=border), PNG_MIME, headers=headers or {})
        if fmt == "svg":
            return Response(200, qr.to_svg(scale=scale, border=border), SVG_MIME, headers=headers or {})
        raise QrCodeError(f"Format de QR Code inconnu : {fmt!r} (attendu 'png' ou 'svg').")
