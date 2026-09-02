"""`AUDIO-ID3-001`, `AUDIO-TRIM-001` et `AUDIO-DOCTOR-HARMONISE-001`.

Deux manques réels et un faux besoin.

`ffprobe` rendait déjà les étiquettes du fichier, le paquet les jetait. Elles
viennent pourtant du fichier **envoyé**, et finissent affichées dans une page :
les nettoyer est le vrai sujet du ticket.

La découpe n'existait pas, et il fallait rappeler `ffmpeg` à la main, donc
réécrire le durcissement des arguments.

`audio:doctor` était **déjà** aligné sur `video:doctor`. Le ticket livre le
garde-fou qui manquait pour que les deux ne divergent plus, et corrige la
divergence réelle qu'il a fait apparaître : la configuration audio retombait en
silence sur ses défauts.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from forge_mvc_audio.config import AudioConfigError, load_audio_config
from forge_mvc_audio.probe import parse_probe_json
from forge_mvc_audio.tags import (
    MAX_TAG_LENGTH,
    AudioTags,
    clean_tag_value,
    parse_tags,
)
from forge_mvc_audio.transcode import FfmpegError, safe_path_arg
from forge_mvc_audio.trim import (
    AudioTrimError,
    build_trim_command,
    format_timecode,
    parse_timecode,
    trim_audio,
)


# ------------------------------------------------------------- AUDIO-ID3


class TestLectureDesEtiquettes:

    def test_le_titre_et_l_artiste_sont_lus(self) -> None:
        tags = parse_tags({"format": {"tags": {"title": "Le Sacre", "artist": "S"}}})

        assert tags.title == "Le Sacre"
        assert tags.artist == "S"

    @pytest.mark.parametrize(
        "cle", ["TITLE", "Title", "title", "tit2"]
    )
    def test_la_casse_et_les_alias_sont_absorbes(self, cle: str) -> None:
        """ID3 dit `tit2`, Vorbis dit `TITLE`, et la casse varie."""
        assert parse_tags({"format": {"tags": {cle: "X"}}}).title == "X"

    def test_les_etiquettes_du_flux_servent_de_repli(self) -> None:
        """Un conteneur comme le WAV ne porte pas de bloc de format."""
        tags = parse_tags(
            {"streams": [{"codec_type": "audio", "tags": {"title": "X"}}]}
        )

        assert tags.title == "X"

    def test_le_format_l_emporte_sur_le_flux(self) -> None:
        tags = parse_tags({
            "streams": [{"codec_type": "audio", "tags": {"title": "flux"}}],
            "format": {"tags": {"title": "format"}},
        })

        assert tags.title == "format"

    def test_l_annee_est_extraite_d_une_date_complete(self) -> None:
        assert parse_tags({"format": {"tags": {"date": "2019-05-01T00:00:00Z"}}}).year == 2019

    @pytest.mark.parametrize("date", ["0090", "90210", "sans date"])
    def test_une_annee_implausible_est_ecartee(self, date: str) -> None:
        """Afficher « année 20 » vaut moins que ne rien afficher."""
        assert parse_tags({"format": {"tags": {"date": date}}}).year is None

    def test_la_piste_sur_total_est_decoupee(self) -> None:
        tags = parse_tags({"format": {"tags": {"track": "3/12"}}})

        assert (tags.track_number, tags.track_total) == (3, 12)

    def test_une_piste_seule_n_invente_pas_de_total(self) -> None:
        tags = parse_tags({"format": {"tags": {"track": "3"}}})

        assert (tags.track_number, tags.track_total) == (3, None)

    def test_un_total_inferieur_au_numero_est_ecarte(self) -> None:
        """« piste 5 sur 2 » est une saisie fausse, pas une information."""
        tags = parse_tags({"format": {"tags": {"track": "5/2"}}})

        assert (tags.track_number, tags.track_total) == (5, None)


class TestNettoyageDesEtiquettes:
    """Le vrai sujet : une étiquette vient du fichier envoyé."""

    @pytest.mark.parametrize(
        "brut", ["a\nb", "a\rb", "a b", "a b", "a\tb"]
    )
    def test_les_sauts_de_ligne_sont_retires(self, brut: str) -> None:
        """Un saut de ligne dans un titre casse un en-tête HTTP.

        `U+2028` casse en plus une chaîne JavaScript, et `str.strip` le laisse
        passer.
        """
        nettoye = clean_tag_value(brut)

        assert nettoye == "a b"

    def test_la_longueur_est_bornee(self) -> None:
        """Rien n'empêche un titre d'un mégaoctet, qui n'est pas un titre."""
        assert len(clean_tag_value("x" * 10**6) or "") == MAX_TAG_LENGTH

    def test_rien_n_est_echappe(self) -> None:
        """L'échappement appartient au gabarit ; le faire deux fois afficherait
        `&amp;amp;`."""
        assert clean_tag_value("Tom & Jerry <3") == "Tom & Jerry <3"

    @pytest.mark.parametrize("vide", [None, "", "   ", "\n\n"])
    def test_une_etiquette_vide_devient_none(self, vide: Any) -> None:
        assert clean_tag_value(vide) is None

    def test_un_alias_vide_laisse_place_au_suivant(self) -> None:
        tags = parse_tags({"format": {"tags": {"title": "  ", "tit2": "Vrai"}}})

        assert tags.title == "Vrai"


