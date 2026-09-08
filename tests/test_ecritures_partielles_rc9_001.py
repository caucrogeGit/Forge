"""Six défauts d'écriture partielle, de reprise et de garde.

Dernière famille de la revue externe des 27 opt-ins. Le fil commun est qu'une
opération réussit à moitié, ou qu'une garde regarde à côté :

- `images` : une sélection de variantes levait après avoir écrit des fichiers.
- `files` : une suppression aboutissait, puis levait, sans nettoyer le registre.
- `settings` : le cache était vidé avant l'écriture, donc rechargé périmé.
- `video` : une reprise recomptait sa propre durée dans le quota.
- `audio` : le chemin servi n'était pas vérifié comme descendant de la racine.
- `iot` : le garde de démarrage ignorait le mode d'authentification par jetons.
"""
from __future__ import annotations

import io
import os
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

import pytest


class TestImagesSelectionDeVariantes:
    """`IMAGES-VARIANTES-SELECTION-001` — l'API rend ce qu'elle a produit."""

    @staticmethod
    def _png() -> bytes:
        Image = pytest.importorskip("PIL.Image")
        tampon = io.BytesIO()
        Image.new("RGB", (400, 300)).save(tampon, format="PNG")
        return tampon.getvalue()

    @pytest.mark.parametrize(
        ("selection", "attendu"),
        [
            (["thumbnail"], {"thumbnail"}),
            (["medium"], {"medium"}),
            (["medium", "thumbnail"], {"medium", "thumbnail"}),
            (True, {"medium", "thumbnail"}),
        ],
        ids=["une-seule", "l-autre", "les-deux", "par-defaut"],
    )
    def test_les_variantes_rendues_sont_celles_produites(self, selection, attendu) -> None:
        """`variants=["thumbnail"]` levait `KeyError('medium')` après avoir écrit."""
        pytest.importorskip("forge_mvc_images")
        from forge_mvc_images.processing import save_image_upload

        televerse = SimpleNamespace(
            filename="t.png", content=self._png(), content_type="image/png"
        )
        with tempfile.TemporaryDirectory() as racine, patch.dict(
            os.environ, {"UPLOAD_ROOT": racine}
        ):
            enregistre = save_image_upload(televerse, variants=selection)

        assert set(enregistre.variants) == attendu

    def test_l_original_n_est_pas_une_variante(self) -> None:
        """`saved.path` le porte déjà : l'ajouter le ferait afficher en double."""
        pytest.importorskip("forge_mvc_images")
        from forge_mvc_images.processing import save_image_upload

        televerse = SimpleNamespace(
            filename="t.png", content=self._png(), content_type="image/png"
        )
        with tempfile.TemporaryDirectory() as racine, patch.dict(
            os.environ, {"UPLOAD_ROOT": racine}
        ):
            enregistre = save_image_upload(televerse, variants=True)

        assert "original" not in enregistre.variants


class TestFilesOrdreDeSuppression:
    """`FILES-DELETE-ORDRE-001` — rien n'est supprimé avant d'être accepté."""

    @pytest.fixture
    def racine(self):
        with tempfile.TemporaryDirectory() as chemin, patch.dict(
            os.environ, {"UPLOAD_ROOT": chemin}
        ):
            (Path(chemin) / "images").mkdir()
            yield Path(chemin)

    @pytest.mark.parametrize("forme", ["relatif", "absolu"])
    def test_les_deux_formes_internes_aboutissent(self, forme: str, racine: Path) -> None:
        """Un chemin absolu interne faisait supprimer **puis** lever."""
        pytest.importorskip("forge_mvc_files")
        from forge_mvc_files.manager import delete_upload

        fichier = racine / "images" / "a.txt"
        fichier.write_text("x", encoding="utf-8")
        entree = "images/a.txt" if forme == "relatif" else str(fichier)

        assert delete_upload(entree) is True
        assert not fichier.exists()

    def test_un_chemin_externe_est_refuse_sans_rien_supprimer(self, racine: Path) -> None:
        pytest.importorskip("forge_mvc_files")
        from core.forms.upload_exceptions import UploadStorageError
        from forge_mvc_files.manager import delete_upload

        with tempfile.TemporaryDirectory() as ailleurs:
            dehors = Path(ailleurs) / "hors.txt"
            dehors.write_text("y", encoding="utf-8")

            with pytest.raises(UploadStorageError):
                delete_upload(str(dehors))

            assert dehors.exists(), "un refus ne doit rien avoir supprimé"


