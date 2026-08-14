"""VIDEO-FFMPEG-REEL-001 — le transcodage produit vraiment un MP4 lisible.

`forge-mvc-video` compte 1624 lignes, dont le transcodage est la raison d'être.
Rien ne l'exerçait contre le vrai `ffmpeg`, pourtant installé :

- `transcode_to_mp4` était appelé avec `runner=fake`. La **commande était
  construite et comparée à une chaîne attendue**, jamais exécutée. Un drapeau
  invalide, un codec absent de la compilation locale, un ordre d'arguments que
  `ffmpeg` refuse : rien ne l'aurait dit ;
- `parse_probe_json` était nourri d'un JSON **écrit à la main**. C'est la
  croyance de l'auteur du test sur ce que rend `ffprobe`, pas ce que `ffprobe`
  rend. Si la forme réelle diffère, le parseur casse en production pendant que
  la suite reste verte.

Ce fichier fabrique une vraie vidéo, la sonde, la transcode, puis sonde le
résultat. C'est la même correction que celle apportée au script de
`forge db:init` : un artefact produit pour l'utilisateur ne se vérifie pas en
comparant des chaînes.

La vidéo est synthétique, 160x120 sur trois secondes, et le tour complet prend
moins d'une seconde.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_video")

from forge_mvc_video.probe import parse_probe_json
from forge_mvc_video.transcode import generate_poster, transcode_to_mp4

#: `ffmpeg` fabrique la source ; `ffprobe` juge le résultat. Sans eux, ce
#: fichier n'a rien à dire, et le dit.
_FFMPEG = shutil.which("ffmpeg")
_FFPROBE = shutil.which("ffprobe")

pytestmark = pytest.mark.skipif(
    not (_FFMPEG and _FFPROBE),
    reason=(
        "ffmpeg et ffprobe absents : le transcodage ne peut pas être exercé. "
        "Installez-les (apt install ffmpeg) pour couvrir forge-mvc-video."
    ),
)


@pytest.fixture(scope="module")
def source(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Une vraie vidéo, image et son, fabriquée par ffmpeg lui-même."""
    chemin = tmp_path_factory.mktemp("video") / "source.mov"
    resultat = subprocess.run(
        [
            _FFMPEG or "ffmpeg", "-v", "error",
            "-f", "lavfi", "-i", "testsrc=duration=3:size=160x120:rate=10",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=3",
            # `yuv420p` : le format de toute vidéo de téléphone. Sans lui,
            # libx264 choisit `yuv444p`, que l'encodeur JPEG refuse, et l'on
            # mesurerait un défaut de la source plutôt que du code.
            "-pix_fmt", "yuv420p",
            "-c:v", "libx264", "-c:a", "aac", "-shortest", "-y", str(chemin),
        ],
        capture_output=True, text=True, timeout=120,
    )
    assert resultat.returncode == 0, f"fabrication de la source impossible :\n{resultat.stderr}"
    return chemin


def _sonder(chemin: Path) -> dict:
    """La sortie **réelle** de ffprobe, celle que le parseur doit savoir lire."""
    resultat = subprocess.run(
        [
            _FFPROBE or "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", str(chemin),
        ],
        capture_output=True, text=True, timeout=120,
    )
    assert resultat.returncode == 0, resultat.stderr
    return json.loads(resultat.stdout)


# ── Le parseur face à la vraie sortie de l'outil ─────────────────────────────


def test_le_parseur_lit_la_sortie_reelle_de_ffprobe(source: Path) -> None:
    """LE test du parseur : il était nourri d'un JSON écrit à la main.

    Une clé renommée, un type qui change, une profondeur différente, et le
    parseur rendrait `None` partout sans que rien ne le signale : les champs
    sont tous facultatifs.
    """
    brut = _sonder(source)

    meta = parse_probe_json(json.dumps(brut))

    assert meta.width == 160, f"largeur mal lue : {meta.width}"
    assert meta.height == 120, f"hauteur mal lue : {meta.height}"
    assert meta.duration_seconds == 3, f"durée mal lue : {meta.duration_seconds}"


def test_le_parseur_ne_rend_pas_silencieusement_des_champs_vides(source: Path) -> None:
    """Le mode de défaillance propre à ce parseur : tout est facultatif.

    Rendre `VideoMetadata(None, None, None)` sur une vidéo parfaitement valide
    serait indiscernable d'un succès pour l'appelant, et c'est exactement ce
    qui arriverait si la forme de la sortie changeait.
    """
    meta = parse_probe_json(json.dumps(_sonder(source)))

    vides = [
        nom for nom in ("width", "height", "duration_seconds")
        if getattr(meta, nom) is None
    ]
    assert not vides, (
        f"le parseur rend {vides} à vide sur une vidéo valide : la forme de la "
        "sortie de ffprobe a changé sous lui"
    )


# ── Le transcodage produit un fichier réellement lisible ─────────────────────


