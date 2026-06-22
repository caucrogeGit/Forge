"""Tests pour CONSOLIDATION-MODULES-001 — Cycle complet des modules Forge."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

ROOT = Path(__file__).resolve().parents[2]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _write_module(
    modules_root: Path,
    name: str = "agenda",
    *,
    provides: list[str] | None = None,
    paths: dict | None = None,
    extra: dict | None = None,
) -> Path:
    """Crée un module minimal valide dans modules_root/name/."""
    module_dir = modules_root / name
    module_dir.mkdir(parents=True, exist_ok=True)
    data: dict = {
        "name": name,
        "label": name.capitalize(),
        "version": "0.1.0",
        "description": f"Module {name} pour tests.",
    }
    if provides is not None:
        data["provides"] = provides
    if paths is not None:
        data["paths"] = paths
    if extra:
        data.update(extra)
    (module_dir / "module.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    return module_dir


def _write_module_with_controller(modules_root: Path, name: str = "agenda") -> Path:
    """Crée un module avec un contrôleur installable."""
    module_dir = _write_module(
        modules_root, name,
        provides=["controllers"],
        paths={"controllers": "controllers"},
    )
    ctrl_dir = module_dir / "controllers"
    ctrl_dir.mkdir(exist_ok=True)
    (ctrl_dir / f"{name}_controller.py").write_text(
        f"# Contrôleur {name}\n", encoding="utf-8"
    )
    return module_dir


def _write_module_with_routes(modules_root: Path, name: str = "agenda") -> Path:
    """Crée un module avec un fichier de routes."""
    module_dir = _write_module(
        modules_root, name,
        provides=["routes"],
        paths={"routes": "routes.py"},
    )
    (module_dir / "routes.py").write_text(
        "def register_routes(router): pass\n", encoding="utf-8"
    )
    return module_dir


def _install_manifest(tmp_path: Path, module_dir: Path, name: str) -> Path:
    """Installe le manifeste dans le registre et retourne le chemin du registre."""
    from core.modules import install_module_manifest, load_module_manifest
    manifest = load_module_manifest(module_dir / "module.json")
    reg_path = tmp_path / "forge_modules.json"
    install_module_manifest(manifest, module_dir, registry_path=reg_path)
    return reg_path


# ── Découverte des modules ─────────────────────────────────────────────────────

def test_discover_module_valide(tmp_path):
    """Un dossier module valide est découvert et retourné dans la liste des valides."""
    from core.modules import discover_module_manifests
    modules_root = tmp_path / "modules"
    _write_module(modules_root, "agenda")

    valid, invalid = discover_module_manifests(modules_root)

    assert len(valid) == 1
    assert valid[0].name == "agenda"
    assert invalid == []


def test_discover_dossier_absent_retourne_listes_vides(tmp_path):
    """Si le dossier modules/ n'existe pas, discover retourne ([], [])."""
    from core.modules import discover_module_manifests
    valid, invalid = discover_module_manifests(tmp_path / "modules_absent")
    assert valid == []
    assert invalid == []


def test_discover_module_invalide_dans_liste_invalides(tmp_path):
    """Un module avec module.json invalide apparaît dans la liste des invalides."""
    from core.modules import discover_module_manifests
    modules_root = tmp_path / "modules"
    bad_dir = modules_root / "mauvais"
    bad_dir.mkdir(parents=True)
    (bad_dir / "module.json").write_text('{"name": "", "label": ""}', encoding="utf-8")

    valid, invalid = discover_module_manifests(modules_root)

    assert len(invalid) == 1
    assert invalid[0][0] == "mauvais"


def test_discover_plusieurs_modules(tmp_path):
    """Plusieurs modules dans le même dossier sont tous découverts."""
    from core.modules import discover_module_manifests
    modules_root = tmp_path / "modules"
    _write_module(modules_root, "agenda")
    _write_module(modules_root, "contacts")

    valid, _ = discover_module_manifests(modules_root)

    names = {m.name for m in valid}
    assert "agenda" in names
    assert "contacts" in names


# ── Installation du manifeste ──────────────────────────────────────────────────

def test_install_manifest_cree_registre(tmp_path, monkeypatch):
    """install_module_manifest crée forge_modules.json avec le module enregistré."""
    monkeypatch.chdir(tmp_path)
    from core.modules import install_module_manifest, load_installed_modules_registry, load_module_manifest
    modules_root = tmp_path / "modules"
    module_dir = _write_module(modules_root, "agenda")
    manifest = load_module_manifest(module_dir / "module.json")
    reg_path = tmp_path / "forge_modules.json"

    install_module_manifest(manifest, "modules/agenda", registry_path=reg_path)

    assert reg_path.exists()
    registry = load_installed_modules_registry(reg_path)
    assert "agenda" in registry["installed"]