class TestVideoQuotaDeReprise:
    """`VIDEO-QUOTA-REPRISE-001` — une reprise ne se compte pas deux fois."""

    @staticmethod
    def _depot(total: int):
        return SimpleNamespace(totals=lambda: {"videos": 1, "total_bytes": 1, "total_duration": total})

    def test_une_reprise_ne_recompte_pas_sa_propre_duree(self) -> None:
        """60 s déjà comptées, plafond 60 : la reprise était refusée à 120."""
        pytest.importorskip("forge_mvc_video")
        from forge_mvc_video.config import VideoConfig
        from forge_mvc_video.quota import check_duration_quota

        check_duration_quota(
            60,
            repository=self._depot(60),
            config=VideoConfig(storage_root="/tmp", max_total_duration_seconds=60),
            already_counted_seconds=60,
        )

    def test_une_video_neuve_est_toujours_comptee(self) -> None:
        """Une garde qui ne compterait plus rien ne protégerait rien non plus."""
        pytest.importorskip("forge_mvc_video")
        from forge_mvc_video.config import VideoConfig
        from forge_mvc_video.quota import VideoQuotaError, check_duration_quota

        with pytest.raises(VideoQuotaError):
            check_duration_quota(
                60,
                repository=self._depot(60),
                config=VideoConfig(storage_root="/tmp", max_total_duration_seconds=60),
            )

    def test_une_reprise_plus_longue_reste_refusee(self) -> None:
        """La vidéo a été remplacée par une plus longue : le delta compte."""
        pytest.importorskip("forge_mvc_video")
        from forge_mvc_video.config import VideoConfig
        from forge_mvc_video.quota import VideoQuotaError, check_duration_quota

        with pytest.raises(VideoQuotaError):
            check_duration_quota(
                120,
                repository=self._depot(60),
                config=VideoConfig(storage_root="/tmp", max_total_duration_seconds=60),
                already_counted_seconds=60,
            )


class TestAudioConfinement:
    """`AUDIO-CONFINEMENT-CHEMIN-001` — le chemin servi descend de la racine."""

    def test_un_lien_hors_racine_n_est_pas_servi(self) -> None:
        """Il était servi avec un statut 200, sur un UUID pourtant valide."""
        pytest.importorskip("forge_mvc_audio")
        from forge_mvc_audio.config import AudioConfig
        from forge_mvc_audio.http import AudioHttpController

        with tempfile.TemporaryDirectory() as base:
            racine = Path(base) / "audio"
            identifiant = str(uuid4())
            dossier = racine / "transcoded" / identifiant
            dossier.mkdir(parents=True)
            dehors = Path(base) / "dehors.txt"
            dehors.write_bytes(b"CONTENU HORS RACINE")
            (dossier / "audio.mp3").symlink_to(dehors)

            requete = SimpleNamespace(
                route=lambda cle: identifiant,
                headers={},
                header=lambda cle, defaut=None: defaut,
            )
            reponse = AudioHttpController(AudioConfig(storage_root=str(racine))).stream(requete)

        assert reponse.status == 404

    def test_un_fichier_reel_dans_la_racine_est_servi(self) -> None:
        """Une garde qui refuserait tout ne servirait plus rien."""
        pytest.importorskip("forge_mvc_audio")
        from forge_mvc_audio.config import AudioConfig
        from forge_mvc_audio.http import AudioHttpController

        with tempfile.TemporaryDirectory() as base:
            racine = Path(base) / "audio"
            identifiant = str(uuid4())
            dossier = racine / "transcoded" / identifiant
            dossier.mkdir(parents=True)
            (dossier / "audio.mp3").write_bytes(b"ID3 contenu interne")

            requete = SimpleNamespace(
                route=lambda cle: identifiant,
                headers={},
                header=lambda cle, defaut=None: defaut,
            )
            reponse = AudioHttpController(AudioConfig(storage_root=str(racine))).stream(requete)

        assert reponse.status == 200


class TestIotGardeDeDemarrage:
    """`IOT-GARDE-DEMARRAGE-JETONS-001` — un moyen d'authentification, quel qu'il soit."""

    @pytest.fixture
    def en_production(self):
        from core import forge

        precedent = forge.get("app_env")
        forge.configure(app_env="prod")
        yield
        forge.configure(app_env=precedent)

    def test_des_jetons_scopes_seuls_suffisent(self, en_production) -> None:
        """Le démarrage était refusé alors qu'un registre de jetons était fourni."""
        pytest.importorskip("forge_mvc_iot")
        from forge_mvc_iot.http import register_iot_routes

        register_iot_routes(
            SimpleNamespace(add=lambda *a, **k: None),
            repository=object(),
            config=SimpleNamespace(api_token=None),
            token_repository=object(),
        )

    def test_aucun_moyen_reste_refuse(self, en_production) -> None:
        """C'est la garantie pour laquelle ce garde existe."""
        pytest.importorskip("forge_mvc_iot")
        from forge_mvc_iot.http import register_iot_routes

        with pytest.raises(RuntimeError, match="ouverte interdite en production"):
            register_iot_routes(
                SimpleNamespace(add=lambda *a, **k: None),
                repository=object(),
                config=SimpleNamespace(api_token=None),
            )

    def test_le_message_nomme_les_trois_issues(self, en_production) -> None:
        pytest.importorskip("forge_mvc_iot")
        from forge_mvc_iot.http import register_iot_routes

        with pytest.raises(RuntimeError) as capture:
            register_iot_routes(
                SimpleNamespace(add=lambda *a, **k: None),
                repository=object(),
                config=SimpleNamespace(api_token=None),
            )

        message = str(capture.value)
        assert "FORGE_IOT_API_TOKEN" in message
        assert "token_repository" in message
        assert "développement" in message
