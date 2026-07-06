"""Garde-fou SKELETON-500-ERROR-CONTEXT-001.

Incident : la page 500 du squelette n'affichait jamais le détail de l'exception,
même en développement, parce que `app.py` rendait `errors/500.html` **sans
contexte** — le bloc `{% if error %}` du template restait toujours faux.

Le squelette doit :
- définir `_error_context()` qui ne renvoie le détail (type/message/traceback)
  **qu'en développement** (`APP_ENV == "dev"`) et `None` sinon (pas de fuite de
  traceback en production) ;
- passer ce contexte aux deux rendus de `errors/500.html` (GET et requêtes
  dynamiques), donc ne plus appeler la forme sans contexte.

Test structurel (lecture de texte ; `app.py` n'est pas importable hors d'un
projet généré). L'identité `app.py` racine == squelette est garantie ailleurs
(test_skeleton_tree_001 : anti-dérive ADR-024).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
APP_PY = PROJECT_ROOT / "skeleton" / "data" / "app.py"


def _src() -> str:
    return APP_PY.read_text(encoding="utf-8")


def test_import_traceback_present():
    assert "import traceback" in _src()


def test_helper_error_context_defini():
    assert "def _error_context(" in _src()


def test_error_context_gate_sur_dev():
    src = _src()
    assert 'APP_ENV != "dev"' in src or 'APP_ENV == "dev"' in src, (
        "_error_context() doit conditionner le détail au mode dev pour ne pas "
        "exposer de traceback en production."
    )
    assert "traceback.format_exc()" in src


def test_les_deux_rendus_500_passent_le_contexte():
    src = _src()
    assert '_html("errors/500.html", 500, _error_context())' in src
    assert src.count('_html("errors/500.html", 500, _error_context())') == 2, (
        "Les deux points de rendu de la 500 (GET et requêtes dynamiques) doivent "
        "passer _error_context()."
    )


def test_plus_de_rendu_500_sans_contexte():
    # La forme sans contexte (cause de l'incident) ne doit plus exister.
    assert '_html("errors/500.html", 500)' not in _src()


# ── Détail dev des pages 404 / 413 (SKELETON-ERROR-PAGES-DEV-DETAIL-001) ──────

ERRORS_DIR = PROJECT_ROOT / "skeleton" / "data" / "mvc" / "views" / "errors"


def test_helper_dev_error_gate_sur_dev():
    src = _src()
    assert "def _dev_error(" in src
    assert 'APP_ENV == "dev"' in src, (
        "_dev_error() doit renvoyer le détail seulement en dev (None en prod)."
    )


def test_413_passe_la_taille_recue_en_dev():
    src = _src()
    assert '_html("errors/413.html", 413, _dev_error({"received"' in src


def test_404_passe_le_chemin_en_dev():
    src = _src()
    assert '_html("errors/404.html", 404, _dev_error({"path": path}))' in src
    assert '_html("errors/404.html", 404)' not in src


def test_templates_404_413_ont_un_bloc_detail():
    for name, var in [("404.html", "error.path"), ("413.html", "error.received")]:
        content = (ERRORS_DIR / name).read_text(encoding="utf-8")
        assert "{% if error %}" in content, f"{name} doit avoir un bloc {{% if error %}}."
        assert var in content, f"{name} doit afficher {{{{ {var} }}}}."
        assert "APP_ENV=dev" in content, f"{name} doit rappeler que le détail est dev-only."
