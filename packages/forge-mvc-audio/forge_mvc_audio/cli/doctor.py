# pyright: strict
"""Diagnostic ``forge audio:doctor``.

Diagnostic **statique** : ne lance aucun ``ffmpeg``, n'ouvre aucun fichier
audio, ne touche à aucune base (il n'y en a pas). Il vérifie que l'environnement
est prêt :

1. le package ``forge_mvc_audio`` est importable et expose ``__version__`` ;
2. ``load_audio_config()`` charge une configuration cohérente ;
3. le binaire ``ffprobe`` est présent dans le PATH (validation/métadonnées) ;
4. le binaire ``ffmpeg`` est présent dans le PATH (transcodage MP3) ;
5. ``register_audio_routes`` est exposée (branchement HTTP).

``ffmpeg``/``ffprobe`` absents → ``fail`` : sondage et transcodage les exigent.
Convention alignée sur ``forge video:doctor`` / ``forge iot:doctor`` : statuts
minuscules ``ok``/``warn``/``fail``/``skip``, dataclass ``CheckResult``.
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from typing import Literal

__all__ = [
    "CheckResult",
    "check_package_importable",
    "check_config_loadable",
    "check_ffprobe_present",
    "check_ffmpeg_present",
    "check_routes_registrable",
    "run_all",
    "print_report",
    "has_failures",
    "main",
]

Status = Literal["ok", "warn", "fail", "skip"]


@dataclass(frozen=True)
class CheckResult:
    status: Status
    name: str
    detail: str = ""


def check_package_importable() -> CheckResult:
    try:
        import forge_mvc_audio

        version = getattr(forge_mvc_audio, "__version__", None)
    except Exception as exc:  # pragma: no cover — défensif
        return CheckResult("fail", "package", f"import impossible : {exc}")
    if not version:
        return CheckResult("warn", "package", "importable mais sans __version__")
    return CheckResult("ok", "package", f"forge_mvc_audio {version}")


def check_config_loadable() -> CheckResult:
    try:
        from forge_mvc_audio.config import load_audio_config

        cfg = load_audio_config()
    except Exception as exc:  # pragma: no cover — défensif
        return CheckResult("fail", "config", f"chargement impossible : {exc}")
    return CheckResult(
        "ok",
        "config",
        f"storage={cfg.storage_root}, max_upload={cfg.max_upload_mb} Mo, "
        f"max_durée={cfg.max_duration_seconds}s",
    )


def _check_binary(name: str, bin_value: str, purpose: str) -> CheckResult:
    path = shutil.which(bin_value)
    if path is None:
        return CheckResult(
            "fail",
            name,
            f"`{bin_value}` introuvable dans le PATH — requis pour {purpose}",
        )
    return CheckResult("ok", name, path)


def check_ffprobe_present() -> CheckResult:
    from forge_mvc_audio.config import load_audio_config

    return _check_binary(
        "ffprobe", load_audio_config().ffprobe_bin, "la validation et les métadonnées"
    )


def check_ffmpeg_present() -> CheckResult:
    from forge_mvc_audio.config import load_audio_config

    return _check_binary(
        "ffmpeg", load_audio_config().ffmpeg_bin, "le transcodage MP3"
    )


def check_routes_registrable() -> CheckResult:
    try:
        from forge_mvc_audio import register_audio_routes
    except Exception as exc:  # pragma: no cover — défensif
        return CheckResult("fail", "routes", f"register_audio_routes absente : {exc}")
    if not callable(register_audio_routes):
        return CheckResult("fail", "routes", "register_audio_routes non appelable")
    return CheckResult("ok", "routes", "register_audio_routes exposée")


def run_all() -> list[CheckResult]:
    return [
        check_package_importable(),
        check_config_loadable(),
        check_ffprobe_present(),
        check_ffmpeg_present(),
        check_routes_registrable(),
    ]


_TAGS = {"ok": "[OK]  ", "warn": "[WARN]", "fail": "[FAIL]", "skip": "[SKIP]"}


def print_report(results: list[CheckResult]) -> None:
    for r in results:
        tag = _TAGS.get(r.status, "[????]")
        line = f"{tag} {r.name}"
        if r.detail:
            line += f" — {r.detail}"
        print(line)


def has_failures(results: list[CheckResult]) -> bool:
    return any(r.status == "fail" for r in results)


def main(args: list[str] | None = None) -> int:
    results = run_all()
    print_report(results)
    return 1 if has_failures(results) else 0
