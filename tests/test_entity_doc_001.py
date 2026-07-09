"""ENTITY-DOC-001 — la commande `forge entity:doc`.

Vérifie la vue globale Markdown des entités et relations (tableaux + cardinalité
+ diagramme Mermaid), le mode affichage (stdout) et le mode `--output`, et
l'enregistrement CLI.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from forge_mvc_entities.entity_doc import build_entity_doc, main

_REPO_ROOT = Path(__file__).resolve().parent.parent
FORGE_PY = _REPO_ROOT / "forge.py"


def _project(tmp_path: Path) -> Path:
    ents = tmp_path / "mvc" / "entities"
    for name, table, fields in [
        ("AnneeScolaire", "annee_scolaire", [{"name": "libelle", "type": "string", "max_length": 50, "required": True}]),
        ("Classe", "classe", [{"name": "code", "type": "string", "max_length": 50, "required": True}]),
        ("Tag", "tag", [{"name": "nom", "type": "string", "max_length": 40, "required": True}]),
        ("Article", "article", [{"name": "titre", "type": "string", "max_length": 120, "required": True}]),
    ]:
        d = ents / name.lower()
        d.mkdir(parents=True)
        (d / f"{name.lower()}.json").write_text(
            json.dumps({"schema_version": "1.0", "name": name, "table": table, "fields": fields}),
            encoding="utf-8",
        )
    (ents / "relations.json").write_text(
        json.dumps({"schema_version": "1.0", "relations": [
            {"type": "many_to_one", "from": "Classe", "to": "AnneeScolaire", "name": "annee_scolaire",
             "foreign_key": "annee_scolaire_id", "on_delete": "restrict", "nullable": True, "index": True},
            {"type": "many_to_many", "from": "Article", "to": "Tag", "name": "tags",
             "pivot": {"table": "article_tag", "from_key": "article_id", "to_key": "tag_id",
                       "id": True, "unique_pair": True, "on_delete": "cascade", "fields": []}},
        ]}),
        encoding="utf-8",
    )
    return ents


# ── Contenu de la documentation ──────────────────────────────────────────────

def test_doc_contient_tableau_par_entite(tmp_path):
    doc = build_entity_doc(_project(tmp_path))
    assert "### AnneeScolaire (`annee_scolaire`)" in doc
    assert "| Champ | Colonne | Type SQL | Type Python | Nullable | PK | Unique |" in doc
    assert "| id | Id | BIGINT UNSIGNED | int | non | oui | non |" in doc


def test_doc_liste_relations_avec_cardinalite(tmp_path):
    doc = build_entity_doc(_project(tmp_path))
    assert "| Classe | AnneeScolaire | `annee_scolaire_id` | N:1 | RESTRICT |" in doc
    assert "| Article | Tag | `article_tag` (pivot) | N:N | CASCADE |" in doc


def test_doc_contient_diagramme_mermaid(tmp_path):
    doc = build_entity_doc(_project(tmp_path))
    assert "```mermaid" in doc
    assert "erDiagram" in doc
    assert 'CLASSE }o--|| ANNEE_SCOLAIRE : "annee_scolaire_id"' in doc
    assert "ARTICLE }o--o{ TAG : \"article_tag\"" in doc


def test_doc_projet_sans_entite(tmp_path):
    ents = tmp_path / "mvc" / "entities"
    ents.mkdir(parents=True)
    doc = build_entity_doc(ents)
    assert "Aucune entité déclarée" in doc


# ── Modes de sortie ──────────────────────────────────────────────────────────

def test_affiche_sur_stdout_par_defaut(tmp_path, capsys, monkeypatch):
    _project(tmp_path)
    monkeypatch.chdir(tmp_path)
    main([])
    out = capsys.readouterr().out
    assert "# Schéma des entités" in out
    assert not (tmp_path / "ENTITES.md").exists()


def test_output_ecrit_le_fichier(tmp_path, capsys, monkeypatch):
    _project(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["--output", "ENTITES.md"])
    out = capsys.readouterr().out
    target = tmp_path / "ENTITES.md"
    assert target.exists()
    assert "erDiagram" in target.read_text(encoding="utf-8")
    assert "[OK]" in out


def test_output_sans_chemin_echoue(tmp_path, monkeypatch):
    _project(tmp_path)
    monkeypatch.chdir(tmp_path)
    try:
        main(["--output"])
        raise AssertionError("attendu SystemExit")
    except SystemExit as exc:
        assert exc.code == 1


# ── Enregistrement CLI ───────────────────────────────────────────────────────

def test_forge_py_dispatche_entity_doc():
    from forge import CORE_COMMANDS
    assert "entity:doc" in CORE_COMMANDS


def test_forge_help_liste_entity_doc():
    result = subprocess.run(
        [sys.executable, str(FORGE_PY), "help"],
        capture_output=True, text=True, timeout=30,
    )
    assert "entity:doc" in result.stdout


def test_help_rend_sans_effet():
    result = subprocess.run(
        [sys.executable, str(FORGE_PY), "entity:doc", "--help"],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0
    assert "entity:doc" in result.stdout