class TestAbsenceDEtiquettes:

    def test_un_fichier_sans_etiquette_n_est_pas_une_erreur(self) -> None:
        """Le cas courant d'un enregistrement brut, ou d'un fichier transcodé
        par le paquet, qui pose `-map_metadata -1`."""
        assert parse_tags({"format": {}}).is_empty

    @pytest.mark.parametrize("charge", [None, "texte", 42, []])
    def test_une_charge_illisible_ne_leve_pas(self, charge: Any) -> None:
        """Une exception ici ferait échouer un envoi parfaitement valide."""
        assert parse_tags(charge).is_empty

    def test_le_sondage_rend_toujours_des_etiquettes(self) -> None:
        """Jamais `None` : l'appelant n'a pas à tester avant de lire."""
        meta = parse_probe_json(
            {"streams": [{"codec_type": "audio"}], "format": {}}
        )

        assert isinstance(meta.tags, AudioTags)
        assert meta.tags.is_empty

    def test_le_sondage_expose_les_etiquettes_lues(self) -> None:
        meta = parse_probe_json({
            "streams": [{"codec_type": "audio", "codec_name": "mp3"}],
            "format": {"duration": "182.5", "tags": {"title": "T"}},
        })

        assert meta.duration_seconds == 182
        assert meta.tags.title == "T"


class TestTitreAffichable:

    def test_l_artiste_precede_le_titre(self) -> None:
        assert AudioTags(title="T", artist="A").display_title == "A - T"

    def test_le_titre_seul_suffit(self) -> None:
        assert AudioTags(title="T").display_title == "T"

    def test_sans_rien_il_n_y_a_rien_a_afficher(self) -> None:
        assert AudioTags().display_title is None


# ------------------------------------------------------------ AUDIO-TRIM


class TestFormatDeTemps:

    @pytest.mark.parametrize(
        "brut,attendu",
        [("90", 90.0), ("1:30", 90.0), ("0:01:30.5", 90.5), ("01:00:00", 3600.0),
         ("0", 0.0), ("12.25", 12.25)],
    )
    def test_les_trois_formes_sont_lues(self, brut: str, attendu: float) -> None:
        assert parse_timecode(brut) == attendu

    @pytest.mark.parametrize(
        "mauvais", ["", "   ", "-5", "abc", "1:2:3:4", "1:70", "1:70:00", "::"]
    )
    def test_une_forme_invalide_est_refusee(self, mauvais: str) -> None:
        with pytest.raises(AudioTrimError):
            parse_timecode(mauvais)

    def test_le_message_dit_les_formes_attendues(self) -> None:
        with pytest.raises(AudioTrimError, match="HH:MM:SS"):
            parse_timecode("abc")

    def test_le_rendu_est_sans_ambiguite_pour_ffmpeg(self) -> None:
        assert format_timecode(90.5) == "00:01:30.500"
        assert format_timecode(3661) == "01:01:01.000"


