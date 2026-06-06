"""Tests RUNTIME-ERROR-ENV-SOURCE-001 — le logger lit app_env via core.forge.

Le reste du core lit l'environnement via core.forge.get("app_env"). Le logger
d'erreurs runtime doit faire pareil, sinon il peut écrire (ou non) à contre-temps
quand la config est posée par forge.configure(app_env=...) sans export os.environ.
"""

import core.forge as forge
from core.errors.runtime_error_logger import (
    log_runtime_error,
    set_jsonl_dir,
)


def _trigger(log_dir, monkeypatch, *, forge_env, os_env):
    set_jsonl_dir(log_dir)
    monkeypatch.setitem(forge._cfg, "app_env", forge_env)
    monkeypatch.setenv("APP_ENV", os_env)
    try:
        try:
            raise RuntimeError("x")
        except RuntimeError as exc:
            log_runtime_error(exc)
    finally:
        set_jsonl_dir(None)
    return any(log_dir.glob("*.jsonl"))


def test_forge_prod_wins_over_os_env_dev(tmp_path, monkeypatch):
    # forge dit prod, os.environ dit dev : la source canonique (forge) gagne -> pas d'ecriture
    wrote = _trigger(tmp_path, monkeypatch, forge_env="prod", os_env="dev")
    assert wrote is False


def test_forge_dev_triggers_write(tmp_path, monkeypatch):
    wrote = _trigger(tmp_path, monkeypatch, forge_env="dev", os_env="prod")
    assert wrote is True
