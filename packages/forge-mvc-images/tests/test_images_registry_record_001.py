"""`IMAGES-REGISTRY-RECORD-001` — la purge d'orphelins ne détruit plus les images.

`forge-mvc-images` écrit sous `UPLOAD_ROOT` et n'inscrivait rien au registre de
`forge-mvc-files`. La purge d'orphelins rapproche le disque et le registre : une
image absente du registre y est donc **un orphelin**, et
`forge files:orphans --delete` la supprimait.

Le garde-fou du registre vide ne protégeait pas ce cas. Il ne se déclenche que
si le registre est **entièrement** vide. Un projet qui inscrit ses documents,
comme la documentation de `forge-mvc-files` l'enseigne, et qui utilise cet
opt-in pour ses images, avait un registre peuplé et des images signalées
orphelines.

Mesuré avant correction, sur un projet portant un document inscrit et une image
non inscrite :

    disque : 3 fichiers, registre : 1 inscription
    signalés comme orphelins : media/photo.jpg, media/photo_thumbnail.jpg

L'original **et ses variantes**. Deux opt-ins officiels, dont l'un dépend de
l'autre, et la purge de l'un supprimait les fichiers de l'autre.

## Pourquoi l'inscription est au mieux

La table `forge_files` est optionnelle (ADR-094). Faire échouer une sauvegarde
d'image parce qu'un registre n'est pas provisionné serait disproportionné.

Ce n'est pas une dégradation silencieuse pour autant : sans cette table,
`find_orphans` lève aussi, et la purge ne peut pas tourner. Les deux cas
s'alignent, il n'y a pas de fenêtre où l'inscription manque pendant que la purge
supprime.
"""
from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

pytest.importorskip("forge_mvc_images")
pytest.importorskip("forge_mvc_files")
pytest.importorskip("PIL")


def _octets_jpeg() -> bytes:
    from PIL import Image

    tampon = io.BytesIO()
    Image.new("RGB", (400, 300), "red").save(tampon, format="JPEG")
    return tampon.getvalue()


class _Fichier:
    filename = "photo.jpg"
    content_type = "image/jpeg"

    def __init__(self, octets: bytes) -> None:
        self._octets = octets

    def read(self) -> bytes:
        return self._octets


@pytest.fixture
def racine(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path))
    return tmp_path


def _ecrire_et_relever(racine: Path, *, variantes: bool = True) -> "tuple[list[str], list[str]]":
    """Rend (fichiers écrits, chemins inscrits)."""
    import forge_mvc_files
    from forge_mvc_images.processing import generate_image_variants, save_image

    inscrits: "list[str]" = []
    with patch.object(forge_mvc_files, "record_file",
                      side_effect=lambda *a, **k: inscrits.append(a[0])):
        media = save_image(_Fichier(_octets_jpeg()), category="images")
        if variantes:
            generate_image_variants(media.path)

    ecrits = sorted(
        chemin.relative_to(racine).as_posix()
        for chemin in racine.rglob("*") if chemin.is_file()
    )
    return ecrits, inscrits


# ─────────────────────────────────────────────────────────────────────────────
# Tout ce qui est écrit est inscrit
# ─────────────────────────────────────────────────────────────────────────────


class TestInscription:

    def test_l_original_est_inscrit(self, racine: Path) -> None:
        ecrits, inscrits = _ecrire_et_relever(racine, variantes=False)

        assert len(ecrits) == 1
        assert inscrits == ecrits

    def test_les_variantes_sont_inscrites_aussi(self, racine: Path) -> None:
        """Une vignette est un fichier de plus sous `UPLOAD_ROOT`, donc un
        orphelin de plus. Elle était signalée au même titre que l'original."""
        ecrits, inscrits = _ecrire_et_relever(racine)

        assert len(ecrits) > 1, "le préréglage n'a produit aucune variante"
        assert set(ecrits) - set(inscrits) == set()

    def test_aucun_fichier_ecrit_n_echappe_au_registre(self, racine: Path) -> None:
        """Le contrôle décisif, formulé comme la fin visée."""
        ecrits, inscrits = _ecrire_et_relever(racine)

        assert sorted(inscrits) == ecrits

    def test_la_taille_inscrite_est_celle_du_fichier(self, racine: Path) -> None:
        """Une taille fausse rendrait tout quota faux."""
        import forge_mvc_files
        from forge_mvc_images.processing import save_image

        appels: "list[tuple[Any, ...]]" = []
        with patch.object(forge_mvc_files, "record_file",
                          side_effect=lambda *a, **k: appels.append(a)):
            save_image(_Fichier(_octets_jpeg()), category="images")

        chemin, _nom, taille = appels[0][0], appels[0][1], appels[0][2]

        assert taille == (racine / chemin).stat().st_size


# ─────────────────────────────────────────────────────────────────────────────
# Le registre indisponible n'empêche pas d'écrire
# ─────────────────────────────────────────────────────────────────────────────


class TestRegistreIndisponible:

    def test_l_image_est_ecrite_malgre_tout(self, racine: Path) -> None:
        """Faire échouer une sauvegarde parce qu'un registre optionnel n'est pas
        provisionné serait disproportionné."""
        import forge_mvc_files
        from forge_mvc_images.processing import save_image

        def _casse(*a: Any, **k: Any) -> None:
            raise RuntimeError("no such table: forge_files")

        with patch.object(forge_mvc_files, "record_file", side_effect=_casse):
            media = save_image(_Fichier(_octets_jpeg()), category="images")

        assert (racine / media.path).is_file()

    def test_l_echec_est_journalise(
        self, racine: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Se rabattre est acceptable, se taire ne l'est pas."""
        import logging

        import forge_mvc_files
        from forge_mvc_images.processing import save_image

        with patch.object(forge_mvc_files, "record_file",
                          side_effect=RuntimeError("table absente")), \
             caplog.at_level(logging.WARNING, logger="forge.images"):
            save_image(_Fichier(_octets_jpeg()), category="images")

        assert "registre" in caplog.text
        assert "orphelin" in caplog.text


# ─────────────────────────────────────────────────────────────────────────────
# La composition qui détruisait des fichiers
# ─────────────────────────────────────────────────────────────────────────────


class TestCompositionAvecLaPurge:

    def test_une_image_inscrite_n_est_plus_un_orphelin(self, racine: Path) -> None:
        """Le scénario mesuré : un document inscrit, une image écrite par cet
        opt-in, et la purge qui voyait la seconde comme un orphelin."""
        import time

        from forge_mvc_files.orphans import find_orphans

        ecrits, inscrits = _ecrire_et_relever(racine)
        vieux = time.time() - 3 * 24 * 3600
        for chemin in racine.rglob("*"):
            if chemin.is_file():
                os.utime(chemin, (vieux, vieux))

        class _Registre:
            def fetch_all(self, sql: str, params: Any = ()) -> "list[dict[str, Any]]":
                return [{"path": chemin, "id": i} for i, chemin in enumerate(inscrits)]

            def fetch_one(self, sql: str, params: Any = ()) -> "dict[str, Any]":
                return {"total": len(inscrits)}

        rapport = find_orphans(root=racine, db=_Registre())

        assert rapport.on_disk_only == (), (
            f"ces fichiers seraient supprimés par files:orphans --delete : "
            f"{rapport.on_disk_only}")
        assert rapport.files_on_disk == len(ecrits)