class TestCommandeConstruite:

    def test_ss_precede_i(self) -> None:
        """Sinon ffmpeg décode tout ce qui précède l'instant demandé.

        Sur un long fichier, cela change une découpe immédiate en plusieurs
        minutes de travail.
        """
        commande = build_trim_command("ffmpeg", "a.mp3", "b.mp3", start=90)

        assert commande.index("-ss") < commande.index("-i")

    def test_sans_fin_aucune_borne_haute(self) -> None:
        assert "-to" not in build_trim_command("ffmpeg", "a.mp3", "b.mp3")

    def test_par_defaut_les_flux_sont_copies(self) -> None:
        commande = build_trim_command("ffmpeg", "a.mp3", "b.mp3")

        assert "-c" in commande and "copy" in commande

    def test_le_reencodage_se_demande(self) -> None:
        commande = build_trim_command("ffmpeg", "a.mp3", "b.mp3", reencode=True)

        assert "libmp3lame" in commande
        assert "copy" not in commande

    @pytest.mark.parametrize("chemin", ["-evil.mp3", "--rm-rf"])
    def test_un_chemin_en_tiret_est_durci(self, chemin: str) -> None:
        """Il serait sinon lu comme une option ffmpeg."""
        commande = build_trim_command("ffmpeg", chemin, chemin)

        assert commande[commande.index("-i") + 1] == f"./{chemin}"
        assert commande[-1] == f"./{chemin}"

    def test_le_durcissement_est_celui_du_transcodage(self) -> None:
        """Une seconde copie divergerait le jour où l'une serait corrigée."""
        assert safe_path_arg("-x") == "./-x"
        assert safe_path_arg("/abs/x") == "/abs/x"


class TestRefusDeDecoupe:

    @pytest.fixture
    def source(self, tmp_path: Path) -> Path:
        chemin = tmp_path / "source.mp3"
        chemin.write_bytes(b"pas vraiment du mp3")
        return chemin

    def test_une_source_absente_est_refusee(self, tmp_path: Path) -> None:
        with pytest.raises(AudioTrimError, match="introuvable"):
            trim_audio(str(tmp_path / "absent.mp3"), str(tmp_path / "out.mp3"))

    def test_la_sortie_ne_peut_pas_etre_la_source(self, source: Path) -> None:
        """ffmpeg lit et écrit en même temps : le fichier serait tronqué."""
        with pytest.raises(AudioTrimError, match="ne peut pas être la source"):
            trim_audio(str(source), str(source))

    def test_le_meme_fichier_ecrit_autrement_est_reconnu(self, source: Path) -> None:
        """`a.mp3` et `./a.mp3` désignent le même fichier."""
        with pytest.raises(AudioTrimError, match="ne peut pas être la source"):
            trim_audio(str(source), f"{source.parent}/./{source.name}")

    def test_une_sortie_existante_n_est_pas_ecrasee(self, source: Path) -> None:
        """Mode « Forge génère » de la charte, write-if-new."""
        cible = source.parent / "deja.mp3"
        cible.write_bytes(b"contenu precieux")

        with pytest.raises(AudioTrimError, match="existe déjà"):
            trim_audio(str(source), str(cible))

        assert cible.read_bytes() == b"contenu precieux"

    def test_l_ecrasement_se_demande(self, source: Path) -> None:
        cible = source.parent / "deja.mp3"
        cible.write_bytes(b"x")
        appels: list[list[str]] = []

        def _faux(cmd: list[str], timeout: int) -> "tuple[int, str]":
            appels.append(cmd)
            return (0, "")

        trim_audio(str(source), str(cible), overwrite=True, runner=_faux)

        assert len(appels) == 1

    def test_un_intervalle_renverse_est_refuse(self, source: Path) -> None:
        """ffmpeg écrirait un fichier de zéro seconde sans se plaindre."""
        with pytest.raises(AudioTrimError, match="renversé"):
            trim_audio(str(source), str(source.parent / "o.mp3"), start=60, end=30)

    def test_un_intervalle_vide_est_refuse(self, source: Path) -> None:
        with pytest.raises(AudioTrimError):
            trim_audio(str(source), str(source.parent / "o.mp3"), start=30, end=30)

    def test_un_echec_ffmpeg_est_remonte(self, source: Path) -> None:
        def _echoue(cmd: list[str], timeout: int) -> "tuple[int, str]":
            return (1, "Invalid data found")

        with pytest.raises(FfmpegError, match="Invalid data"):
            trim_audio(str(source), str(source.parent / "o.mp3"), runner=_echoue)


