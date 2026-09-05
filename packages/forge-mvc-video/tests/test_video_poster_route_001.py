"""`VIDEO-POSTER-ROUTE-001` — la vignette est servable, les métadonnées lisibles.

Le poster de première image est engendré au transcodage et inscrit en base
depuis la livraison du paquet. **Aucune route ne le servait**, et la réponse
d'état ne le mentionnait pas.

Les métadonnées sondées, durée, largeur et hauteur, étaient dans la même
situation : trois colonnes remplies, et rien pour les lire.

Une interface qui sonde `/videos/<uuid>/status` pour savoir quand afficher
n'avait donc ni vignette, ni durée, ni dimensions. Elle devait interroger la
base par un chemin qu'un client n'a pas, ou l'application réécrire une route en
refaisant la résolution anti-traversal que `stream` porte déjà.

## `poster_path` n'est pas rendu, et c'est délibéré

C'est un chemin de **stockage**, pas une URL. Le rendre publierait
l'arborescence du serveur, ce que cette classe évite ailleurs avec soin :
`technical_detail` en est absent par construction pour la même raison.

Un booléen dit qu'une vignette existe, et la route la sert.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("forge_mvc_video")

from forge_mvc_video.http import (  # noqa: E402
    ROUTE_POSTER,
    ROUTE_STATUS,
    VideoHttpController,
    register_video_routes,
)
from forge_mvc_video.status import describe_video_status  # noqa: E402


class _Repo:
    def __init__(self, row: "dict[str, Any] | None") -> None:
        self._row = row

    def get_by_uuid(self, uuid: str) -> "dict[str, Any] | None":
        return self._row


class _Config:
    def __init__(self, racine: Path) -> None:
        self.storage_root = str(racine)
        self.api_token = None


class _Req:
    def __init__(self, uuid: str = "abc") -> None:
        self._uuid = uuid
        self.headers: "dict[str, str]" = {}

    def route(self, nom: str) -> Any:
        return self._uuid if nom == "uuid" else None

    def header(self, nom: str, defaut: Any = None) -> Any:
        return self.headers.get(nom, defaut)


def _controleur(racine: Path, row: "dict[str, Any] | None") -> VideoHttpController:
    return VideoHttpController(_Repo(row), _Config(racine), api_token=None)


# ─────────────────────────────────────────────────────────────────────────────
# La vignette est servable
# ─────────────────────────────────────────────────────────────────────────────


class TestRoutePoster:

    def test_elle_sert_la_vignette(self, tmp_path: Path) -> None:
        """Le cas qui n'existait pas."""
        vignette = tmp_path / "poster" / "abc.jpg"
        vignette.parent.mkdir(parents=True)
        vignette.write_bytes(b"\xff\xd8\xff")

        reponse = _controleur(tmp_path, {
            "uuid": "abc", "status": "ready", "poster_path": "poster/abc.jpg",
        }).poster(_Req())

        assert reponse.status == 200

    def test_une_video_sans_vignette_rend_409(self, tmp_path: Path) -> None:
        """Pas encore transcodée, ou transcodage en échec. Un 404 ferait croire
        à une vidéo inconnue, ce qui envoie chercher au mauvais endroit."""
        reponse = _controleur(tmp_path, {
            "uuid": "abc", "status": "processing", "poster_path": None,
        }).poster(_Req())

        assert reponse.status == 409

    def test_une_video_inconnue_rend_404(self, tmp_path: Path) -> None:
        assert _controleur(tmp_path, None).poster(_Req()).status == 404

    def test_un_fichier_absent_rend_404(self, tmp_path: Path) -> None:
        reponse = _controleur(tmp_path, {
            "uuid": "abc", "status": "ready", "poster_path": "poster/disparu.jpg",
        }).poster(_Req())

        assert reponse.status == 404


class TestAntiTraversal:
    """Même garde que `stream` : le chemin vient de la base, jamais de l'URL,
    et il est revalidé sous `storage_root`. Une ligne corrompue ou écrite par un
    autre composant ne doit pas permettre de sortir du dossier."""

    @pytest.mark.parametrize(
        "chemin", ["../../../etc/passwd", "/etc/passwd", "poster/../../secret.jpg"],
        ids=["relatif", "absolu", "remontee-interne"],
    )
    def test_un_chemin_hors_racine_est_refuse(
        self, tmp_path: Path, chemin: str
    ) -> None:
        reponse = _controleur(tmp_path, {
            "uuid": "abc", "status": "ready", "poster_path": chemin,
        }).poster(_Req())

        assert reponse.status == 404

    def test_le_refus_ne_dit_pas_pourquoi(self, tmp_path: Path) -> None:
        """Distinguer « hors racine » de « absent » apprendrait à l'appelant ce
        que contient le disque."""
        hors = _controleur(tmp_path, {
            "uuid": "a", "status": "ready", "poster_path": "../secret.jpg"}).poster(_Req())
        absent = _controleur(tmp_path, {
            "uuid": "a", "status": "ready", "poster_path": "poster/x.jpg"}).poster(_Req())

        assert hors.status == absent.status == 404


