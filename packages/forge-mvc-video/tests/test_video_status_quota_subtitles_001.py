"""`VIDEO-STATUS-UI-001`, `VIDEO-QUOTA-001` et `VIDEO-SUBTITLES-001`.

Trois manques du paquet vidéo, dont deux portent un piège qui ne se voit pas.

- `error_message` porte la sortie d'erreur de ffmpeg, donc les chemins absolus
  du serveur. Un gabarit qui affiche « la raison de l'échec » les publie.
- Les limites par fichier existaient et fonctionnaient ; leur **somme** n'était
  bornée par rien.
- Un fichier de sous-titres est servi au navigateur : ce qui n'est pas du
  WebVTT doit être refusé à l'entrée, pas filtré à la lecture.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from forge_mvc_video.config import VideoConfigError, load_video_config
from forge_mvc_video.quota import (
    VideoQuotaError,
    check_duration_quota,
    check_size_quota,
    library_totals,
)
from forge_mvc_video.status import (
    FINAL_STATUSES,
    PENDING_STATUSES,
    STATUS_LABELS,
    UNKNOWN_LABEL,
    describe_video_status,
)
from forge_mvc_video.storage.repository import (
    STATUS_FAILED,
    STATUS_PROCESSING,
    STATUS_READY,
    STATUS_UPLOADED,
    VALID_STATUSES,
    VideoRepository,
)
from forge_mvc_video.subtitles import (
    MAX_SUBTITLE_BYTES,
    VTT_MIME_TYPE,
    SubtitleError,
    SubtitleTrack,
    normalize_lang,
    store_subtitle,
    subtitle_relpath,
    validate_vtt,
)

#: Sortie d'erreur réelle de ffmpeg : elle porte le chemin absolu du serveur.
FFMPEG_STDERR = (
    "ffmpeg a échoué (code 1) : /srv/monapp/storage/video/2026/06/"
    "3f2b.mov: Invalid data found when processing input"
)


# ------------------------------------------------------- VIDEO-STATUS-UI


class TestVueDEtat:

    @pytest.mark.parametrize("etat", sorted(VALID_STATUSES))
    def test_chaque_etat_connu_a_un_libelle(self, etat: str) -> None:
        """Sinon chaque application réécrit sa table de correspondance."""
        vue = describe_video_status({"status": etat})

        assert vue.label != UNKNOWN_LABEL
        assert vue.public_message

    def test_les_libelles_couvrent_exactement_les_etats(self) -> None:
        assert set(STATUS_LABELS) == VALID_STATUSES

    def test_les_deux_familles_partagent_les_etats(self) -> None:
        assert PENDING_STATUSES | FINAL_STATUSES == VALID_STATUSES
        assert not PENDING_STATUSES & FINAL_STATUSES

    @pytest.mark.parametrize(
        "etat,attendu", [(STATUS_UPLOADED, True), (STATUS_PROCESSING, True),
                         (STATUS_READY, False), (STATUS_FAILED, False)]
    )
    def test_is_pending_repond_a_la_question_de_la_page(
        self, etat: str, attendu: bool
    ) -> None:
        """« Faut il redemander l'état ? »"""
        assert describe_video_status({"status": etat}).is_pending is attendu

    def test_un_etat_inconnu_ne_leve_pas(self) -> None:
        """Une exception ici remplacerait une page dégradée par une page d'erreur."""
        vue = describe_video_status({"status": "zzz"})

        assert vue.label == UNKNOWN_LABEL
        assert vue.is_known is False

    def test_une_ligne_absente_ne_leve_pas(self) -> None:
        assert describe_video_status(None).label == UNKNOWN_LABEL