class TestCommandeCli:

    def test_deux_chemins_sont_exiges(self) -> None:
        from forge_mvc_audio.cli.trim import parse_options

        assert parse_options(["une_seule.mp3"]).error is not None

    def test_une_option_inconnue_est_une_erreur(self) -> None:
        from forge_mvc_audio.cli.trim import parse_options

        assert parse_options(["a", "b", "--frome", "1"]).error is not None

    @pytest.mark.parametrize(
        "argv",
        [["a", "b", "--from", "1:30"], ["a", "b", "--from=1:30"],
         ["a", "b", "--start", "1:30"]],
    )
    def test_les_ecritures_d_option_sont_lues(self, argv: list[str]) -> None:
        from forge_mvc_audio.cli.trim import parse_options

        assert parse_options(argv).debut == "1:30"

    def test_un_instant_illisible_est_une_erreur(self) -> None:
        from forge_mvc_audio.cli.trim import parse_options

        assert parse_options(["a", "b", "--from", "abc"]).error is not None

    def test_un_intervalle_renverse_est_refuse_avant_ffmpeg(self) -> None:
        from forge_mvc_audio.cli.trim import parse_options

        assert parse_options(["a", "b", "--from", "60", "--to", "30"]).error is not None


# ------------------------------------------------- AUDIO-DOCTOR-HARMONISE


class TestDoctorsAlignes:
    """Faux besoin mesuré : les deux doctors étaient déjà alignés.

    Le ticket livre le garde-fou qui manquait, pour qu'une évolution de l'un
    ne fasse pas diverger l'autre en silence.
    """

    def test_les_deux_partagent_leur_contrat_de_sortie(self) -> None:
        from forge_mvc_audio.cli.doctor import CheckResult as AudioResult
        from forge_mvc_video.cli.doctor import CheckResult as VideoResult

        assert (
            {champ.name for champ in AudioResult.__dataclass_fields__.values()}
            == {champ.name for champ in VideoResult.__dataclass_fields__.values()}
        )

    def test_les_deux_exposent_exactement_la_meme_surface(self) -> None:
        """À la migration près, que l'audio n'a pas : il est sans état.

        L'égalité stricte est délibérée. Une inclusion laisserait l'un des deux
        gagner un contrôle sans que l'autre s'en aperçoive, ce que ce garde-fou
        existe précisément pour empêcher.
        """
        from forge_mvc_audio.cli import doctor as audio_doctor
        from forge_mvc_video.cli import doctor as video_doctor

        assert set(video_doctor.__all__) - set(audio_doctor.__all__) == {
            "check_migration_present"
        }
        assert set(audio_doctor.__all__) - set(video_doctor.__all__) == set()

    def test_les_deux_emploient_les_memes_statuts(self) -> None:
        from forge_mvc_audio.cli.doctor import run_all as audio_run
        from forge_mvc_video.cli.doctor import run_all as video_run

        statuts = {"ok", "warn", "fail", "skip"}
        assert {r.status for r in audio_run()} <= statuts
        assert {r.status for r in video_run()} <= statuts


class TestConfigurationAlignee:
    """La divergence réelle, que la comparaison a fait apparaître."""

    @pytest.mark.parametrize(
        "cle", ["FORGE_AUDIO_MAX_UPLOAD_MB", "FORGE_AUDIO_MAX_DURATION_SECONDS"]
    )
    def test_une_valeur_illisible_leve(self, cle: str) -> None:
        """Elle retombait sur le défaut en silence, comme le faisait la vidéo.

        Les fichiers au delà étaient refusés, et rien ne l'expliquait.
        """
        with pytest.raises(AudioConfigError):
            load_audio_config({cle: "7200x"})

    def test_une_valeur_nulle_leve(self) -> None:
        with pytest.raises(AudioConfigError):
            load_audio_config({"FORGE_AUDIO_MAX_UPLOAD_MB": "0"})

    def test_une_variable_absente_garde_le_defaut(self) -> None:
        assert load_audio_config({}).max_upload_mb == 200

    def test_les_deux_paquets_refusent_de_la_meme_facon(self) -> None:
        from forge_mvc_video.config import VideoConfigError, load_video_config

        with pytest.raises(AudioConfigError):
            load_audio_config({"FORGE_AUDIO_MAX_UPLOAD_MB": "abc"})
        with pytest.raises(VideoConfigError):
            load_video_config({"FORGE_VIDEO_MAX_UPLOAD_MB": "abc"})