def test_le_mp4_produit_est_lisible_et_bien_encode(source: Path, tmp_path: Path) -> None:
    """LE test du ticket : la commande était comparée à une chaîne, jamais lancée.

    Le contrat annoncé par l'opt-in est un MP4 en H.264 et AAC. Seul `ffprobe`
    peut le confirmer, et il le confirme sur le fichier réellement écrit.
    """
    sortie = tmp_path / "sortie.mp4"

    transcode_to_mp4(str(source), str(sortie))

    assert sortie.is_file(), "aucun fichier produit"
    assert sortie.stat().st_size > 0, "fichier produit vide"

    sonde = _sonder(sortie)
    codecs = {flux["codec_name"] for flux in sonde["streams"]}
    conteneur = sonde["format"]["format_name"]

    assert "h264" in codecs, f"la vidéo n'est pas en H.264 : {codecs}"
    assert "aac" in codecs, f"l'audio n'est pas en AAC : {codecs}"
    assert "mp4" in conteneur, f"le conteneur n'est pas un MP4 : {conteneur}"


def test_le_transcodage_conserve_les_dimensions(source: Path, tmp_path: Path) -> None:
    """Une vidéo déformée est un défaut visible, qu'aucune chaîne ne montre."""
    sortie = tmp_path / "sortie.mp4"
    transcode_to_mp4(str(source), str(sortie))

    flux = next(f for f in _sonder(sortie)["streams"] if f["codec_type"] == "video")

    assert (flux["width"], flux["height"]) == (160, 120)


def test_l_affiche_produite_est_une_vraie_image(source: Path, tmp_path: Path) -> None:
    """L'affiche est ce que voit l'utilisateur avant de lancer la lecture.

    Un fichier de zéro octet, ou un fichier que rien ne sait ouvrir, se
    présenterait comme une image cassée dans la page.
    """
    affiche = tmp_path / "affiche.jpg"

    generate_poster(str(source), str(affiche))

    assert affiche.is_file(), "aucune affiche produite"
    assert affiche.stat().st_size > 0, "affiche vide"

    flux = _sonder(affiche)["streams"]
    assert flux, "ffprobe ne reconnaît aucun flux dans l'affiche"
    assert flux[0]["width"] > 0 and flux[0]["height"] > 0


def test_un_fichier_qui_n_est_pas_une_video_fait_echouer_le_transcodage(
    tmp_path: Path,
) -> None:
    """La contrepartie : tout accepter ferait passer les tests précédents.

    Un envoi malveillant ou simplement erroné doit produire une erreur nette,
    et non un MP4 vide que l'application servirait ensuite.
    """
    faux = tmp_path / "pas_une_video.mp4"
    faux.write_bytes(b"ceci n'est pas une video")
    sortie = tmp_path / "sortie.mp4"

    with pytest.raises(Exception):
        transcode_to_mp4(str(faux), str(sortie))


# ── La vidéo trop courte pour l'instant de capture ───────────────────────────


@pytest.fixture
def source_courte(tmp_path: Path) -> Path:
    """Une vidéo d'une seconde : un clip de produit, un GIF converti."""
    chemin = tmp_path / "courte.mp4"
    resultat = subprocess.run(
        [
            _FFMPEG or "ffmpeg", "-v", "error",
            "-f", "lavfi", "-i", "testsrc=duration=1:size=160x120:rate=10",
            "-pix_fmt", "yuv420p", "-c:v", "libx264", "-y", str(chemin),
        ],
        capture_output=True, text=True, timeout=120,
    )
    assert resultat.returncode == 0, resultat.stderr
    return chemin


def test_une_video_d_une_seconde_a_bien_son_affiche(source_courte: Path, tmp_path: Path) -> None:
    """LE défaut trouvé en écrivant ce fichier (`VIDEO-AFFICHE-COURTE-001`).

    L'affiche était prise à une seconde sans regarder la durée. Sur une vidéo
    d'une seconde ou moins, la recherche tombe après la dernière image, aucune
    image n'est écrite, et ffmpeg échoue. Le pipeline marquait alors la vidéo
    ENTIÈRE en échec, alors que le transcodage aurait réussi.

    Aucun test ne pouvait le voir : la commande était comparée à une chaîne,
    jamais exécutée.
    """
    from forge_mvc_video.process import instant_de_l_affiche

    affiche = tmp_path / "affiche.jpg"

    generate_poster(str(source_courte), str(affiche),
                    at_seconds=instant_de_l_affiche(1))

    assert affiche.is_file() and affiche.stat().st_size > 0, (
        "une vidéo d'une seconde n'a pas d'affiche : elle sera rejetée en entier"
    )


def test_l_instant_par_defaut_echoue_bien_sur_une_video_courte(
    source_courte: Path, tmp_path: Path
) -> None:
    """Le contre-exemple, sans lequel le test précédent ressemblerait à un rite.

    Il enregistre pourquoi la borne existe : à une seconde sur une vidéo d'une
    seconde, ffmpeg n'écrit rien. Si un jour ffmpeg tolère ce cas, ce test
    échouera et la borne pourra être revue.
    """
    with pytest.raises(Exception):
        generate_poster(str(source_courte), str(tmp_path / "vide.jpg"), at_seconds=1)