class TestFuiteDeChemin:
    """Le point qui n'est pas cosmétique."""

    def test_le_detail_technique_est_conserve_pour_l_exploitant(self) -> None:
        vue = describe_video_status(
            {"status": STATUS_FAILED, "error_message": FFMPEG_STDERR}
        )

        assert vue.technical_detail == FFMPEG_STDERR

    def test_le_message_public_ne_porte_aucun_chemin(self) -> None:
        vue = describe_video_status(
            {"status": STATUS_FAILED, "error_message": FFMPEG_STDERR}
        )

        assert "/srv" not in vue.public_message
        assert "ffmpeg" not in vue.public_message.lower()

    def test_la_representation_publique_ne_peut_pas_porter_le_detail(self) -> None:
        """La séparation est portée par le type, non par une consigne.

        Un gabarit ne peut pas afficher par accident un champ qui n'est pas là.
        """
        vue = describe_video_status(
            {"status": STATUS_FAILED, "error_message": FFMPEG_STDERR}
        )

        rendu = str(vue.as_public_dict())
        assert "/srv" not in rendu
        assert "error_message" not in vue.as_public_dict()
        assert "technical_detail" not in vue.as_public_dict()

    def test_le_detail_n_est_lu_qu_en_cas_d_echec(self) -> None:
        vue = describe_video_status(
            {"status": STATUS_READY, "error_message": FFMPEG_STDERR}
        )

        assert vue.technical_detail is None

    def test_la_route_d_etat_ne_rend_pas_le_detail(self) -> None:
        from forge_mvc_video.http import VideoHttpController

        class _Repo:
            def get_by_uuid(self, uuid: str) -> "dict[str, Any] | None":
                return {"id": 1, "uuid": uuid, "status": STATUS_FAILED,
                        "error_message": FFMPEG_STDERR}

        class _Req:
            def route(self, name: str) -> str:
                return "abc"

            def header(self, name: str, default: Any = None) -> Any:
                return default

        controleur = VideoHttpController(
            _Repo(), load_video_config({}), api_token=None  # type: ignore[arg-type]
        )
        reponse = controleur.status(_Req())

        assert reponse.status == 200
        assert b"/srv" not in reponse.body


# ---------------------------------------------------------- VIDEO-QUOTA


class _Repo:
    def __init__(self, videos: int = 0, octets: int = 0, secondes: int = 0) -> None:
        self._totaux = {
            "videos": videos, "total_bytes": octets, "total_duration": secondes
        }

    def totals(self) -> "dict[str, int]":
        return dict(self._totaux)


class _RepoInterdit:
    def totals(self) -> "dict[str, int]":
        raise AssertionError("la base ne doit pas être interrogée")


class TestLimitesParFichierDejaPresentes:
    """Elles existaient avant ce ticket, et le ticket ne les touche pas."""

    def test_la_taille_d_un_fichier_est_bornee_par_defaut(self) -> None:
        assert load_video_config({}).max_upload_mb == 1000

    def test_la_duree_d_un_fichier_est_bornee_par_defaut(self) -> None:
        assert load_video_config({}).max_duration_seconds == 3600


class TestPlafondsCumules:

    def test_rien_n_est_cumule_par_defaut(self) -> None:
        """Le paquet ne borne pas ce que l'exploitant n'a pas demandé."""
        config = load_video_config({})

        assert config.max_total_mb is None
        assert config.max_total_duration_seconds is None

    def test_sans_plafond_la_base_n_est_pas_lue(self) -> None:
        """Un déploiement sans quota ne paye pas une requête par envoi."""
        check_size_quota(10**12, repository=_RepoInterdit(), config=load_video_config({}))
        check_duration_quota(10**9, repository=_RepoInterdit(), config=load_video_config({}))

    def test_un_envoi_qui_tient_passe(self) -> None:
        config = load_video_config({"FORGE_VIDEO_MAX_TOTAL_MB": "1"})

        check_size_quota(100, repository=_Repo(octets=900), config=config)

    def test_un_envoi_qui_deborde_est_refuse(self) -> None:
        """Cinq cents vidéos de 999 Mo passaient chacune le contrôle par fichier."""
        config = load_video_config({"FORGE_VIDEO_MAX_TOTAL_MB": "1"})

        with pytest.raises(VideoQuotaError):
            check_size_quota(2 * 1024 * 1024, repository=_Repo(octets=900), config=config)

    def test_le_message_nomme_la_variable(self) -> None:
        config = load_video_config({"FORGE_VIDEO_MAX_TOTAL_MB": "1"})

        with pytest.raises(VideoQuotaError, match="FORGE_VIDEO_MAX_TOTAL_MB"):
            check_size_quota(10**9, repository=_Repo(octets=900), config=config)

    def test_la_duree_cumulee_se_borne_aussi(self) -> None:
        config = load_video_config({"FORGE_VIDEO_MAX_TOTAL_DURATION_SECONDS": "100"})

        with pytest.raises(VideoQuotaError, match="durée"):
            check_duration_quota(50, repository=_Repo(secondes=80), config=config)

    def test_pile_a_la_limite_passe(self) -> None:
        config = load_video_config({"FORGE_VIDEO_MAX_TOTAL_DURATION_SECONDS": "100"})

        check_duration_quota(20, repository=_Repo(secondes=80), config=config)

    def test_le_restant_ne_devient_jamais_negatif(self) -> None:
        """Un plafond abaissé après coup laisse au dessus."""
        config = load_video_config({"FORGE_VIDEO_MAX_TOTAL_MB": "1"})

        etat = library_totals(repository=_Repo(octets=10**9), config=config)

        assert etat.remaining_bytes == 0

    def test_sans_plafond_le_restant_est_indetermine(self) -> None:
        """Zéro voudrait dire « plus rien », ce qui est le contraire."""
        etat = library_totals(repository=_Repo(octets=10), config=load_video_config({}))

        assert etat.remaining_bytes is None


