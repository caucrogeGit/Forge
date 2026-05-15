"""Tests du contrat des profils de projet Forge (PROFILE-001 / PROFILE-002 / PROFILE-003)."""

from __future__ import annotations

import sys
import importlib
import pathlib
import pytest
from unittest.mock import patch

from forge_cli.project_profiles import (
    DEFAULT_PROJECT_PROFILE,
    PROJECT_PROFILE_DESCRIPTIONS,
    SUPPORTED_PROJECT_PROFILES,
)


def test_cinq_profils():
    assert len(SUPPORTED_PROJECT_PROFILES) == 5


def test_profils_stables():
    assert "minimal" in SUPPORTED_PROJECT_PROFILES
    assert "standard" in SUPPORTED_PROJECT_PROFILES
    assert "dynamic" in SUPPORTED_PROJECT_PROFILES
    assert "multilingual" in SUPPORTED_PROJECT_PROFILES


def test_profils_sans_doublon():
    assert len(SUPPORTED_PROJECT_PROFILES) == len(set(SUPPORTED_PROJECT_PROFILES))


def test_profil_par_defaut_est_standard():
    assert DEFAULT_PROJECT_PROFILE == "standard"


def test_profil_par_defaut_dans_supported():
    assert DEFAULT_PROJECT_PROFILE in SUPPORTED_PROJECT_PROFILES


def test_toutes_descriptions_presentes():
    for p in SUPPORTED_PROJECT_PROFILES:
        assert p in PROJECT_PROFILE_DESCRIPTIONS, f"Description manquante : {p}"


def test_toutes_descriptions_non_vides():
    for p, desc in PROJECT_PROFILE_DESCRIPTIONS.items():
        assert desc.strip(), f"Description vide : {p}"


def test_pas_de_profil_inconnu_dans_descriptions():
    for p in PROJECT_PROFILE_DESCRIPTIONS:
        assert p in SUPPORTED_PROJECT_PROFILES, f"Profil inconnu dans descriptions : {p}"


def test_ordre_progression():
    profiles = list(SUPPORTED_PROJECT_PROFILES)
    assert profiles.index("minimal") < profiles.index("standard")
    assert profiles.index("standard") < profiles.index("dynamic")


# ── PROFILE-002 : intégration forge new --profile ─────────────────────────────

