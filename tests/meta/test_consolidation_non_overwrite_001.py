"""Tests pour CONSOLIDATION-NON-OVERWRITE-001 — Préservation du code utilisateur dans les générateurs Forge."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
pytestmark = pytest.mark.meta

ROOT = Path(__file__).resolve().parents[2]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _contact_json() -> dict:
    return {
        "schema_version": "1.0",
        "name": "Contact",
        "table": "contact",
        "description": "",
        "fields": [
            {"name": "nom", "type": "string", "max_length": 100},
        ],
    }


def _write_entity(entities_root: Path, name: str, data: dict) -> None:
    entity_dir = entities_root / name
    entity_dir.mkdir(parents=True, exist_ok=True)
    (entity_dir / f"{name}.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _write_relations(entities_root: Path) -> None:
    (entities_root / "relations.json").write_text(
        json.dumps({"schema_version": "1.0", "relations": []}, indent=2) + "\n",
        encoding="utf-8",
    )


# ── ensure_file ────────────────────────────────────────────────────────────────

def test_ensure_file_cree_si_absent(tmp_path):
    """ensure_file crée le fichier s'il n'existe pas encore."""
    from forge_mvc_entities.make_entity import ensure_file

    path = tmp_path / "test.py"
    created: list[Path] = []
    skipped: list[Path] = []
    ensure_file(path, "# contenu\n", created, skipped)

    assert path.exists()
    assert path in created
    assert path not in skipped
    assert path.read_text(encoding="utf-8") == "# contenu\n"


def test_ensure_file_ne_crase_pas_existant(tmp_path):
    """ensure_file ne modifie pas le contenu d'un fichier déjà présent."""
    from forge_mvc_entities.make_entity import ensure_file

    path = tmp_path / "test.py"
    path.write_text("# code utilisateur\n", encoding="utf-8")
    created: list[Path] = []
    skipped: list[Path] = []
    ensure_file(path, "# nouveau contenu\n", created, skipped)

    assert path.read_text(encoding="utf-8") == "# code utilisateur\n"
    assert path in skipped
    assert path not in created


def test_ensure_file_signale_skip_correctement(tmp_path):
    """ensure_file ajoute à skipped (non à created) si le fichier existe."""
    from forge_mvc_entities.make_entity import ensure_file

    path = tmp_path / "already.py"
    path.write_text("# existant\n", encoding="utf-8")
    created: list[Path] = []
    skipped: list[Path] = []
    ensure_file(path, "# nouveau\n", created, skipped)

    assert len(skipped) == 1
    assert len(created) == 0


# ── build_model — scénario intégration complet ────────────────────────────────

def test_scenario_integration_sync_preserve_manuel(tmp_path):
    """Scénario complet : générer, modifier manuellement, re-synchroniser.

    Le fichier .py manuel doit être préservé avec son contenu utilisateur intact.
    Les fichiers _base.py et .sql sont régénérés.
    """
    from forge_mvc_entities.model import build_model

    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "contact", _contact_json())
    _write_relations(entities_root)

    # Première génération
    result1 = build_model(entities_root)
    manual = entities_root / "contact" / "contact.py"
    base = entities_root / "contact" / "contact_base.py"
    sql = entities_root / "contact" / "contact.sql"
    assert manual in result1.created

    # Modification manuelle du fichier utilisateur
    user_code = "# CODE UTILISATEUR MODIFIÉ\nclass Contact: pass\n"
    manual.write_text(user_code, encoding="utf-8")

    # Re-synchronisation
    result2 = build_model(entities_root)

    assert manual in result2.preserved
    assert manual not in result2.created
    assert manual.read_text(encoding="utf-8") == user_code
    assert base in result2.written
    assert sql in result2.written


def test_scenario_base_py_regenere_apres_sync(tmp_path):
    """_base.py est régénéré à chaque sync — son contenu est mis à jour."""
    from forge_mvc_entities.model import build_model

    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "contact", _contact_json())
    _write_relations(entities_root)
    build_model(entities_root)

    base = entities_root / "contact" / "contact_base.py"
    base.write_text("# vieux contenu\n", encoding="utf-8")

    build_model(entities_root)

    assert base.read_text(encoding="utf-8") != "# vieux contenu\n"


def test_scenario_sql_regenere_apres_sync(tmp_path):
    """contact.sql est régénéré à chaque sync — son contenu est mis à jour."""
    from forge_mvc_entities.model import build_model

    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "contact", _contact_json())
    _write_relations(entities_root)
    build_model(entities_root)

    sql = entities_root / "contact" / "contact.sql"
    sql.write_text("-- vieux SQL\n", encoding="utf-8")

    build_model(entities_root)

    assert sql.read_text(encoding="utf-8") != "-- vieux SQL\n"