class TestConfigurationIllisible:

    @pytest.mark.parametrize(
        "cle", ["FORGE_VIDEO_MAX_UPLOAD_MB", "FORGE_VIDEO_MAX_DURATION_SECONDS",
                "FORGE_VIDEO_MAX_TOTAL_MB"]
    )
    def test_une_valeur_illisible_leve(self, cle: str) -> None:
        """Elle retombait en silence sur le défaut.

        `FORGE_VIDEO_MAX_DURATION_SECONDS=7200x` donnait 3600, les vidéos de
        deux heures étaient refusées, et rien n'expliquait pourquoi.
        """
        with pytest.raises(VideoConfigError):
            load_video_config({cle: "7200x"})

    def test_une_valeur_nulle_leve(self) -> None:
        with pytest.raises(VideoConfigError):
            load_video_config({"FORGE_VIDEO_MAX_TOTAL_MB": "0"})

    def test_une_variable_absente_ne_leve_pas(self) -> None:
        assert load_video_config({}).max_total_mb is None


class TestTotauxDuDepot:

    def test_une_table_vide_rend_zero_et_non_nul(self) -> None:
        """`SUM` rend NULL sur une table vide, et un NULL propagé ferait passer
        le premier envoi pour un dépassement."""

        class _Db:
            def fetch_one(self, sql: str, params: Any) -> "dict[str, Any]":
                return {"videos": 0, "total_bytes": None, "total_duration": None}

        assert VideoRepository(_Db()).totals() == {  # type: ignore[arg-type]
            "videos": 0, "total_bytes": 0, "total_duration": 0,
        }


# ------------------------------------------------------ VIDEO-SUBTITLES


class TestEtiquetteDeLangue:

    @pytest.mark.parametrize(
        "brut,attendu", [(" FR ", "fr"), ("en-GB", "en-gb"), ("zh-Hans", "zh-hans")]
    )
    def test_elle_est_normalisee(self, brut: str, attendu: str) -> None:
        """`FR` et `fr` créeraient deux pistes que le lecteur afficherait deux fois."""
        assert normalize_lang(brut) == attendu

    @pytest.mark.parametrize("mauvais", ["", "   ", "../etc", "fr!", "f", "a" * 40])
    def test_une_etiquette_invalide_est_refusee(self, mauvais: str) -> None:
        with pytest.raises(SubtitleError):
            normalize_lang(mauvais)

    def test_le_chemin_ne_prend_rien_de_l_utilisateur(self) -> None:
        """Ni le nom de fichier envoyé, ni rien d'autre : aucune traversée."""
        assert subtitle_relpath("abc-123", "FR") == "subtitles/abc-123/fr.vtt"


class TestValidationWebVtt:

    @pytest.mark.parametrize(
        "contenu",
        [b"WEBVTT\n", b"WEBVTT - Mon film\n", b"WEBVTT\tMon film\n",
         "﻿WEBVTT\n".encode()],
    )
    def test_les_formes_valides_passent(self, contenu: bytes) -> None:
        assert validate_vtt(contenu)

    def test_le_bom_est_retire(self) -> None:
        assert validate_vtt("﻿WEBVTT\n".encode()).startswith("WEBVTT")

    @pytest.mark.parametrize(
        "contenu",
        [b"", b"<html><script>alert(1)</script></html>",
         b"1\n00:00:00,000 --> 00:00:02,000\nDu SRT\n", b"%PDF-1.4"],
    )
    def test_ce_qui_n_est_pas_du_webvtt_est_refuse(self, contenu: bytes) -> None:
        """Le fichier est servi depuis le domaine de l'application.

        Le refuser à l'écriture vaut mieux que de le filtrer à chaque lecture.
        """
        with pytest.raises(SubtitleError):
            validate_vtt(contenu)

    def test_le_message_oriente_celui_qui_a_du_srt(self) -> None:
        with pytest.raises(SubtitleError, match="SRT"):
            validate_vtt(b"1\n00:00:00,000 --> 00:00:02,000\nBonjour\n")

    def test_un_fichier_non_utf8_est_refuse(self) -> None:
        with pytest.raises(SubtitleError, match="UTF-8"):
            validate_vtt(b"\xff\xfe\x00WEBVTT")

    def test_un_fichier_trop_lourd_est_refuse(self) -> None:
        with pytest.raises(SubtitleError, match="trop lourd"):
            validate_vtt(b"WEBVTT\n" + b"x" * MAX_SUBTITLE_BYTES)


