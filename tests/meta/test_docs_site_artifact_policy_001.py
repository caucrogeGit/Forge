"""Garde-fou DOCS-SITE-ARTIFACT-POLICY-001 (révisé ADR-044).

Verrouille la politique des couches documentaires Forge :

  * ``docs/`` — **source documentaire canonique** suivie par Git ;
  * ``docs/index.html`` — **landing canonique**, éditée directement
    (ADR-044 : plus de génération par ``forge sync:landing``) ;
  * ``site/`` — **artefact** généré par ``mkdocs build``, jamais
    canonique, ignoré par ``.gitignore``, supprimable sans perte.

Le test vérifie :

  1. ``.gitignore`` ignore ``site/`` (pattern explicite) ;
  2. ``docs/`` n'apparaît PAS comme entrée ignorée ;
  3. la documentation de contribution mentionne ces rôles ;
  4. ``docs/index.html`` est documentée comme landing canonique éditée
     directement.

Les assertions visent la **présence des notions** plus que le texte
exact — la doc reste réécrivable éditorialement.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


_REPO_ROOT = Path(__file__).resolve().parents[2]
_GITIGNORE = _REPO_ROOT / ".gitignore"
_CONTRIBUTING = _REPO_ROOT / "docs" / "philosophy" / "contributing.md"


# ---------------------------------------------------------------------------
# .gitignore — site/ doit être ignoré, docs/ doit rester suivi
# ---------------------------------------------------------------------------


def _gitignore_lines() -> list[str]:
    text = _GITIGNORE.read_text(encoding="utf-8")
    out = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        out.append(line)
    return out


class TestGitignore:
    def test_gitignore_exists(self):
        assert _GITIGNORE.is_file(), ".gitignore doit exister."

    def test_site_is_ignored(self):
        lines = _gitignore_lines()
        # Tolère plusieurs formes équivalentes.
        accepted = {"site/", "site", "/site/", "/site"}
        assert any(line in accepted for line in lines), (
            "`.gitignore` doit ignorer `site/` (artefact MkDocs). "
            "Ajouter la ligne `site/` au .gitignore."
        )

    def test_docs_is_not_ignored(self):
        """Pattern interdits : `docs/`, `docs`, `/docs/`, `/docs`.

        Note : on tolère des sous-chemins ignorés (`docs/_drafts/`, etc.)
        si besoin futur — seule l'exclusion racine du dossier est refusée.
        """
        forbidden = {"docs/", "docs", "/docs/", "/docs"}
        offenders = [line for line in _gitignore_lines() if line in forbidden]
        assert not offenders, (
            f"`.gitignore` ne doit PAS ignorer `docs/` (source documentaire "
            f"canonique). Lignes problématiques : {offenders}."
        )


# ---------------------------------------------------------------------------
# Documentation — la politique est expliquée dans docs/philosophy/contributing.md
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def contributing_text() -> str:
    assert _CONTRIBUTING.is_file(), (
        f"{_CONTRIBUTING.relative_to(_REPO_ROOT)} doit exister."
    )
    return _CONTRIBUTING.read_text(encoding="utf-8")


class TestDocumentedPolicy:
    """La politique 3-couches doit être documentée dans le guide
    contributeur, avec les 4 chemins identifiés et la commande de
    synchronisation."""

    def test_mentions_docs_as_source(self, contributing_text):
        """``docs/`` est la source documentaire canonique."""
        # On cherche une mention conjointe de `docs/` et d'un mot évoquant
        # « source canonique ».
        assert "docs/" in contributing_text
        assert re.search(
            r"docs/[^\n]{0,200}(source|canonique)",
            contributing_text,
            re.IGNORECASE | re.DOTALL,
        ), (
            "La documentation doit présenter `docs/` comme source documentaire "
            "(mot clé `source` ou `canonique` à proximité)."
        )

    def test_mentions_site_as_generated_artifact(self, contributing_text):
        """``site/`` est un artefact MkDocs, jamais une référence."""
        assert "site/" in contributing_text
        # `site/` doit être qualifié de généré / artefact / mkdocs / supprimable.
        markers = ("artefact", "généré", "mkdocs build", "supprimable")
        joined = contributing_text.lower()
        assert any(m in joined for m in markers), (
            "La documentation doit qualifier `site/` comme artefact / généré "
            "par `mkdocs build` / supprimable sans perte."
        )

    def test_mentions_landing_canonical(self, contributing_text):
        """``docs/index.html`` est la landing canonique (ADR-044)."""
        assert "docs/index.html" in contributing_text, (
            "La documentation doit identifier `docs/index.html` "
            "comme landing canonique publique."
        )

    def test_landing_edited_directly(self, contributing_text):
        """``docs/index.html`` est éditée directement, pas générée (ADR-044)."""
        assert "docs/index.html" in contributing_text, (
            "La documentation doit mentionner `docs/index.html` (landing canonique)."
        )
        markers = ("canonique", "directement", "éditer", "à la main")
        joined = contributing_text.lower()
        assert any(m in joined for m in markers), (
            "La documentation doit indiquer que `docs/index.html` est la "
            "landing canonique éditée directement (ADR-044)."
        )


# ---------------------------------------------------------------------------
# Cohérence finale — site/ ne doit jamais être suivi par Git
# ---------------------------------------------------------------------------


class TestSiteNotTracked:
    """Au-delà de `.gitignore`, on vérifie qu'aucun fichier `site/...`
    n'est effectivement suivi par Git (catch accidentel commit)."""

    def test_no_tracked_file_under_site(self):
        import subprocess
        result = subprocess.run(
            ["git", "ls-files", "site/"],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        tracked = [line for line in result.stdout.splitlines() if line.strip()]
        assert not tracked, (
            f"Des fichiers sous `site/` sont suivis par Git : {tracked[:5]} "
            "(et possiblement plus). `site/` est un artefact MkDocs — le "
            "retirer de l'index avec `git rm -r --cached site/`."
        )
