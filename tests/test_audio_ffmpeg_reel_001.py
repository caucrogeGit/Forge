"""AUDIO-FFMPEG-REEL-001 — le transcodage MP3 produit vraiment un fichier lisible.

`forge-mvc-audio` a le montage exact de `forge-mvc-video` avant
`VIDEO-FFMPEG-REEL-001`, et le même angle mort :

    probe_audio("x.mp3", runner=lambda _bin, _path: _FFPROBE_JSON)
    transcode_to_mp3("in.wav", "out.mp3", runner=lambda cmd, t: (0, ""))

La commande est **construite et comparée à une chaîne**, jamais exécutée, et le
parseur est nourri d'un JSON écrit à la main, c'est-à-dire la croyance de
l'auteur du test sur ce que rend `ffprobe`.

`AudioMetadata` porte six champs, tous facultatifs. Un parseur qui rendrait
`None` partout sur un fichier parfaitement valide serait indiscernable d'un
succès pour l'appelant, et c'est exactement ce qui arriverait si la forme de la
sortie de `ffprobe` changeait sous lui.

Ce fichier fabrique un vrai WAV, le transcode en MP3, puis sonde le résultat.
Le tour complet prend moins d'une seconde.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_audio")

from forge_mvc_audio.probe import parse_probe_json
from forge_mvc_audio.transcode import transcode_to_mp3

_FFMPEG = shutil.which("ffmpeg")
_FFPROBE = shutil.which("ffprobe")

pytestmark = pytest.mark.skipif(
    not (_FFMPEG and _FFPROBE),
    reason=(
        "ffmpeg et ffprobe absents : le transcodage ne peut pas être exercé. "
        "Installez-les (apt install ffmpeg) pour couvrir forge-mvc-audio."
    ),
)


@pytest.fixture(scope="module")
def source(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Un vrai WAV stéréo, deux secondes, fabriqué par ffmpeg lui-même."""
    chemin = tmp_path_factory.mktemp("audio") / "source.wav"
    resultat = subprocess.run(
        [
            _FFMPEG or "ffmpeg", "-v", "error",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
            "-f", "lavfi", "-i", "sine=frequency=660:duration=2",
            # Deux canaux : le nombre de canaux fait partie des métadonnées
            # lues, et un fichier mono ne le distinguerait pas d'un défaut.
            "-filter_complex", "[0:a][1:a]join=inputs=2:channel_layout=stereo[a]",
            "-map", "[a]", "-ar", "44100", "-y", str(chemin),
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
    """LE test du parseur : il était nourri d'un JSON écrit à la main."""
    meta = parse_probe_json(json.dumps(_sonder(source)))

    assert meta.duration_seconds == 2, f"durée mal lue : {meta.duration_seconds}"
    assert meta.sample_rate_hz == 44100, f"échantillonnage mal lu : {meta.sample_rate_hz}"
    assert meta.channels == 2, f"canaux mal lus : {meta.channels}"


def test_le_parseur_ne_rend_pas_silencieusement_des_champs_vides(source: Path) -> None:
    """Les six champs sont facultatifs : tout rendre à `None` passe pour un succès.

    C'est le mode de défaillance propre à ce parseur, et il est muet.
    """
    meta = parse_probe_json(json.dumps(_sonder(source)))

    vides = [
        nom for nom in ("duration_seconds", "audio_codec", "sample_rate_hz",
                        "channels", "container")
        if getattr(meta, nom) is None
    ]
    assert not vides, (
        f"le parseur rend {vides} à vide sur un fichier valide : la forme de la "
        "sortie de ffprobe a changé sous lui"
    )


# ── Le transcodage produit un fichier réellement lisible ─────────────────────


def test_le_mp3_produit_est_lisible_et_bien_encode(source: Path, tmp_path: Path) -> None:
    """LE test du ticket : la commande était comparée à une chaîne, jamais lancée.

    Le contrat annoncé par l'opt-in est un MP3 standard. Seul `ffprobe` peut le
    confirmer, et il le confirme sur le fichier réellement écrit.
    """
    sortie = tmp_path / "sortie.mp3"

    transcode_to_mp3(str(source), str(sortie))

    assert sortie.is_file(), "aucun fichier produit"
    assert sortie.stat().st_size > 0, "fichier produit vide"

    sonde = _sonder(sortie)
    codecs = {flux["codec_name"] for flux in sonde["streams"]}

    assert "mp3" in codecs, f"le flux n'est pas en MP3 : {codecs}"
    assert "mp3" in sonde["format"]["format_name"]


def test_le_transcodage_conserve_la_duree(source: Path, tmp_path: Path) -> None:
    """Un fichier tronqué reste un MP3 valide : seule la durée le démasque."""
    sortie = tmp_path / "sortie.mp3"
    transcode_to_mp3(str(source), str(sortie))

    duree = float(_sonder(sortie)["format"]["duration"])

    assert abs(duree - 2.0) < 0.5, f"durée du MP3 produit : {duree:.2f} s au lieu de 2 s"


def test_le_debit_demande_est_reellement_applique(source: Path, tmp_path: Path) -> None:
    """`bitrate_kbps` est un paramètre public : il doit agir sur le fichier.

    Comparer la commande construite dirait seulement que le drapeau est passé,
    pas qu'il est honoré par l'encodeur.
    """
    faible = tmp_path / "faible.mp3"
    fort = tmp_path / "fort.mp3"

    transcode_to_mp3(str(source), str(faible), bitrate_kbps=64)
    transcode_to_mp3(str(source), str(fort), bitrate_kbps=256)

    assert faible.stat().st_size < fort.stat().st_size, (
        f"le débit demandé ne change pas le fichier produit : "
        f"64 kbps -> {faible.stat().st_size} o, 256 kbps -> {fort.stat().st_size} o"
    )


def test_un_fichier_qui_n_est_pas_du_son_fait_echouer_le_transcodage(
    tmp_path: Path,
) -> None:
    """La contrepartie : tout accepter ferait passer les tests précédents."""
    faux = tmp_path / "pas_du_son.wav"
    faux.write_bytes(b"ceci n'est pas du son")
    sortie = tmp_path / "sortie.mp3"

    with pytest.raises(Exception):
        transcode_to_mp3(str(faux), str(sortie))
