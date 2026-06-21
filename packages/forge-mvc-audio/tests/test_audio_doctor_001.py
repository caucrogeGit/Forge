"""Tests AUDIO-DOCTOR-001 : diagnostic statique `forge audio:doctor`.

Aucun ffmpeg/ffprobe réel n'est lancé (les checks binaires sont testés via la
présence/absence dans le PATH, monkeypatchée). Aligné sur le doctor vidéo/IoT.
"""
from __future__ import annotations

import pytest

pytest.importorskip("forge_mvc_audio")

from forge_mvc_audio.cli import doctor


def test_check_package_importable():
    r = doctor.check_package_importable()
    assert r.status == "ok"
    assert "forge_mvc_audio" in r.detail


def test_check_config_loadable():
    r = doctor.check_config_loadable()
    assert r.status == "ok"
    assert "storage=" in r.detail


def test_check_routes_registrable():
    r = doctor.check_routes_registrable()
    assert r.status == "ok"


def test_check_ffprobe_present_ok(monkeypatch):
    monkeypatch.setattr(doctor.shutil, "which", lambda _b: "/usr/bin/ffprobe")
    assert doctor.check_ffprobe_present().status == "ok"


def test_check_ffprobe_absent_fail(monkeypatch):
    monkeypatch.setattr(doctor.shutil, "which", lambda _b: None)
    r = doctor.check_ffprobe_present()
    assert r.status == "fail"
    assert "PATH" in r.detail


def test_check_ffmpeg_absent_fail(monkeypatch):
    monkeypatch.setattr(doctor.shutil, "which", lambda _b: None)
    assert doctor.check_ffmpeg_present().status == "fail"


def test_run_all_returns_five_checks():
    results = doctor.run_all()
    names = [r.name for r in results]
    assert names == ["package", "config", "ffprobe", "ffmpeg", "routes"]


def test_has_failures_counts_only_fail():
    ok = [doctor.CheckResult("ok", "a"), doctor.CheckResult("warn", "b")]
    assert not doctor.has_failures(ok)
    assert doctor.has_failures(ok + [doctor.CheckResult("fail", "c")])


def test_no_migration_check():
    # Module sans état : pas de check migration (contrairement à video/iot).
    assert not hasattr(doctor, "check_migration_present")


def test_main_returns_int(monkeypatch):
    # ffmpeg/ffprobe présents → 0 ; absents → 1.
    monkeypatch.setattr(doctor.shutil, "which", lambda _b: "/usr/bin/x")
    assert doctor.main([]) == 0
    monkeypatch.setattr(doctor.shutil, "which", lambda _b: None)
    assert doctor.main([]) == 1