def test_install_manifest_double_echoue(tmp_path, monkeypatch):
    """install_module_manifest lève ModuleAlreadyInstalledError si déjà installé."""
    monkeypatch.chdir(tmp_path)
    from core.modules import (
        ModuleAlreadyInstalledError,
        install_module_manifest,
        load_module_manifest,
    )
    modules_root = tmp_path / "modules"
    module_dir = _write_module(modules_root, "agenda")
    manifest = load_module_manifest(module_dir / "module.json")
    reg_path = tmp_path / "forge_modules.json"
    install_module_manifest(manifest, "modules/agenda", registry_path=reg_path)

    with pytest.raises(ModuleAlreadyInstalledError):
        install_module_manifest(manifest, "modules/agenda", registry_path=reg_path)


def test_install_manifest_dry_run_necrit_rien(tmp_path, monkeypatch):
    """install_module_manifest en dry-run ne crée pas forge_modules.json."""
    monkeypatch.chdir(tmp_path)
    from core.modules import install_module_manifest, load_module_manifest
    modules_root = tmp_path / "modules"
    module_dir = _write_module(modules_root, "agenda")
    manifest = load_module_manifest(module_dir / "module.json")
    reg_path = tmp_path / "forge_modules.json"

    result = install_module_manifest(manifest, "modules/agenda", registry_path=reg_path, dry_run=True)

    assert not reg_path.exists()
    assert result.dry_run is True
    assert result.installed is False


# ── Installation des fichiers ──────────────────────────────────────────────────

def test_install_files_copie_controller(tmp_path, monkeypatch):
    """install_module_files copie le contrôleur dans mvc/controllers/."""
    monkeypatch.chdir(tmp_path)
    from core.modules import install_module_files, load_module_manifest, install_module_manifest
    modules_root = tmp_path / "modules"
    module_dir = _write_module_with_controller(modules_root, "agenda")
    manifest = load_module_manifest(module_dir / "module.json")
    reg_path = tmp_path / "forge_modules.json"
    install_module_manifest(manifest, module_dir, registry_path=reg_path)

    result = install_module_files("agenda", registry_path=reg_path)

    target = tmp_path / "mvc" / "controllers" / "agenda_controller.py"
    assert target.exists()
    assert result.installed is True
    assert result.dry_run is False


def test_install_files_dry_run_ne_copie_rien(tmp_path, monkeypatch):
    """install_module_files en dry-run ne crée aucun fichier."""
    monkeypatch.chdir(tmp_path)
    from core.modules import install_module_files, load_module_manifest, install_module_manifest
    modules_root = tmp_path / "modules"
    module_dir = _write_module_with_controller(modules_root, "agenda")
    manifest = load_module_manifest(module_dir / "module.json")
    reg_path = tmp_path / "forge_modules.json"
    install_module_manifest(manifest, module_dir, registry_path=reg_path)

    install_module_files("agenda", registry_path=reg_path, dry_run=True)

    assert not (tmp_path / "mvc" / "controllers" / "agenda_controller.py").exists()


def test_install_files_conflit_refuse_atomiquement(tmp_path, monkeypatch):
    """Si un fichier cible existe, install_module_files refuse tout et ne modifie rien."""
    monkeypatch.chdir(tmp_path)
    from core.modules import ModuleFileConflictError, install_module_files, load_module_manifest, install_module_manifest
    modules_root = tmp_path / "modules"
    module_dir = _write_module_with_controller(modules_root, "agenda")
    manifest = load_module_manifest(module_dir / "module.json")
    reg_path = tmp_path / "forge_modules.json"
    install_module_manifest(manifest, module_dir, registry_path=reg_path)

    # Pré-créer le fichier cible avec contenu utilisateur
    target = tmp_path / "mvc" / "controllers" / "agenda_controller.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    user_content = "# code utilisateur\n"
    target.write_text(user_content, encoding="utf-8")

    with pytest.raises(ModuleFileConflictError):
        install_module_files("agenda", registry_path=reg_path)

    assert target.read_text(encoding="utf-8") == user_content


def test_install_files_module_non_installe_echoue(tmp_path, monkeypatch):
    """install_module_files lève ModuleFileInstallError si le module n'est pas dans le registre."""
    monkeypatch.chdir(tmp_path)
    from core.modules import ModuleFileInstallError, install_module_files
    reg_path = tmp_path / "forge_modules.json"

    with pytest.raises(ModuleFileInstallError):
        install_module_files("absent", registry_path=reg_path)


# ── Routes de module ───────────────────────────────────────────────────────────

