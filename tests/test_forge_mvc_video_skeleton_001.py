"""Tests VIDEO-ROADMAP-OPEN-001 : squelette de l'opt-in forge-mvc-video.

Couvre : entrée catalogue (intégration opt-in:*), import du package, contrat
de configuration ``FORGE_VIDEO_*``, branchement HTTP ``register_video_routes``,
diagnostic ``video:doctor``, et présence dans l'aide CLI.

Le package est rendu importable par ``conftest.py`` (ajoute ``packages/*`` au
``sys.path``) — pas besoin d'installation pip.
"""
from __future__ import annotations

import importlib


# ---------------------------------------------------------------------------
# Package : import, version, API publique
# ---------------------------------------------------------------------------
# NB : l'entrée catalogue (opt-in:list/install/enable) est volontairement
# différée à un ticket d'intégration dédié — le garde-fou OPTIN-AUDIT-FIX-001
# interdit un opt-in routier au catalogue sans son câblage enable (registry
# projet multi-opt-in à généraliser). Ce squelette livre le package autonome
# et la commande `forge video:doctor`.

def test_package_importable_et_versionne():
    mod = importlib.import_module("forge_mvc_video")
    assert getattr(mod, "__version__", "")
    assert hasattr(mod, "register_video_routes")


def test_register_video_routes_retourne_le_router():
    from forge_mvc_video import register_video_routes

    sentinel = object()
    assert register_video_routes(sentinel) is sentinel  # chaînable, no-op au squelette


# ---------------------------------------------------------------------------
# Configuration FORGE_VIDEO_*
# ---------------------------------------------------------------------------

def test_config_defauts():
    from forge_mvc_video.config import load_video_config

    cfg = load_video_config({})
    assert cfg.ffmpeg_bin == "ffmpeg"
    assert cfg.ffprobe_bin == "ffprobe"
    assert cfg.storage_root == "storage/video"
    assert cfg.max_upload_mb == 1000
    assert cfg.max_duration_seconds == 3600


def test_config_override_et_valeurs_invalides():
    from forge_mvc_video.config import load_video_config

    cfg = load_video_config({
        "FORGE_VIDEO_FFMPEG_BIN": "/usr/bin/ffmpeg",
        "FORGE_VIDEO_MAX_UPLOAD_MB": "250",
        "FORGE_VIDEO_MAX_DURATION_SECONDS": "abc",  # invalide → défaut
    })
    assert cfg.ffmpeg_bin == "/usr/bin/ffmpeg"
    assert cfg.max_upload_mb == 250
    assert cfg.max_duration_seconds == 3600


# ---------------------------------------------------------------------------
# video:doctor
# ---------------------------------------------------------------------------

def test_doctor_checks_structure():
    from forge_mvc_video.cli.doctor import CheckResult, run_all

    results = run_all()
    names = [r.name for r in results]
    assert names == ["package", "config", "ffprobe", "ffmpeg", "routes"]
    assert all(isinstance(r, CheckResult) for r in results)
    # Les checks indépendants de l'environnement sont OK quoi qu'il arrive.
    by_name = {r.name: r for r in results}
    assert by_name["package"].status == "ok"
    assert by_name["config"].status == "ok"
    assert by_name["routes"].status == "ok"
    # ffmpeg/ffprobe : ok si présents, fail sinon — jamais autre chose.
    assert by_name["ffmpeg"].status in ("ok", "fail")
    assert by_name["ffprobe"].status in ("ok", "fail")


def test_doctor_main_retourne_code_coherent():
    from forge_mvc_video.cli.doctor import has_failures, main, run_all

    rc = main([])
    assert rc in (0, 1)
    assert rc == (1 if has_failures(run_all()) else 0)


# ---------------------------------------------------------------------------
# Aide CLI
# ---------------------------------------------------------------------------

def test_video_doctor_dans_aide():
    from forge_cli.help_dispatch import HELP_DESCRIPTIONS

    assert "video:doctor" in HELP_DESCRIPTIONS
