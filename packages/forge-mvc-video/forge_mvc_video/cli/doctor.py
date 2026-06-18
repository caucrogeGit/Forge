# pyright: strict
"""Diagnostic ``forge video:doctor`` — VIDEO-ROADMAP-OPEN-001.

Diagnostic **statique** : ne lance aucun ``ffmpeg``, n'ouvre aucun fichier
vidéo, ne touche à aucune base. Il vérifie que l'environnement est prêt :

1. le package ``forge_mvc_video`` est importable et expose ``__version__`` ;
2. ``load_video_config()`` charge une configuration cohérente ;
3. le binaire ``ffprobe`` est présent dans le PATH (validation/métadonnées) ;
4. le binaire ``ffmpeg`` est présent dans le PATH (transcodage MP4) ;
5. ``register_video_routes`` est exposée (branchement HTTP).

``ffmpeg``/``ffprobe`` absents → ``fail`` : le transcodage est central dans la
v1. Convention alignée sur ``forge iot:doctor`` : statuts minuscules
``ok``/``warn``/``fail``/``skip``, dataclass ``CheckResult``.
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from typing import Literal

__all__ = [
    "CheckResult",
    "check_package_importable",
    "check_config_loadable",
    "check_migration_present",
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
        import forge_mvc_video

        version = getattr(forge_mvc_video, "__version__", None)
    except Exception as exc:  # pragma: no cover — défensif
        return CheckResult("fail", "package", f"import impossible : {exc}")
    if not version:
        return CheckResult("warn", "package", "importable mais sans __version__")
    return CheckResult("ok", "package", f"forge_mvc_video {version}")


def check_config_loadable() -> CheckResult:
    try:
        from forge_mvc_video.config import load_video_config

        cfg = load_video_config()
    except Exception as exc:  # pragma: no cover — défensif
        return CheckResult("fail", "config", f"chargement impossible : {exc}")
    return CheckResult(
        "ok",
        "config",
        f"storage={cfg.storage_root}, max_upload={cfg.max_upload_mb} Mo, "
        f"max_durée={cfg.max_duration_seconds}s",
    )


def check_migration_present() -> CheckResult:
    """Vérifie la présence du fichier ``*_create_videos.sql`` packagé.

    Lecture via ``importlib.resources`` — fonctionne en install éditable, en
    wheel et en sdist (``[tool.setuptools.package-data]`` embarque les ``.sql``).
    """
    try:
        from importlib import resources

        anchor = resources.files("forge_mvc_video") / "migrations"
        candidates = sorted(
            entry.name for entry in anchor.iterdir()
            if entry.name.endswith("_create_videos.sql")
        )
    except (ImportError, ModuleNotFoundError, FileNotFoundError) as exc:  # pragma: no cover
        return CheckResult("fail", "migration", f"ressources illisibles : {exc}")
    if not candidates:
        return CheckResult("fail", "migration", "*_create_videos.sql introuvable dans le package")
    return CheckResult("ok", "migration", candidates[0])


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
    from forge_mvc_video.config import load_video_config

    return _check_binary(
        "ffprobe", load_video_config().ffprobe_bin, "la validation et les métadonnées"
    )


def check_ffmpeg_present() -> CheckResult:
    from forge_mvc_video.config import load_video_config

    return _check_binary(
        "ffmpeg", load_video_config().ffmpeg_bin, "le transcodage MP4"
    )


def check_routes_registrable() -> CheckResult:
    try:
        from forge_mvc_video import register_video_routes
    except Exception as exc:  # pragma: no cover — défensif
        return CheckResult("fail", "routes", f"register_video_routes absente : {exc}")
    if not callable(register_video_routes):
        return CheckResult("fail", "routes", "register_video_routes non appelable")
    return CheckResult("ok", "routes", "register_video_routes exposée")


def run_all() -> list[CheckResult]:
    return [
        check_package_importable(),
        check_config_loadable(),
        check_migration_present(),
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
