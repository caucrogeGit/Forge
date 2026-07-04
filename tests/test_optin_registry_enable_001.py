"""OPTIN-REGISTRY-ENABLE-001 (ADR-061) — enable/disable inscrivent tous les kind.

`forge opt-in:enable <name>` inscrit l'opt-in dans `ENABLED_OPTINS` (nom -> kind),
quel que soit son kind : les `route` reçoivent en plus le câblage, les autres
sont documentaires. `disable` retire l'entrée. Le registre n'est jamais supprimé.
"""
from __future__ import annotations

from pathlib import Path


from cli.optins import disable, enable
from cli.optins.registry_format import REGISTRY_TEMPLATE, read_enabled_optins

REGISTRY_REL = "optins/registry.py"


def _project(tmp_path: Path) -> Path:
    """Projet minimal avec le registre du squelette (toujours présent)."""
    (tmp_path / "optins").mkdir()
    (tmp_path / "optins" / "registry.py").write_text(REGISTRY_TEMPLATE, encoding="utf-8")
    return tmp_path


def _registry(tmp_path: Path) -> str:
    return (tmp_path / REGISTRY_REL).read_text(encoding="utf-8")


# ── Opt-in library (qrcode) : inscription documentaire, sans câblage ─────────

def test_enable_library_dry_run_n_ecrit_rien(tmp_path, monkeypatch, capsys):
    _project(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert enable.main(["qrcode"]) == 0
    assert read_enabled_optins(_registry(tmp_path)) == {}


def test_enable_library_apply_inscrit_l_entree(tmp_path, monkeypatch, capsys):
    _project(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert enable.main(["qrcode", "--apply"]) == 0
    assert read_enabled_optins(_registry(tmp_path)) == {"qrcode": "library"}


def test_enable_library_idempotent(tmp_path, monkeypatch, capsys):
    _project(tmp_path)
    monkeypatch.chdir(tmp_path)
    enable.main(["qrcode", "--apply"])
    assert enable.main(["qrcode", "--apply"]) == 0
    assert read_enabled_optins(_registry(tmp_path)) == {"qrcode": "library"}


def test_disable_library_retire_l_entree(tmp_path, monkeypatch, capsys):
    _project(tmp_path)
    monkeypatch.chdir(tmp_path)
    enable.main(["qrcode", "--apply"])
    assert disable.main(["qrcode", "--apply"]) == 0
    assert read_enabled_optins(_registry(tmp_path)) == {}
    # Le registre reste présent (fichier permanent, ADR-061).
    assert (tmp_path / REGISTRY_REL).exists()


def test_disable_library_ne_supprime_jamais_le_registre(tmp_path, monkeypatch, capsys):
    _project(tmp_path)
    monkeypatch.chdir(tmp_path)
    # disable d'un opt-in jamais inscrit : idempotent, registre intact.
    assert disable.main(["i18n", "--apply"]) == 0
    assert (tmp_path / REGISTRY_REL).exists()


def test_plusieurs_kinds_coexistent(tmp_path, monkeypatch, capsys):
    _project(tmp_path)
    monkeypatch.chdir(tmp_path)
    enable.main(["qrcode", "--apply"])   # library
    enable.main(["deploy", "--apply"])   # cli
    entries = read_enabled_optins(_registry(tmp_path))
    assert entries == {"qrcode": "library", "deploy": "cli"}