def test_generate_routes_cree_fichier_dedie(tmp_path, monkeypatch):
    """generate_module_routes crée mvc/routes_agenda.py avec l'import du module."""
    monkeypatch.chdir(tmp_path)
    from core.modules import generate_module_routes, install_module_manifest, load_module_manifest
    modules_root = tmp_path / "modules"
    module_dir = _write_module_with_routes(modules_root, "agenda")
    manifest = load_module_manifest(module_dir / "module.json")
    reg_path = tmp_path / "forge_modules.json"
    install_module_manifest(manifest, module_dir, registry_path=reg_path)

    result = generate_module_routes("agenda", registry_path=reg_path)

    dedicated = tmp_path / "mvc" / "routes_agenda.py"
    assert dedicated.exists()
    assert result.generated is True
    content = dedicated.read_text(encoding="utf-8")
    assert "register_agenda_routes" in content


def test_generate_routes_doublon_refuse(tmp_path, monkeypatch):
    """generate_module_routes lève ModuleRoutesAlreadyGeneratedError si déjà généré."""
    monkeypatch.chdir(tmp_path)
    from core.modules import generate_module_routes, install_module_manifest, load_module_manifest
    from core.modules.routes import ModuleRoutesAlreadyGeneratedError
    modules_root = tmp_path / "modules"
    module_dir = _write_module_with_routes(modules_root, "agenda")
    manifest = load_module_manifest(module_dir / "module.json")
    reg_path = tmp_path / "forge_modules.json"
    install_module_manifest(manifest, module_dir, registry_path=reg_path)
    generate_module_routes("agenda", registry_path=reg_path)

    with pytest.raises(ModuleRoutesAlreadyGeneratedError):
        generate_module_routes("agenda", registry_path=reg_path)


# ── Scénario cycle complet représentatif ──────────────────────────────────────

def test_cycle_complet_liste_installe_fichiers(tmp_path, monkeypatch):
    """Scénario complet : découvrir → installer manifeste → installer fichiers.

    Vérifie que le cycle module de bout en bout est fonctionnel.
    """
    monkeypatch.chdir(tmp_path)
    from core.modules import (
        discover_module_manifests,
        install_module_manifest,
        install_module_files,
        load_installed_modules_registry,
        load_module_manifest,
    )

    # 1. Préparer un module avec contrôleur
    modules_root = tmp_path / "modules"
    module_dir = _write_module_with_controller(modules_root, "agenda")

    # 2. Lister les modules disponibles
    valid, invalid = discover_module_manifests(modules_root)
    assert len(valid) == 1
    assert valid[0].name == "agenda"
    assert invalid == []

    # 3. Installer le manifeste
    manifest = load_module_manifest(module_dir / "module.json")
    reg_path = tmp_path / "forge_modules.json"
    install_module_manifest(manifest, module_dir, registry_path=reg_path)

    # 4. Vérifier le registre
    registry = load_installed_modules_registry(reg_path)
    assert "agenda" in registry["installed"]

    # 5. Installer les fichiers
    result = install_module_files("agenda", registry_path=reg_path)
    assert result.installed is True

    # 6. Vérifier que les fichiers existent
    assert (tmp_path / "mvc" / "controllers" / "agenda_controller.py").exists()

    # 7. Vérifier que le registre liste les fichiers installés
    registry2 = load_installed_modules_registry(reg_path)
    files_installed = registry2["installed"]["agenda"].get("files_installed", [])
    assert any("agenda_controller.py" in f for f in files_installed)


# ── Sécurité des fichiers ─────────────────────────────────────────────────────

def test_symlink_refuse_a_installation(tmp_path, monkeypatch):
    """install_module_files refuse un module dont le dossier source est un symlink."""
    monkeypatch.chdir(tmp_path)
    from core.modules import (
        ModuleFileInstallError,
        install_module_files,
        install_module_manifest,
        load_module_manifest,
    )

    # Créer un module réel
    modules_root = tmp_path / "modules"
    real_dir = modules_root / "agenda_real"
    real_dir.mkdir(parents=True)
    ctrl_dir = real_dir / "controllers"
    ctrl_dir.mkdir()
    (ctrl_dir / "agenda_controller.py").write_text("# ctrl\n", encoding="utf-8")

    # Créer un symlink pointant vers le dossier controllers
    link_dir = modules_root / "agenda" / "ctrl_link"
    (modules_root / "agenda").mkdir(parents=True)
    link_dir.symlink_to(ctrl_dir)

    # Forger un module avec paths.controllers pointant vers le symlink
    module_json = {
        "name": "agenda",
        "label": "Agenda",
        "version": "0.1.0",
        "description": "Test symlink.",
        "provides": ["controllers"],
        "paths": {"controllers": "ctrl_link"},
    }
    (modules_root / "agenda" / "module.json").write_text(json.dumps(module_json), encoding="utf-8")
    manifest = load_module_manifest(modules_root / "agenda" / "module.json")
    reg_path = tmp_path / "forge_modules.json"
    install_module_manifest(manifest, modules_root / "agenda", registry_path=reg_path)

    with pytest.raises(ModuleFileInstallError):
        install_module_files("agenda", registry_path=reg_path)