# ─────────────────────────────────────────────────────────────────────────────
# Les métadonnées accompagnent l'état
# ─────────────────────────────────────────────────────────────────────────────


class TestMetadonneesExposees:

    def _vue(self, **row: Any) -> "dict[str, Any]":
        return describe_video_status(row).as_public_dict()

    def test_la_duree_et_les_dimensions_sont_rendues(self) -> None:
        rendu = self._vue(status="ready", duration_seconds=187,
                          width=1920, height=1080, poster_path="poster/a.jpg")

        assert rendu["duration_seconds"] == 187
        assert (rendu["width"], rendu["height"]) == (1920, 1080)

    def test_la_presence_d_une_vignette_est_dite(self) -> None:
        assert self._vue(status="ready", poster_path="poster/a.jpg")["has_poster"]
        assert not self._vue(status="processing", poster_path=None)["has_poster"]

    def test_le_chemin_de_stockage_n_est_jamais_rendu(self) -> None:
        """C'est un chemin de stockage, pas une URL : le rendre publierait
        l'arborescence du serveur."""
        rendu = self._vue(status="ready", poster_path="poster/abc.jpg")

        assert "poster_path" not in rendu
        assert "poster/abc.jpg" not in str(rendu)

    def test_la_sortie_de_ffmpeg_ne_sort_toujours_pas(self) -> None:
        """La garde d'origine ne doit pas avoir été affaiblie par l'ajout."""
        rendu = self._vue(status="failed",
                          error_message="ffmpeg: /srv/monapp/storage/video/a.mov")

        assert "/srv/" not in str(rendu)
        assert "technical_detail" not in rendu

    def test_une_metadonnee_absente_n_apparait_pas(self) -> None:
        """Rendre `null` ferait afficher « durée : null » à une interface qui
        ne teste que la présence de la clé."""
        rendu = self._vue(status="processing")

        assert "duration_seconds" not in rendu
        assert "width" not in rendu

    @pytest.mark.parametrize("valeur", ["187", None, "", "abc", True])
    def test_une_valeur_illisible_ne_leve_pas(self, valeur: Any) -> None:
        """Une ligne peut porter une chaîne venue d'un pilote. Lever ici
        remplacerait une page par une erreur, alors que le contrat de cette
        vue est de toujours pouvoir afficher quelque chose."""
        rendu = self._vue(status="ready", duration_seconds=valeur)

        assert rendu["status"] == "ready"


# ─────────────────────────────────────────────────────────────────────────────
# La route est câblée
# ─────────────────────────────────────────────────────────────────────────────


class TestRouteCablee:
    """Une route qui existe sans être posée ne sert personne : c'est le défaut
    que ce ticket corrige, il ne doit pas revenir sous une autre forme."""

    def _routes(self, tmp_path: Path) -> "list[tuple[str, str, dict[str, Any]]]":
        posees: "list[tuple[str, str, dict[str, Any]]]" = []

        class _Router:
            def add(self, methode: str, chemin: str, handler: Any, **kw: Any) -> None:
                posees.append((methode, chemin, kw))

        register_video_routes(
            _Router(), config=_Config(tmp_path), repository=_Repo(None))
        return posees

    def test_la_route_poster_est_posee(self, tmp_path: Path) -> None:
        assert ("GET", ROUTE_POSTER) in [(m, c) for m, c, _ in self._routes(tmp_path)]

    def test_elle_ne_capture_pas_la_route_d_etat(self, tmp_path: Path) -> None:
        """`/videos/{uuid}/poster` et `/videos/{uuid}/status` sont deux
        littéraux distincts : ni l'un ni l'autre ne doit prendre la place de
        l'autre."""
        chemins = [c for _, c, _ in self._routes(tmp_path)]

        assert ROUTE_STATUS in chemins
        assert ROUTE_POSTER in chemins
        assert ROUTE_POSTER != ROUTE_STATUS
