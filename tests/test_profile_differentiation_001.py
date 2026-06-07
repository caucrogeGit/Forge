"""
Tests PROFILE-DIFFERENTIATION-001 — Contrat et différenciation des profils Forge.

Valide :
- chaque profil a un contrat sémantique distinct dans sa description
- minimal n'inclut pas les intentions HTMX / Alpine / i18n
- dynamic inclut l'intention HTMX / Alpine
- multilingual inclut l'intention i18n / internationalisation
- les descriptions sont toutes différentes
- forge_profile.txt enregistre le nom exact du profil
- docs/reference/reference.md documente les profils
"""
from __future__ import annotations

import pathlib
import importlib
import importlib.util
from unittest.mock import patch

import pytest

from forge_cli.project_profiles import (
    PROJECT_PROFILE_DESCRIPTIONS,
    SUPPORTED_PROJECT_PROFILES,
)

ROOT = pathlib.Path(__file__).resolve().parent.parent


# ── Helpers ──────────────────────────────────────────────────────────────────


def _import_forge():
    spec = importlib.util.spec_from_file_location("forge", ROOT / "forge.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_cmd_new(forge, monkeypatch, tmp_path, name="Demo", profile="standard"):
    monkeypatch.chdir(tmp_path)
    with (
        patch.object(forge, "_require_command"),
        patch.object(
            forge,
            "_materialize_skeleton",
            side_effect=lambda d: pathlib.Path(d).mkdir(parents=True, exist_ok=True),
        ),
        patch.object(forge, "_configure_env_files"),
        patch.object(forge, "_setup_python_environment"),
        patch.object(forge, "_setup_node_environment", return_value=[]),
        patch.object(forge, "_generate_certificates"),
        patch.object(forge, "_reinitialize_git"),
    ):
        forge.cmd_new(name, profile=profile)
    return tmp_path / name


# ── Contrats sémantiques par profil ──────────────────────────────────────────


def test_minimal_description_sans_htmx():
    desc = PROJECT_PROFILE_DESCRIPTIONS["minimal"].lower()
    assert "htmx" not in desc


def test_minimal_description_sans_alpine():
    desc = PROJECT_PROFILE_DESCRIPTIONS["minimal"].lower()
    assert "alpine" not in desc


def test_minimal_description_sans_i18n():
    desc = PROJECT_PROFILE_DESCRIPTIONS["minimal"].lower()
    assert "i18n" not in desc and "internationalisation" not in desc and "translat" not in desc


def test_dynamic_description_mentionne_htmx():
    desc = PROJECT_PROFILE_DESCRIPTIONS["dynamic"].lower()
    assert "htmx" in desc


def test_dynamic_description_mentionne_alpine():
    desc = PROJECT_PROFILE_DESCRIPTIONS["dynamic"].lower()
    assert "alpine" in desc


def test_multilingual_description_mentionne_i18n():
    desc = PROJECT_PROFILE_DESCRIPTIONS["multilingual"].lower()
    assert "i18n" in desc or "internationalisation" in desc or "translat" in desc


def test_multilingual_description_sans_htmx():
    """multilingual hérite de standard, pas de dynamic."""
    desc = PROJECT_PROFILE_DESCRIPTIONS["multilingual"].lower()
    assert "htmx" not in desc


# ── Unicité des descriptions ──────────────────────────────────────────────────


def test_descriptions_toutes_distinctes():
    descs = list(PROJECT_PROFILE_DESCRIPTIONS.values())
    assert len(descs) == len(set(descs)), "Deux profils ont la même description"


def test_chaque_profil_a_sa_propre_identite_semantique():
    """Les descriptions doivent cibler des cas d'usage différents."""
    minimal = PROJECT_PROFILE_DESCRIPTIONS["minimal"].lower()
    standard = PROJECT_PROFILE_DESCRIPTIONS["standard"].lower()
    dynamic = PROJECT_PROFILE_DESCRIPTIONS["dynamic"].lower()
    multilingual = PROJECT_PROFILE_DESCRIPTIONS["multilingual"].lower()
    # dynamic ≠ multilingual (intentions orthogonales)
    assert dynamic != multilingual
    # minimal ≠ standard
    assert minimal != standard


# ── Hiérarchie contractuelle ─────────────────────────────────────────────────


def test_standard_description_plus_riche_que_minimal():
    """standard décrit plus d'éléments que minimal."""
    assert len(PROJECT_PROFILE_DESCRIPTIONS["standard"]) > len(
        PROJECT_PROFILE_DESCRIPTIONS["minimal"]
    )


def test_dynamic_construit_sur_standard():
    """dynamic se réfère à standard dans sa description."""
    desc = PROJECT_PROFILE_DESCRIPTIONS["dynamic"].lower()
    assert "standard" in desc


def test_multilingual_construit_sur_standard():
    """multilingual se réfère à standard dans sa description."""
    desc = PROJECT_PROFILE_DESCRIPTIONS["multilingual"].lower()
    assert "standard" in desc


# ── forge_profile.txt par profil ─────────────────────────────────────────────


@pytest.mark.parametrize("profile", list(SUPPORTED_PROJECT_PROFILES))
def test_forge_profile_txt_contenu_exact(tmp_path, monkeypatch, profile):
    """forge_profile.txt contient uniquement le nom du profil."""
    forge = _import_forge()
    dest = _run_cmd_new(forge, monkeypatch, tmp_path, name=f"P{profile}", profile=profile)
    raw = (dest / "forge_profile.txt").read_text(encoding="utf-8")
    assert raw.strip() == profile


# ── Documentation ─────────────────────────────────────────────────────────────


def test_reference_md_documente_les_profils():
    """docs/reference/reference.md (index) ou docs/reference/profils.md mentionne les profils."""
    index = (ROOT / "docs" / "reference" / "reference.md").read_text(encoding="utf-8")
    profils = (ROOT / "docs" / "reference" / "profils.md").read_text(encoding="utf-8")
    content = index + profils
    assert "profil" in content.lower() or "profile" in content.lower()


def test_reference_md_mentionne_les_quatre_profils():
    """docs/reference/profils.md mentionne chacun des 4 profils."""
    content = (ROOT / "docs" / "reference" / "profils.md").read_text(encoding="utf-8")
    for profile in SUPPORTED_PROJECT_PROFILES:
        assert profile in content, f"Profil absent de docs/reference/profils.md : {profile}"


def test_profiles_md_documente_limites_actuelles():
    """docs/features/profiles.md précise les limites actuelles de la différenciation."""
    content = (ROOT / "docs" / "features" / "profiles.md").read_text(encoding="utf-8")
    assert "limit" in content.lower()