class TestEcritureDUnePiste:

    def test_elle_ecrit_sous_la_racine(self, tmp_path: Path) -> None:
        relatif = store_subtitle(b"WEBVTT\n", "abc-123", "fr", storage_root=tmp_path)

        assert (tmp_path / relatif).is_file()
        assert (tmp_path / relatif).read_text(encoding="utf-8") == "WEBVTT\n"

    def test_un_contenu_invalide_n_ecrit_rien(self, tmp_path: Path) -> None:
        with pytest.raises(SubtitleError):
            store_subtitle(b"<html>", "abc-123", "fr", storage_root=tmp_path)

        assert list(tmp_path.rglob("*.vtt")) == []


class TestPisteParDefaut:

    def test_une_seule_piste_par_defaut(self) -> None:
        """Deux pistes par défaut laisseraient le navigateur choisir."""
        appels: list[tuple[str, Any]] = []

        class _Db:
            def insert(self, sql: str, params: Any) -> int:
                appels.append(("insert", params))
                return 1

            def execute(self, sql: str, params: Any) -> int:
                appels.append(("clear", params))
                return 1

        VideoRepository(_Db()).add_subtitle(  # type: ignore[arg-type]
            7, lang="fr", path="x.vtt", is_default=True
        )

        assert appels[0][0] == "clear"

    def test_une_piste_ordinaire_ne_touche_pas_les_autres(self) -> None:
        appels: list[str] = []

        class _Db:
            def insert(self, sql: str, params: Any) -> int:
                appels.append("insert")
                return 1

            def execute(self, sql: str, params: Any) -> int:
                appels.append("clear")
                return 1

        VideoRepository(_Db()).add_subtitle(7, lang="fr", path="x.vtt")  # type: ignore[arg-type]

        assert appels == ["insert"]


class TestPisteRendue:

    def test_l_etiquette_retombe_sur_la_langue(self) -> None:
        assert SubtitleTrack(lang="fr", path="x.vtt").display_label == "fr"

    def test_l_etiquette_donnee_l_emporte(self) -> None:
        piste = SubtitleTrack(lang="fr", path="x.vtt", label="Français")

        assert piste.display_label == "Français"

    def test_le_type_servi_est_celui_qu_exige_la_balise_track(self) -> None:
        assert VTT_MIME_TYPE.startswith("text/vtt")


class TestTableDesSousTitres:

    def test_deux_pistes_de_meme_langue_sont_impossibles(self) -> None:
        """Elles désigneraient la même entrée dans le menu du lecteur."""
        from forge_mvc_video.tables import VIDEO_SUBTITLES

        noms = {c.name for c in VIDEO_SUBTITLES.columns}
        contraintes = {
            tuple(c.columns) if isinstance(c.columns, tuple) else (c.columns,)
            for c in VIDEO_SUBTITLES.unique_constraints
        }

        assert {"video_id", "lang", "path", "is_default"} <= noms
        assert ("video_id", "lang") in contraintes

    def test_la_migration_est_declaree(self) -> None:
        from forge_mvc_video.tables import MIGRATIONS, VIDEO_SUBTITLES

        assert any(table is VIDEO_SUBTITLES for _, table in MIGRATIONS)


class TestRoutes:

    def test_les_trois_routes_sont_enregistrees(self) -> None:
        from forge_mvc_video.http import (
            ROUTE_PLAYBACK,
            ROUTE_STATUS,
            ROUTE_SUBTITLE,
            register_video_routes,
        )

        posees: list[tuple[str, str]] = []

        class _Router:
            def add(self, methode: str, chemin: str, handler: Any, **kw: Any) -> None:
                posees.append((methode, chemin))

        class _Repo:
            pass

        register_video_routes(
            _Router(), repository=_Repo(), config=load_video_config({})  # type: ignore[arg-type]
        )

        assert ("GET", ROUTE_PLAYBACK) in posees
        assert ("GET", ROUTE_STATUS) in posees
        assert ("GET", ROUTE_SUBTITLE) in posees

    def test_la_route_de_sous_titres_est_protegee_comme_la_lecture(self) -> None:
        """Une piste dit ce que la vidéo raconte."""
        from forge_mvc_video.http import VideoHttpController

        class _Req:
            def route(self, name: str) -> str:
                return "abc"

            def header(self, name: str, default: Any = None) -> Any:
                return default

        controleur = VideoHttpController(
            object(), load_video_config({}), api_token="secret"  # type: ignore[arg-type]
        )

        assert controleur.subtitle(_Req()).status == 401
        assert controleur.status(_Req()).status == 401
