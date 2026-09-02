"""Tests unitaires du module opt-in forge-mvc-audio — AUDIO-MODULE-001.

Couvre config, storage (uuid-based, sans état), probe (parsing + runner injecté),
ingest (validation + stockage) et transcode (commande pure + runner injecté).
Aucun ffmpeg/ffprobe réel n'est lancé.
"""
from __future__ import annotations

import json

import pytest

pytest.importorskip("forge_mvc_audio")

from forge_mvc_audio.config import AudioConfig, load_audio_config
from forge_mvc_audio.ingest import AudioIngestError, ingest_audio
from forge_mvc_audio.probe import AudioProbeError, parse_probe_json, probe_audio
from forge_mvc_audio.storage import (
    ALLOWED_EXTENSIONS,
    is_valid_uuid,
    resolve_playable_relpath,
    safe_extension,
    store_original,
)
from forge_mvc_audio.transcode import (
    FfmpegError,
    build_transcode_command,
    transcode_to_mp3,
)

_UUID = "11111111-1111-4111-8111-111111111111"


# ── Config ───────────────────────────────────────────────────────────────────

def test_config_defaults():
    cfg = load_audio_config({})
    assert cfg.ffmpeg_bin == "ffmpeg"
    assert cfg.ffprobe_bin == "ffprobe"
    assert cfg.storage_root == "storage/audio"
    assert cfg.max_upload_mb == 200
    assert cfg.max_duration_seconds == 7200
    assert cfg.api_token is None


def test_config_from_env():
    cfg = load_audio_config({
        "FORGE_AUDIO_STORAGE_ROOT": "/data/audio",
        "FORGE_AUDIO_MAX_UPLOAD_MB": "50",
        "FORGE_AUDIO_API_TOKEN": "secret",
    })
    assert cfg.storage_root == "/data/audio"
    assert cfg.max_upload_mb == 50
    assert cfg.api_token == "secret"


def test_config_invalid_int_leve():
    """Une valeur illisible LÈVE, elle ne retombe plus sur le défaut.

    Ce test verrouillait le comportement inverse, qui était un défaut :
    `FORGE_AUDIO_MAX_UPLOAD_MB=abc` donnait 200 en silence, les fichiers plus
    lourds étaient refusés, et rien ne l'expliquait.

    `AUDIO-DOCTOR-HARMONISE-001` aligne l'audio sur la vidéo, qui a fait le
    même chemin avec `VIDEO-QUOTA-001`, et sur `forge-mvc-files`.
    """
    import pytest

    from forge_mvc_audio.config import AudioConfigError

    assert load_audio_config({}).max_upload_mb == 200

    for mauvais in ("abc", "-5", "0"):
        with pytest.raises(AudioConfigError):
            load_audio_config({"FORGE_AUDIO_MAX_UPLOAD_MB": mauvais})


# ── Storage ──────────────────────────────────────────────────────────────────

def test_safe_extension():
    assert safe_extension("song.MP3") == ".mp3"
    assert safe_extension("noext") == ""


def test_is_valid_uuid():
    assert is_valid_uuid(_UUID)
    assert not is_valid_uuid("../etc/passwd")
    assert not is_valid_uuid("not-a-uuid")
    assert not is_valid_uuid("")


def test_allowed_extensions_cover_common_audio():
    for ext in (".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac"):
        assert ext in ALLOWED_EXTENSIONS


def test_store_original_uuid_based(tmp_path):
    rel = store_original(b"AUDIO", _UUID, ".mp3", storage_root=str(tmp_path))
    assert rel == f"originals/{_UUID}/source.mp3"
    assert (tmp_path / rel).read_bytes() == b"AUDIO"
    # Le nom utilisateur n'apparaît jamais dans le chemin.
    assert "source.mp3" in rel


def test_resolve_prefers_transcoded(tmp_path):
    (tmp_path / "transcoded" / _UUID).mkdir(parents=True)
    (tmp_path / "transcoded" / _UUID / "audio.mp3").write_bytes(b"MP3")
    store_original(b"WAV", _UUID, ".wav", storage_root=str(tmp_path))
    assert resolve_playable_relpath(_UUID, storage_root=str(tmp_path)) == (
        f"transcoded/{_UUID}/audio.mp3"
    )


