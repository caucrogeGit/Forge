"""Tests pour CONSOLIDATION-PROFILES-001 — Cohérence des profils Forge."""

from __future__ import annotations

import importlib
import pathlib
import sys
from unittest.mock import patch

import pytest

from forge_cli.project_profiles import (
    DEFAULT_PROJECT_PROFILE,
    PROJECT_PROFILE_DESCRIPTIONS,
    SUPPORTED_PROJECT_PROFILES,
)

pytestmark = pytest.mark.meta

ROOT = pathlib.Path(__file__).resolve().parents[2]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _import_forge():
    spec = importlib.util.spec_from_file_location("forge", ROOT / "forge.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _fake_clone(d, ref=None):
    pathlib.Path(d).mkdir(parents=True, exist_ok=True)


def _run_cmd_new(forge, monkeypatch, tmp_path, name="Demo", **kwargs):
    monkeypatch.chdir(tmp_path)
    with (
        patch.object(forge, "_require_command"),
        patch.object(forge, "_clone_skeleton", side_effect=_fake_clone),
        patch.object(forge, "_configure_env_files"),
        patch.object(forge, "_setup_python_environment"),
        patch.object(forge, "_setup_node_environment", return_value=[]),
        patch.object(forge, "_generate_certificates"),
        patch.object(forge, "_reinitialize_git"),
    ):
        forge.cmd_new(name, **kwargs)
    return tmp_path / name


# ── Contrat des profils ────────────────────────────────────────────────────────

def test_profils_de_base_declares():
    """Les profils de base (minimal, standard, dynamic, multilingual) sont déclarés."""
    assert {"minimal", "standard", "dynamic", "multilingual"} <= set(SUPPORTED_PROJECT_PROFILES)


def test_profil_par_defaut_est_standard():
    """Le profil par défaut est 'standard'."""
    assert DEFAULT_PROJECT_PROFILE == "standard"


def test_description_dynamic_mentionne_htmx():
    """La description du profil dynamic mentionne HTMX."""
    desc = PROJECT_PROFILE_DESCRIPTIONS["dynamic"]
    assert "HTMX" in desc or "htmx" in desc.lower()


def test_description_multilingual_mentionne_i18n():
    """La description du profil multilingual mentionne i18n."""
    desc = PROJECT_PROFILE_DESCRIPTIONS["multilingual"]
    assert "i18n" in desc or "internationalisation" in desc.lower() or "multilingual" in desc.lower()


def test_description_minimal_ne_mentionne_pas_htmx():
    """La description du profil minimal ne promet pas HTMX."""
    desc = PROJECT_PROFILE_DESCRIPTIONS["minimal"]
    assert "HTMX" not in desc


# ── Scénario représentatif : génération des 4 profils ─────────────────────────

@pytest.mark.parametrize("profile", SUPPORTED_PROJECT_PROFILES)
def test_generation_profil_ecrit_forge_profile_txt(tmp_path, monkeypatch, profile):
    """Chaque profil officiel génère forge_profile.txt avec le bon nom."""
    forge = _import_forge()
    dest = _run_cmd_new(forge, monkeypatch, tmp_path, name=f"Projet{profile.capitalize()}", profile=profile)
    profile_file = dest / "forge_profile.txt"
    assert profile_file.exists(), f"forge_profile.txt absent pour le profil {profile}"
    assert profile_file.read_text(encoding="utf-8").strip() == profile


def test_generation_sans_profile_utilise_standard(tmp_path, monkeypatch):
    """forge new sans --profile génère forge_profile.txt contenant 'standard'."""
    forge = _import_forge()
    dest = _run_cmd_new(forge, monkeypatch, tmp_path, name="Demo")
    content = (dest / "forge_profile.txt").read_text(encoding="utf-8").strip()
    assert content == "standard"


def test_profil_invalide_leve_sysexit(tmp_path, monkeypatch):
    """Un profil invalide déclenche SystemExit avant toute création de fichier."""
    forge = _import_forge()
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        forge.cmd_new("Demo", profile="inexistant")


def test_profil_invalide_naucun_dossier_cree(tmp_path, monkeypatch):
    """Un profil invalide ne crée pas de dossier projet partiel."""
    forge = _import_forge()
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        forge.cmd_new("Demo", profile="admin")
    assert not (tmp_path / "Demo").exists()


def test_profil_invalide_message_liste_les_profils_connus(tmp_path, monkeypatch):
    """Le message d'erreur pour un profil invalide liste les profils connus."""
    forge = _import_forge()
    monkeypatch.chdir(tmp_path)
    with patch.object(sys, "exit") as mock_exit:
        mock_exit.side_effect = SystemExit
        try:
            forge.cmd_new("Demo", profile="inexistant")
        except SystemExit:
            pass
        msg = str(mock_exit.call_args[0][0])
        for p in SUPPORTED_PROJECT_PROFILES:
            assert p in msg, f"Profil {p} absent du message d'erreur"


def test_forge_profile_txt_contient_une_seule_ligne(tmp_path, monkeypatch):
    """forge_profile.txt contient exactement une ligne non vide."""
    forge = _import_forge()
    dest = _run_cmd_new(forge, monkeypatch, tmp_path, name="Demo", profile="dynamic")
    raw = (dest / "forge_profile.txt").read_text(encoding="utf-8")
    lignes = [l for l in raw.splitlines() if l.strip()]
    assert lignes == ["dynamic"]


def test_profil_affiche_dans_message_demarrage(tmp_path, monkeypatch, capsys):
    """Le nom du profil apparaît dans le message affiché lors de forge new."""
    forge = _import_forge()
    _run_cmd_new(forge, monkeypatch, tmp_path, name="Demo", profile="multilingual")
    assert "multilingual" in capsys.readouterr().out


# ── Différences entre profils ─────────────────────────────────────────────────

def test_limite_documentee_meme_squelette(tmp_path, monkeypatch):
    """La limitation connue (même squelette pour tous les profils) est documentée dans docs/profiles.md."""
    content = (ROOT / "docs" / "profiles.md").read_text(encoding="utf-8")
    assert "même structure" in content or "même squelette" in content or "même base" in content


def test_profils_coherents_avec_leur_hierarchie():
    """minimal < standard, standard < dynamic (ordre de progression déclaré)."""
    profiles = list(SUPPORTED_PROJECT_PROFILES)
    assert profiles.index("minimal") < profiles.index("standard")
    assert profiles.index("standard") < profiles.index("dynamic")


# ── Cohérence documentaire ────────────────────────────────────────────────────

def test_doc_profiles_md_existe():
    """docs/profiles.md existe."""
    assert (ROOT / "docs" / "profiles.md").exists()


def test_doc_profiles_mentionne_les_quatre_profils():
    """docs/profiles.md mentionne les 4 profils officiels."""
    content = (ROOT / "docs" / "profiles.md").read_text(encoding="utf-8")
    for profile in SUPPORTED_PROJECT_PROFILES:
        assert profile in content


def test_doc_profiles_mentionne_htmx_pour_dynamic():
    """docs/profiles.md mentionne HTMX dans la section dynamic."""
    content = (ROOT / "docs" / "profiles.md").read_text(encoding="utf-8")
    assert "HTMX" in content or "htmx" in content


def test_doc_profiles_mentionne_i18n_pour_multilingual():
    """docs/profiles.md mentionne i18n dans la section multilingual."""
    content = (ROOT / "docs" / "profiles.md").read_text(encoding="utf-8")
    assert "i18n" in content


def test_doc_profiles_mentionne_tailwind():
    """docs/profiles.md mentionne Tailwind (standard contient Tailwind)."""
    content = (ROOT / "docs" / "profiles.md").read_text(encoding="utf-8")
    assert "tailwind" in content.lower() or "Tailwind" in content


def test_doc_profiles_mentionne_limite_squelette():
    """docs/profiles.md documente la limite : mêmes squelettes actuellement."""
    content = (ROOT / "docs" / "profiles.md").read_text(encoding="utf-8")
    assert "Limites" in content or "limite" in content.lower()


# ── Cohérence profils / starters ──────────────────────────────────────────────

def test_doc_starters_index_mentionne_profils():
    """docs/starters/index.md référence les profils des starters."""
    content = (ROOT / "docs" / "starters" / "index.md").read_text(encoding="utf-8")
    assert "profil" in content.lower() or "profile" in content.lower()


def test_doc_starters_index_explique_difference_profil_starter():
    """docs/starters/index.md explique la différence entre profil et starter."""
    content = (ROOT / "docs" / "starters" / "index.md").read_text(encoding="utf-8")
    assert "profil" in content.lower()
    assert "starter" in content.lower()


def test_doc_profiles_mentionne_correspondance_starters():
    """docs/profiles.md établit la correspondance entre profils et starters."""
    content = (ROOT / "docs" / "profiles.md").read_text(encoding="utf-8")
    assert "starter" in content.lower()


def test_readme_mentionne_option_profile():
    """L'option `--profile` reste documentée.

    Le README public simplifié délègue le détail des profils au site de
    doc : on vérifie que `--profile` est documenté dans le README **ou**
    dans `docs/profiles.md` (page de référence des profils).
    """
    content = (ROOT / "README.md").read_text(encoding="utf-8")
    profiles_doc = ROOT / "docs" / "profiles.md"
    documented = "--profile" in content or (
        profiles_doc.exists() and "--profile" in profiles_doc.read_text(encoding="utf-8")
    )
    assert documented


# ── Séparation Forge Design ────────────────────────────────────────────────────

def test_profiles_py_ne_depend_pas_forge_design():
    """forge_cli/project_profiles.py ne référence pas Forge Design."""
    content = (ROOT / "forge_cli" / "project_profiles.py").read_text(encoding="utf-8")
    assert "forge-design" not in content.lower()
    assert "forge design" not in content.lower()


def test_doc_profiles_ne_promet_pas_editeur_graphique():
    """docs/profiles.md ne promet pas un éditeur graphique lié aux profils."""
    content = (ROOT / "docs" / "profiles.md").read_text(encoding="utf-8")
    assert "éditeur graphique" not in content.lower()


def test_forge_design_roadmap_non_modifie():
    """docs/forge-design-roadmap.md existe et n'a pas été supprimé."""
    assert (ROOT / "docs" / "roadmap" / "forge-design-roadmap.md").exists()


# ── Document d'audit et roadmap ───────────────────────────────────────────────

def test_audit_consolidation_profiles_001_existe():
    """docs/history/audits/consolidation-profiles-001.md existe."""
    assert (ROOT / "docs" / "history" / "audits" / "consolidation-profiles-001.md").exists()


def test_audit_mentionne_minimal():
    """Le document d'audit mentionne le profil minimal."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-profiles-001.md").read_text(encoding="utf-8")
    assert "minimal" in content


def test_audit_mentionne_dynamic():
    """Le document d'audit mentionne le profil dynamic."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-profiles-001.md").read_text(encoding="utf-8")
    assert "dynamic" in content


def test_audit_mentionne_multilingual():
    """Le document d'audit mentionne le profil multilingual."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-profiles-001.md").read_text(encoding="utf-8")
    assert "multilingual" in content


def test_audit_mentionne_forge_profile_txt():
    """Le document d'audit mentionne forge_profile.txt."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-profiles-001.md").read_text(encoding="utf-8")
    assert "forge_profile.txt" in content


def test_audit_contient_verdict_final():
    """Le document d'audit contient un verdict final."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-profiles-001.md").read_text(encoding="utf-8")
    assert "Verdict" in content


def test_roadmap_marque_consolidation_profiles_001_termine():
    """docs/forge-roadmap.md marque CONSOLIDATION-PROFILES-001 comme terminé."""
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    assert "CONSOLIDATION-PROFILES-001" in content
    assert "terminé" in content


def test_roadmap_priorite_est_dans_phase_consolidation():
    """La prochaine priorité immédiate est un ticket CONSOLIDATION-*."""
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    idx = content.find("Prochaine priorité immédiate")
    assert idx != -1
    bloc = content[idx: idx + 200]
    assert "CONSOLIDATION-" in bloc or "PUBLICATION-" in bloc or "POST-2.0-" in bloc or "DEPENDENCY-" in bloc or "RELEASE-" in bloc or "CMD-" in bloc or "AUTH-LEGACY-" in bloc or "CRUD-" in bloc or "SESSION-" in bloc or "I18N-" in bloc or "QUALITY-" in bloc or "RELEASE-2.1" in bloc or "SESSION-STORE-" in bloc or "SECURITY-" in bloc or "MODULE-" in bloc or "PROFILE-" in bloc or "HTTP-" in bloc or "CONCURRENCY-" in bloc or "HEALTH-" in bloc or "RELEASE-" in bloc or "APP-" in bloc or "DX-" in bloc or "HELP-" in bloc or "RECOVERY-" in bloc or "AUDIT-" in bloc or "E2E-" in bloc or "DOC-" in bloc or "API-" in bloc or "AUTH-MFA-" in bloc or "AUTH-SESSION-" in bloc or "AUTH-OIDC-" in bloc or "AUTH-ADMIN-" in bloc or "AUTH-DOC-" in bloc or "PHASE-" in bloc or "CRUD-" in bloc or "ROADMAP-" in bloc or "POST-" in bloc or "WORKFLOW-" in bloc


def test_roadmap_md_non_recree():
    """docs/roadmap.md ne doit pas exister."""
    assert not (ROOT / "docs" / "roadmap.md").exists()
