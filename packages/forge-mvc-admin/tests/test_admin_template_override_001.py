"""Test ADMIN-TEMPLATE-OVERRIDE-001 : surcharge des templates admin par le projet.

Forge Admin embarque ses templates (`admin/*.html`) et les enregistre auprès du
cœur (ADR-046). L'ordre des loaders (projet d'abord, paquet ensuite) permet à un
projet de surcharger un template par défaut en plaçant un fichier de même chemin
sous `mvc/views/admin/`. Ce test verrouille cette propriété.
"""
from __future__ import annotations

from pathlib import Path

import pytest

# Importer le paquet enregistre son PackageLoader de templates auprès du cœur.
pytest.importorskip("forge_mvc_admin")

from integrations.jinja2.renderer import Jinja2Renderer


def test_template_du_paquet_par_defaut(tmp_path: Path):
    # Sans surcharge projet, c'est le template embarqué du paquet qui rend.
    views = tmp_path / "views"
    views.mkdir()
    renderer = Jinja2Renderer(str(views))
    html = renderer.render("admin/dashboard.html", {"resources": ()})
    assert "Ressources administrables" in html


def test_le_projet_surcharge_le_template_admin(tmp_path: Path):
    # Un admin/dashboard.html du projet masque le template par défaut du paquet.
    views = tmp_path / "views"
    (views / "admin").mkdir(parents=True)
    (views / "admin" / "dashboard.html").write_text(
        "TABLEAU DE BORD MAISON", encoding="utf-8"
    )
    renderer = Jinja2Renderer(str(views))
    html = renderer.render("admin/dashboard.html", {"resources": ()})
    assert html.strip() == "TABLEAU DE BORD MAISON"
    assert "Ressources administrables" not in html
