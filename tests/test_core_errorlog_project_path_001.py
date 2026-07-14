"""Tests — CORE-ERRORLOG-PROJECT-PATH-001 : journal d'erreurs écrit dans le projet.

L'ancien repli de `_resolve_jsonl_dir()` écrivait dans
`site-packages/core/storage/logs` (répertoire du paquet installé), invisible
pour le développeur d'un projet généré. Garde-fous :
  1. le défaut résout `storage/logs` contre le répertoire de lancement (cwd) ;
  2. écriture bout en bout : `log_runtime_error` produit le JSONL dans le
     `storage/logs` du projet courant ;
  3. `set_jsonl_dir()` garde la priorité (point d'injection des tests) ;
  4. absence : la résolution du défaut ne dépend plus de `__file__`
     (plus jamais de chemin relatif au paquet).
"""
from __future__ import annotations

import inspect
import pathlib

import core.errors.runtime_error_logger as rel
from core.errors.runtime_error_logger import (
    log_runtime_error,
    set_jsonl_dir,
)


class TestDefaultResolution:
    def test_defaut_resout_contre_cwd(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        set_jsonl_dir(None)
        assert rel._resolve_jsonl_dir() == tmp_path / "storage" / "logs"

    def test_override_garde_la_priorite(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        override = tmp_path / "ailleurs"
        set_jsonl_dir(override)
        try:
            assert rel._resolve_jsonl_dir() == override
        finally:
            set_jsonl_dir(None)


class TestEndToEndWrite:
    def test_ecrit_dans_le_storage_du_projet(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        set_jsonl_dir(None)
        import core.forge as forge

        monkeypatch.setitem(forge._cfg, "app_env", "dev")
        try:
            raise ValueError("erreur de test CORE-ERRORLOG-PROJECT-PATH-001")
        except ValueError as exc:
            log_runtime_error(exc)
        jsonl = tmp_path / "storage" / "logs" / "errors.dev.jsonl"
        assert jsonl.exists()
        assert "CORE-ERRORLOG-PROJECT-PATH-001" in jsonl.read_text(encoding="utf-8")


class TestNoPackageRelativeFallback:
    def test_resolution_sans_file(self):
        source = inspect.getsource(rel._resolve_jsonl_dir)
        assert "__file__" not in source, (
            "_resolve_jsonl_dir ne doit plus se résoudre par rapport au paquet installé"
        )

    def test_defaut_hors_du_paquet(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        set_jsonl_dir(None)
        package_root = pathlib.Path(rel.__file__).resolve().parent.parent
        resolved = rel._resolve_jsonl_dir().resolve()
        assert package_root not in resolved.parents