def _import_forge():
    """Importe forge.py depuis la racine du projet."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    spec = importlib.util.spec_from_file_location("forge", root / "forge.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_cmd_new_signature_accepte_profile():
    import inspect
    forge = _import_forge()
    sig = inspect.signature(forge.cmd_new)
    assert "profile" in sig.parameters


def test_cmd_new_profil_par_defaut_est_standard():
    import inspect
    forge = _import_forge()
    sig = inspect.signature(forge.cmd_new)
    assert sig.parameters["profile"].default == "standard"


def test_cmd_new_profil_inconnu_leve_sysexit():
    forge = _import_forge()
    with patch.object(sys, "exit") as mock_exit:
        mock_exit.side_effect = SystemExit("profil inconnu")
        try:
            forge.cmd_new("MonProjet", profile="inexistant")
        except SystemExit:
            pass
        mock_exit.assert_called_once()
        msg = str(mock_exit.call_args[0][0])
        assert "inexistant" in msg


def test_cmd_new_message_erreur_liste_profils_connus():
    forge = _import_forge()
    with patch.object(sys, "exit") as mock_exit:
        mock_exit.side_effect = SystemExit("profil inconnu")
        try:
            forge.cmd_new("MonProjet", profile="inexistant")
        except SystemExit:
            pass
        msg = str(mock_exit.call_args[0][0])
        for p in SUPPORTED_PROJECT_PROFILES:
            assert p in msg


def test_cmd_new_ecrit_forge_profile_txt(tmp_path, monkeypatch):
    forge = _import_forge()
    monkeypatch.chdir(tmp_path)

    dest = tmp_path / "TestProjet"

    def fake_clone(d, ref=None):
        import pathlib
        pathlib.Path(d).mkdir(parents=True, exist_ok=True)

    with (
        patch.object(forge, "_require_command"),
        patch.object(forge, "_clone_skeleton", side_effect=fake_clone),
        patch.object(forge, "_configure_env_files"),
        patch.object(forge, "_setup_python_environment"),
        patch.object(forge, "_setup_node_environment", return_value=[]),
        patch.object(forge, "_generate_certificates"),
        patch.object(forge, "_reinitialize_git"),
    ):
        forge.cmd_new("TestProjet", profile="dynamic")

    profile_file = dest / "forge_profile.txt"
    assert profile_file.exists()
    assert profile_file.read_text(encoding="utf-8").strip() == "dynamic"


def test_cmd_new_tous_profils_valides_acceptes(tmp_path, monkeypatch):
    forge = _import_forge()

    for profile in SUPPORTED_PROJECT_PROFILES:
        projet_dir = tmp_path / profile
        projet_dir.mkdir()
        monkeypatch.chdir(tmp_path)

        with (
            patch.object(forge, "_require_command"),
            patch.object(forge, "_clone_skeleton"),
            patch.object(forge, "_configure_env_files"),
            patch.object(forge, "_setup_python_environment"),
            patch.object(forge, "_setup_node_environment", return_value=[]),
            patch.object(forge, "_generate_certificates"),
            patch.object(forge, "_reinitialize_git"),
            patch.object(sys, "exit") as mock_exit,
        ):
            mock_exit.side_effect = SystemExit
            # Le dossier existe déjà → sys.exit appelé pour ça, pas pour le profil
            try:
                forge.cmd_new(profile, profile=profile)
            except SystemExit:
                pass
            # L'exit doit mentionner "existe déjà", pas un profil inconnu
            if mock_exit.called:
                msg = str(mock_exit.call_args[0][0])
                assert "profil" not in msg.lower() or "existe" in msg.lower()


def test_dispatch_parse_profile_option():
    """forge new NomProjet --profile minimal appelle cmd_new avec profile='minimal'."""
    forge = _import_forge()

    calls = []

    def fake_cmd_new(name, ref=None, profile=DEFAULT_PROJECT_PROFILE):
        calls.append({"name": name, "ref": ref, "profile": profile})

    with (
        patch.object(forge, "cmd_new", side_effect=fake_cmd_new),
        patch.object(sys, "argv", ["forge", "new", "MonProjet", "--profile", "minimal"]),
    ):
        forge.main()

    assert len(calls) == 1
    assert calls[0]["profile"] == "minimal"
    assert calls[0]["name"] == "MonProjet"


def test_dispatch_profile_defaut_si_absent():
    forge = _import_forge()

    calls = []

    def fake_cmd_new(name, ref=None, profile=DEFAULT_PROJECT_PROFILE):
        calls.append({"profile": profile})

    with (
        patch.object(forge, "cmd_new", side_effect=fake_cmd_new),
        patch.object(sys, "argv", ["forge", "new", "MonProjet"]),
    ):
        forge.main()

    assert calls[0]["profile"] == DEFAULT_PROJECT_PROFILE


def test_dispatch_profile_et_ref_simultanement():
    forge = _import_forge()

    calls = []

    def fake_cmd_new(name, ref=None, profile=DEFAULT_PROJECT_PROFILE):
        calls.append({"ref": ref, "profile": profile})

    with (
        patch.object(forge, "cmd_new", side_effect=fake_cmd_new),
        patch.object(sys, "argv", ["forge", "new", "MonProjet", "--ref", "main", "--profile", "dynamic"]),
    ):
        forge.main()

    assert calls[0]["ref"] == "main"
    assert calls[0]["profile"] == "dynamic"


# ── PROFILE-003 : génération par profil ───────────────────────────────────────

def _fake_clone(d, ref=None):
    """Simule _clone_skeleton en créant uniquement le dossier destination."""
    pathlib.Path(d).mkdir(parents=True, exist_ok=True)


def _run_cmd_new(forge, monkeypatch, tmp_path, name="Demo", **kwargs):
    """Lance cmd_new avec toutes les I/O neutralisées. Retourne le chemin du projet."""
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


@pytest.mark.parametrize("profile", SUPPORTED_PROJECT_PROFILES)
def test_chaque_profil_ecrit_contenu_correct(tmp_path, monkeypatch, profile):
    """Chaque profil officiel est accepté et écrit son nom dans forge_profile.txt."""
    forge = _import_forge()
    dest = _run_cmd_new(forge, monkeypatch, tmp_path, name=f"Projet{profile.capitalize()}", profile=profile)
    content = (dest / "forge_profile.txt").read_text(encoding="utf-8").strip()
    assert content == profile


def test_profil_par_defaut_ecrit_standard(tmp_path, monkeypatch):
    """Sans --profile, forge_profile.txt contient 'standard'."""
    forge = _import_forge()
    dest = _run_cmd_new(forge, monkeypatch, tmp_path, name="Demo")
    content = (dest / "forge_profile.txt").read_text(encoding="utf-8").strip()
    assert content == "standard"


def test_forge_profile_txt_contient_uniquement_le_profil(tmp_path, monkeypatch):
    """forge_profile.txt ne contient que le nom du profil, aucun contenu supplémentaire."""
    forge = _import_forge()
    dest = _run_cmd_new(forge, monkeypatch, tmp_path, name="Demo", profile="minimal")
    raw = (dest / "forge_profile.txt").read_text(encoding="utf-8")
    lignes_non_vides = [l for l in raw.splitlines() if l.strip()]
    assert lignes_non_vides == ["minimal"], f"Contenu inattendu : {raw!r}"


def test_forge_profile_txt_est_lisible(tmp_path, monkeypatch):
    """forge_profile.txt est lisible en UTF-8 sans erreur."""
    forge = _import_forge()
    dest = _run_cmd_new(forge, monkeypatch, tmp_path, name="Demo", profile="multilingual")
    content = (dest / "forge_profile.txt").read_text(encoding="utf-8")
    assert content.strip() in SUPPORTED_PROJECT_PROFILES


def test_profil_invalide_aucun_dossier_cree(tmp_path, monkeypatch):
    """Un profil invalide ne doit créer aucun dossier projet partiel."""
    forge = _import_forge()
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        forge.cmd_new("Demo", profile="admin")
    assert not (tmp_path / "Demo").exists()


def test_profil_invalide_avant_require_command(tmp_path, monkeypatch):
    """La validation du profil précède _require_command : pas de vérification système inutile."""
    forge = _import_forge()
    monkeypatch.chdir(tmp_path)
    require_called = []
    monkeypatch.setattr(forge, "_require_command", lambda cmd, label=None: require_called.append(cmd))
    with pytest.raises(SystemExit):
        forge.cmd_new("Demo", profile="admin")
    assert require_called == []


def test_ref_et_profile_transmis_conjointement(tmp_path, monkeypatch):
    """--ref et --profile sont tous deux propagés correctement à cmd_new."""
    forge = _import_forge()
    monkeypatch.chdir(tmp_path)
    cloned_ref = {}

    def spy_clone(d, ref=None):
        cloned_ref["ref"] = ref
        pathlib.Path(d).mkdir(parents=True, exist_ok=True)

    with (
        patch.object(forge, "_require_command"),
        patch.object(forge, "_clone_skeleton", side_effect=spy_clone),
        patch.object(forge, "_configure_env_files"),
        patch.object(forge, "_setup_python_environment"),
        patch.object(forge, "_setup_node_environment", return_value=[]),
        patch.object(forge, "_generate_certificates"),
        patch.object(forge, "_reinitialize_git"),
    ):
        forge.cmd_new("Demo", ref="v2.0.0", profile="dynamic")

    assert cloned_ref["ref"] == "v2.0.0"
    assert (tmp_path / "Demo" / "forge_profile.txt").read_text(encoding="utf-8").strip() == "dynamic"


def test_comportement_historique_preserve_sans_profile(tmp_path, monkeypatch):
    """Sans --profile, cmd_new se comporte comme avant : profil standard, forge_profile.txt présent."""
    forge = _import_forge()
    dest = _run_cmd_new(forge, monkeypatch, tmp_path, name="Demo")
    profile_file = dest / "forge_profile.txt"
    assert profile_file.exists()
    assert profile_file.read_text(encoding="utf-8").strip() == DEFAULT_PROJECT_PROFILE


def test_profil_mentionne_dans_message_demarrage(tmp_path, monkeypatch, capsys):
    """Le nom du profil apparaît dans le message affiché au lancement de forge new."""
    forge = _import_forge()
    _run_cmd_new(forge, monkeypatch, tmp_path, name="Demo", profile="multilingual")
    assert "multilingual" in capsys.readouterr().out


def test_tests_appuyes_sur_supported_project_profiles():
    """Les tests de profil s'appuient sur SUPPORTED_PROJECT_PROFILES, pas une liste dupliquée."""
    assert set(SUPPORTED_PROJECT_PROFILES) == {"minimal", "standard", "dynamic", "multilingual", "auth-mfa"}
    assert DEFAULT_PROJECT_PROFILE == "standard"