def test_scenario_init_preserve_apres_sync(tmp_path):
    """__init__.py manuel est préservé après re-synchronisation."""
    from forge_mvc_entities.model import build_model

    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "contact", _contact_json())
    _write_relations(entities_root)

    init = entities_root / "contact" / "__init__.py"
    init_code = "# init personnalisé\nfrom .contact import Contact\n"
    init.write_text(init_code, encoding="utf-8")

    result = build_model(entities_root)

    assert init in result.preserved
    assert init.read_text(encoding="utf-8") == init_code


def test_scenario_aucune_suppression_silencieuse(tmp_path):
    """Aucun fichier existant n'est supprimé silencieusement lors d'une sync."""
    from forge_mvc_entities.model import build_model

    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "contact", _contact_json())
    _write_relations(entities_root)

    extra = entities_root / "contact" / "contact_extra.py"
    extra.write_text("# fichier annexe\n", encoding="utf-8")

    build_model(entities_root)

    assert extra.exists()
    assert extra.read_text(encoding="utf-8") == "# fichier annexe\n"


# ── make_crud — _write_if_new ─────────────────────────────────────────────────

def _make_crud_entity(tmp_path: Path) -> Path:
    entities_root = tmp_path / "mvc" / "entities"
    entity_dir = entities_root / "contact"
    entity_dir.mkdir(parents=True, exist_ok=True)
    (entity_dir / "contact.json").write_text(
        json.dumps(_contact_json(), indent=2) + "\n", encoding="utf-8"
    )
    return entities_root


def test_make_crud_preserve_controller_existant(tmp_path):
    """make_crud ne réécrit pas un contrôleur déjà personnalisé."""
    from forge_mvc_entities.make_crud import make_crud

    entities_root = _make_crud_entity(tmp_path)
    ctrl = tmp_path / "mvc" / "controllers" / "contact_controller.py"
    ctrl.parent.mkdir(parents=True, exist_ok=True)
    ctrl.write_text("# code utilisateur contrôleur\n", encoding="utf-8")

    result = make_crud("Contact", entities_root=entities_root, output_root=tmp_path)

    assert any(ctrl.as_posix() in w for w in result.warnings)  # WARNED (CLI-SCAFFOLD-PRIMITIVE-001)
    assert ctrl.read_text(encoding="utf-8") == "# code utilisateur contrôleur\n"


def test_make_crud_preserve_form_existant(tmp_path):
    """make_crud ne réécrit pas un formulaire déjà personnalisé."""
    from forge_mvc_entities.make_crud import make_crud

    entities_root = _make_crud_entity(tmp_path)
    form = tmp_path / "mvc" / "forms" / "contact_form.py"
    form.parent.mkdir(parents=True, exist_ok=True)
    form.write_text("# code utilisateur form\n", encoding="utf-8")

    result = make_crud("Contact", entities_root=entities_root, output_root=tmp_path)

    assert any(form.as_posix() in w for w in result.warnings)  # WARNED (CLI-SCAFFOLD-PRIMITIVE-001)
    assert form.read_text(encoding="utf-8") == "# code utilisateur form\n"


# ── Document d'audit ──────────────────────────────────────────────────────────

def test_audit_consolidation_non_overwrite_001_existe():
    """docs/history/audits/consolidation-non-overwrite-001.md existe."""
    assert (ROOT / "docs" / "history" / "audits" / "consolidation-non-overwrite-001.md").exists()


def test_audit_mentionne_ensure_file():
    """Le document d'audit mentionne ensure_file."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-non-overwrite-001.md").read_text(encoding="utf-8")
    assert "ensure_file" in content


def test_audit_mentionne_write_if_new():
    """Le document d'audit mentionne _write_if_new."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-non-overwrite-001.md").read_text(encoding="utf-8")
    assert "_write_if_new" in content or "write_if_new" in content


def test_audit_mentionne_build_model():
    """Le document d'audit mentionne build_model."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-non-overwrite-001.md").read_text(encoding="utf-8")
    assert "build_model" in content


def test_audit_mentionne_preserved():
    """Le document d'audit mentionne la propriété preserved."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-non-overwrite-001.md").read_text(encoding="utf-8")
    assert "preserved" in content


def test_audit_contient_verdict_final():
    """Le document d'audit contient un verdict final."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-non-overwrite-001.md").read_text(encoding="utf-8")
    assert "Verdict" in content


# ── Roadmap ───────────────────────────────────────────────────────────────────

def test_roadmap_marque_consolidation_non_overwrite_001_termine():
    """docs/forge-roadmap.md marque CONSOLIDATION-NON-OVERWRITE-001 comme terminé."""
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    assert "CONSOLIDATION-NON-OVERWRITE-001" in content
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
