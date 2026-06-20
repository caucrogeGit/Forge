"""Garde-fou IMAGES-EXIF-STRIP-001.

Les variantes d'image générées (servies publiquement) ne doivent pas conserver
les métadonnées EXIF de la source (risque de fuite de géolocalisation), et
l'orientation EXIF doit être appliquée plutôt que transportée.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_images")

from PIL import Image

from forge_mvc_images.processing import _write_resized_image

_ORIENTATION_TAG = 0x0112
_MAKE_TAG = 0x010F


def _image_avec_exif(tmp_path: Path) -> Path:
    source = tmp_path / "source.jpg"
    image = Image.new("RGB", (200, 100), (10, 20, 30))
    exif = image.getexif()
    exif[_ORIENTATION_TAG] = 6  # rotation 90°
    exif[_MAKE_TAG] = "SecretCam"
    image.save(source, format="JPEG", exif=exif)
    return source


def test_la_variante_ne_conserve_pas_l_exif(tmp_path: Path) -> None:
    source = _image_avec_exif(tmp_path)
    target = tmp_path / "variante.jpg"

    with Image.open(source) as image:
        _write_resized_image(image, target, (50, 50))

    with Image.open(target) as variant:
        exif = variant.getexif()
        assert _ORIENTATION_TAG not in exif
        assert _MAKE_TAG not in exif


def test_l_orientation_est_appliquee(tmp_path: Path) -> None:
    # Orientation 6 = rotation 90° : largeur et hauteur sont échangées une fois
    # l'orientation appliquée. La source est 200x100, donc après transpose la
    # variante bornée à (500, 500) doit être plus haute que large.
    source = _image_avec_exif(tmp_path)
    target = tmp_path / "variante.jpg"

    with Image.open(source) as image:
        _write_resized_image(image, target, (500, 500))

    with Image.open(target) as variant:
        assert variant.height > variant.width