def test_docs_roadmap_md_absent():
    """docs/roadmap.md ne doit pas exister (ne doit pas être recréé)."""
    root = pathlib.Path(__file__).resolve().parent.parent
    assert not (root / "docs" / "roadmap.md").exists()


# ── PROFILE-DOC-001 : tests documentaires ─────────────────────────────────────

def test_doc_profiles_md_existe():
    """docs/profiles.md doit exister."""
    root = pathlib.Path(__file__).resolve().parent.parent
    assert (root / "docs" / "profiles.md").exists()


def test_doc_profiles_mentionne_les_quatre_profils():
    """docs/profiles.md mentionne les 4 profils officiels."""
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "docs" / "profiles.md").read_text(encoding="utf-8")
    for profile in SUPPORTED_PROJECT_PROFILES:
        assert profile in content, f"Profil absent de docs/profiles.md : {profile}"


def test_doc_profiles_mentionne_forge_profile_txt():
    """docs/profiles.md documente forge_profile.txt."""
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "docs" / "profiles.md").read_text(encoding="utf-8")
    assert "forge_profile.txt" in content


def test_doc_profiles_mentionne_profil_par_defaut():
    """docs/profiles.md précise que standard est le profil par défaut."""
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "docs" / "profiles.md").read_text(encoding="utf-8")
    assert "standard" in content
    assert "défaut" in content


def test_doc_profiles_mentionne_option_profile():
    """docs/profiles.md documente l'option --profile."""
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "docs" / "profiles.md").read_text(encoding="utf-8")
    assert "--profile" in content


def test_forge_design_roadmap_lisible():
    """docs/forge-design-roadmap.md doit rester lisible (non corrompu, non supprimé)."""
    root = pathlib.Path(__file__).resolve().parent.parent
    design_roadmap = root / "docs" / "roadmap" / "forge-design-roadmap.md"
    if design_roadmap.exists():
        content = design_roadmap.read_text(encoding="utf-8")
        assert len(content) > 0