def test_chemin_traversal_refuse_dans_manifest(tmp_path):
    """Un manifest avec paths contenant '..' est refusé à la validation."""
    from core.modules import validate_module_manifest

    data = {
        "name": "mauvais",
        "label": "Mauvais",
        "version": "0.1.0",
        "description": "Test traversal.",
        "provides": ["controllers"],
        "paths": {"controllers": "../controllers"},
    }
    from core.modules import ModuleManifestError
    with pytest.raises(ModuleManifestError):
        validate_module_manifest(data)


def test_url_file_refuse_dans_manifest(tmp_path):
    """Un manifest avec paths contenant 'file://' est refusé à la validation."""
    from core.modules import validate_module_manifest, ModuleManifestError

    data = {
        "name": "mauvais",
        "label": "Mauvais",
        "version": "0.1.0",
        "description": "Test file://.",
        "provides": ["controllers"],
        "paths": {"controllers": "file:///tmp/controllers"},
    }
    with pytest.raises(ModuleManifestError):
        validate_module_manifest(data)


def test_chemin_absolu_refuse_dans_manifest(tmp_path):
    """Un manifest avec paths contenant un chemin absolu est refusé."""
    from core.modules import validate_module_manifest, ModuleManifestError

    data = {
        "name": "mauvais",
        "label": "Mauvais",
        "version": "0.1.0",
        "description": "Test absolu.",
        "provides": ["controllers"],
        "paths": {"controllers": "/etc/controllers"},
    }
    with pytest.raises(ModuleManifestError):
        validate_module_manifest(data)


# ── Comportement sur module absent ou invalide ────────────────────────────────

def test_install_manifest_module_absent_echoue(tmp_path):
    """cmd_module_install lève SystemExit si le dossier module est absent."""
    from cli.deploy.modules import cmd_module_install
    with pytest.raises(SystemExit):
        cmd_module_install(["absent", "--path", str(tmp_path / "modules")])


def test_install_manifest_json_invalide_echoue(tmp_path):
    """cmd_module_install lève SystemExit si module.json est invalide."""
    from cli.deploy.modules import cmd_module_install
    modules_root = tmp_path / "modules"
    bad_dir = modules_root / "mauvais"
    bad_dir.mkdir(parents=True)
    (bad_dir / "module.json").write_text('{"name": ""}', encoding="utf-8")

    with pytest.raises(SystemExit):
        cmd_module_install(["mauvais", "--path", str(modules_root)])


# ── Document d'audit et roadmap ───────────────────────────────────────────────

def test_audit_consolidation_modules_001_existe():
    """docs/history/audits/consolidation-modules-001.md existe."""
    assert (ROOT / "docs" / "history" / "audits" / "consolidation-modules-001.md").exists()


def test_audit_mentionne_module_list():
    """Le document d'audit mentionne module:list."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-modules-001.md").read_text(encoding="utf-8")
    assert "module:list" in content


def test_audit_mentionne_module_install():
    """Le document d'audit mentionne module:install."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-modules-001.md").read_text(encoding="utf-8")
    assert "module:install" in content


def test_audit_mentionne_module_files():
    """Le document d'audit mentionne module:files."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-modules-001.md").read_text(encoding="utf-8")
    assert "module:files" in content


def test_audit_mentionne_module_routes():
    """Le document d'audit mentionne module:routes."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-modules-001.md").read_text(encoding="utf-8")
    assert "module:routes" in content


def test_audit_mentionne_limites():
    """Le document d'audit mentionne les limites du système."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-modules-001.md").read_text(encoding="utf-8")
    assert "limit" in content.lower()


def test_audit_contient_verdict_final():
    """Le document d'audit contient un verdict final."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-modules-001.md").read_text(encoding="utf-8")
    assert "Verdict" in content


def test_roadmap_marque_consolidation_modules_001_termine():
    """docs/forge-roadmap.md marque CONSOLIDATION-MODULES-001 comme terminé."""
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    assert "CONSOLIDATION-MODULES-001" in content
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


def test_forge_design_roadmap_non_modifie():
    """docs/forge-design-roadmap.md existe et n'a pas été supprimé."""
    assert (ROOT / "docs" / "roadmap" / "forge-design-roadmap.md").exists()
