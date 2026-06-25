"""QRCODE-OPTIN-SCAFFOLD-001 — Socle de génération QR Code.

Vérifie le comportement public réel du paquet (génération PNG/SVG, réponse HTTP,
erreurs d'entrée, types MIME) et l'indépendance de Forge Core vis-à-vis du paquet.
Exécutable depuis la racine (testpaths) ET en autonome
(`cd packages/forge-mvc-qrcode && pytest`). Skip propre si le paquet n'est pas installé.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_qrcode")
pytest.importorskip("segno")

from forge_mvc_qrcode import (  # noqa: E402
    PNG_MIME,
    SVG_MIME,
    QrCode,
    QrCodeError,
    QrCodeResponse,
)

_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


# --- Génération PNG ---------------------------------------------------------

def test_to_png_renvoie_des_octets_png_non_vides() -> None:
    png = QrCode.from_text("https://forgemvc.com").to_png()
    assert isinstance(png, bytes)
    assert png, "le PNG ne doit pas être vide"
    assert png.startswith(_PNG_MAGIC), "octets PNG non reconnaissables"


def test_png_mime_attendu() -> None:
    assert PNG_MIME == "image/png"


# --- Génération SVG ---------------------------------------------------------

def test_to_svg_renvoie_un_document_svg_non_vide() -> None:
    svg = QrCode.from_text("https://forgemvc.com").to_svg()
    assert isinstance(svg, str)
    assert svg, "le SVG ne doit pas être vide"
    assert "<svg" in svg, "contenu SVG non reconnaissable"


def test_svg_mime_attendu() -> None:
    assert SVG_MIME == "image/svg+xml"


# --- Erreurs d'entrée -------------------------------------------------------

@pytest.mark.parametrize("texte", ["", "   ", "\n\t"])
def test_texte_vide_leve_une_erreur_claire(texte: str) -> None:
    with pytest.raises(QrCodeError):
        QrCode.from_text(texte)


# --- Réponse HTTP -----------------------------------------------------------

def test_reponse_png_par_defaut() -> None:
    response = QrCodeResponse.from_text("https://forgemvc.com")
    assert response.status == 200
    assert response.content_type == "image/png"
    assert isinstance(response.body, bytes) and response.body.startswith(_PNG_MAGIC)


def test_reponse_svg_si_demandee() -> None:
    response = QrCodeResponse.from_text("https://forgemvc.com", fmt="svg")
    assert response.status == 200
    assert response.content_type == "image/svg+xml"
    body = response.body if isinstance(response.body, str) else response.body.decode("utf-8")
    assert "<svg" in body


def test_reponse_format_inconnu_leve_une_erreur() -> None:
    with pytest.raises(QrCodeError):
        QrCodeResponse.from_text("https://forgemvc.com", fmt="pdf")


def test_reponse_texte_vide_leve_une_erreur() -> None:
    with pytest.raises(QrCodeError):
        QrCodeResponse.from_text("")


# --- Indépendance de Forge Core --------------------------------------------

def _repo_root() -> Path | None:
    """Racine du monorepo (porte `core/` et le pyproject racine), ou None en install autonome."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "core").is_dir() and (parent / "pyproject.toml").is_file():
            return parent
    return None


def test_core_n_importe_pas_le_paquet_qrcode() -> None:
    root = _repo_root()
    if root is None:
        pytest.skip("hors monorepo : core/ non accessible")
    offenders = [
        str(path.relative_to(root))
        for path in (root / "core").rglob("*.py")
        if "forge_mvc_qrcode" in path.read_text(encoding="utf-8")
    ]
    assert not offenders, f"Forge Core ne doit pas connaître forge_mvc_qrcode : {offenders}"


def test_segno_absent_des_dependances_du_core() -> None:
    root = _repo_root()
    if root is None:
        pytest.skip("hors monorepo : pyproject racine non accessible")
    import tomllib

    data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    core_deps = " ".join(data.get("project", {}).get("dependencies", [])).lower()
    assert "segno" not in core_deps and "qrcode" not in core_deps, (
        "segno/qrcode ne doivent pas être des dépendances du core"
    )
