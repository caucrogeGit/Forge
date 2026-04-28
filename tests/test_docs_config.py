import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def _load_mkdocs_yaml() -> dict:
    """Charge mkdocs.yml en supprimant les tags YAML Python incompatibles avec safe_load."""
    text = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    text = re.sub(r"!!python/\S+", '""', text)
    return yaml.safe_load(text)


def test_mkdocs_nav_entries_are_well_formed_and_point_to_existing_docs():
    config = _load_mkdocs_yaml()
    nav = config["nav"]
    nav_targets = _flatten_nav(nav)
    nav_labels = {label for label, _ in nav_targets}

    for required in (
        "Installation",
        "Premiers pas",
        "Comprendre Forge",
        "Starter apps",
        "Référence",
        "Projet",
        "Vue d'ensemble",
        "Avec pipx",
        "Depuis GitHub",
        "Mode développement",
        "Préparer MariaDB",
        "Guide de démarrage",
        "CRUD explicite",
        "Concepts",
        "Positionnement",
        "Architecture des entités",
        "Présentation",
        "Niveau 1 — Contacts",
        "Niveau 2 — Utilisateurs/auth",
        "Niveau 3 — Carnet relationnel",
        "Niveau 4 — Suivi pédagogique",
        "API et CLI",
        "Roadmap",
    ):
        assert required in nav_labels

    for _, target in nav_targets:
        if target is None:
            continue
        if target.startswith("http"):
            continue
        assert (ROOT / "docs" / target).exists()


def _flatten_nav(entries):
    flattened = []
    for entry in entries:
        assert isinstance(entry, dict)
        for label, target in entry.items():
            if isinstance(target, list):
                flattened.append((label, None))
                flattened.extend(_flatten_nav(target))
            else:
                flattened.append((label, target))
    return flattened