def test_resolve_falls_back_to_source(tmp_path):
    store_original(b"WAV", _UUID, ".wav", storage_root=str(tmp_path))
    assert resolve_playable_relpath(_UUID, storage_root=str(tmp_path)) == (
        f"originals/{_UUID}/source.wav"
    )


def test_resolve_none_when_absent(tmp_path):
    assert resolve_playable_relpath(_UUID, storage_root=str(tmp_path)) is None


def test_resolve_rejects_bad_uuid(tmp_path):
    assert resolve_playable_relpath("../secret", storage_root=str(tmp_path)) is None


# ── Ingest ───────────────────────────────────────────────────────────────────

def test_ingest_stores_and_returns_record(tmp_path):
    cfg = AudioConfig(storage_root=str(tmp_path))
    record = ingest_audio(b"AUDIODATA", "podcast.mp3", title="  Ep 1 ", config=cfg)
    assert record["title"] == "Ep 1"
    assert record["size_bytes"] == len(b"AUDIODATA")
    assert record["mime_type"] == "audio/mpeg"
    assert (tmp_path / record["original_path"]).read_bytes() == b"AUDIODATA"


def test_ingest_refuse_fichier_vide(tmp_path):
    with pytest.raises(AudioIngestError, match="vide"):
        ingest_audio(b"", "x.mp3", config=AudioConfig(storage_root=str(tmp_path)))


def test_ingest_refuse_extension(tmp_path):
    with pytest.raises(AudioIngestError, match="extension"):
        ingest_audio(b"x", "malware.exe", config=AudioConfig(storage_root=str(tmp_path)))


def test_ingest_refuse_trop_volumineux(tmp_path):
    cfg = AudioConfig(storage_root=str(tmp_path), max_upload_mb=1)
    big = b"x" * (1 * 1024 * 1024 + 1)
    with pytest.raises(AudioIngestError, match="volumineux"):
        ingest_audio(big, "x.mp3", config=cfg)


# ── Probe ────────────────────────────────────────────────────────────────────

_FFPROBE_JSON = json.dumps({
    "format": {"duration": "212.5", "bit_rate": "192000", "format_name": "mp3"},
    "streams": [
        {"codec_type": "audio", "codec_name": "mp3", "sample_rate": "44100", "channels": "2"}
    ],
})


def test_parse_probe_json_extrait_metadonnees():
    meta = parse_probe_json(_FFPROBE_JSON)
    assert meta.duration_seconds == 212
    assert meta.audio_codec == "mp3"
    assert meta.bitrate_kbps == 192
    assert meta.sample_rate_hz == 44100
    assert meta.channels == 2
    assert meta.container == "mp3"


def test_parse_probe_json_refuse_sans_flux_audio():
    payload = json.dumps({"format": {}, "streams": [{"codec_type": "video"}]})
    with pytest.raises(AudioProbeError, match="aucun flux audio"):
        parse_probe_json(payload)


def test_probe_audio_with_injected_runner():
    meta = probe_audio("x.mp3", runner=lambda _bin, _path: _FFPROBE_JSON)
    assert meta.duration_seconds == 212


def test_probe_audio_refuse_duree_trop_longue():
    cfg = AudioConfig(max_duration_seconds=10)
    with pytest.raises(AudioProbeError, match="durée"):
        probe_audio("x.mp3", config=cfg, runner=lambda _b, _p: _FFPROBE_JSON)


# ── Transcode ────────────────────────────────────────────────────────────────

def test_build_transcode_command_mp3():
    cmd = build_transcode_command("ffmpeg", "in.wav", "out.mp3")
    assert cmd[0] == "ffmpeg"
    assert "-c:a" in cmd and "libmp3lame" in cmd
    assert "192k" in cmd
    assert "-map_metadata" in cmd and "-1" in cmd
    assert cmd[-1] == "out.mp3"
    # Jamais shell=True : la commande est une liste.
    assert isinstance(cmd, list)


def test_transcode_to_mp3_success_with_runner():
    calls = []
    transcode_to_mp3(
        "in.wav", "out.mp3",
        runner=lambda cmd, timeout: (calls.append((cmd, timeout)) or (0, "")),
    )
    assert calls and calls[0][0][0] == "ffmpeg"


def test_transcode_to_mp3_failure_raises():
    with pytest.raises(FfmpegError, match="échoué"):
        transcode_to_mp3("in.wav", "out.mp3", runner=lambda cmd, t: (1, "boom"))
