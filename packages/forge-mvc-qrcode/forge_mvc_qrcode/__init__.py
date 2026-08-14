# pyright: strict
"""forge-mvc-qrcode — Génération de QR Codes opt-in (QRCODE-OPTIN-SCAFFOLD-001).

Brique générique : produire un QR Code PNG ou SVG depuis du texte ou une URL, et
le servir via une réponse HTTP utilisable dans un contrôleur Forge. Le cœur de
Forge ignore tout des QR Codes ; ce paquet fournit l'API ; l'application décide
de ce qu'elle encode (lien, identifiant, accès à une activité…).
"""
from forge_mvc_qrcode.errors import QrCodeError
from forge_mvc_qrcode.generator import PNG_MIME, SVG_MIME, QrCode
from forge_mvc_qrcode.response import QrCodeResponse

__version__ = "1.0.0rc6"

__all__ = [
    "QrCode",
    "QrCodeResponse",
    "QrCodeError",
    "PNG_MIME",
    "SVG_MIME",
]
