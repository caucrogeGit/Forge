"""Garde-fou DOCS-CLI-COMMANDS-CATALOG-001.

Verrouille la structure du **catalogue concis** ``docs/reference/cli-commands.md``
(refonte DOCS-CLI-COMMANDS-CATALOG-001 : la page n'est plus une référence riche
à fiches ``<details>`` repliables, mais un catalogue de navigation où chaque
commande tient sur une ligne de tableau, avec un lien vers sa page dédiée) :

  * une section « Parcours rapides » en tête, avec des scénarios d'enchaînement ;
  * des sections de domaine (H2) listant les commandes en tableaux ;
  * les commandes essentielles du cœur sont présentes ;
  * chaque commande est listée comme ``| `forge <cmd>` | … |``.

Les assertions visent la **présence des sections** et de **marqueurs
sémantiques** stables, jamais le texte exact d'un paragraphe, pour permettre
une réécriture éditoriale future sans casser le garde-fou.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

_CLI_DOC = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "reference"
    / "cli-commands.md"
)


@pytest.fixture(scope="module")
def doc_text() -> str:
    assert _CLI_DOC.is_file(), f"{_CLI_DOC} doit exister."
    return _CLI_DOC.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Structure de haut niveau
# ---------------------------------------------------------------------------


class TestTopLevelStructure:
    def test_has_title(self, doc_text):
        assert re.search(r"^#\s+Référence des commandes Forge", doc_text, re.MULTILINE), (
            "La page doit ouvrir sur le titre « Référence des commandes Forge »."
        )

    def test_has_parcours_rapides(self, doc_text):
        assert re.search(r"^##\s+Parcours rapides", doc_text, re.MULTILINE), (
            "La page doit contenir une section « Parcours rapides »."
        )

    def test_parcours_appears_before_domain_sections(self, doc_text):
        """« Parcours rapides » ouvre le catalogue, avant les sections de domaine."""
        m_parcours = re.search(r"^##\s+Parcours rapides", doc_text, re.MULTILINE)
        m_projet = re.search(r"^##\s+Projet", doc_text, re.MULTILINE)
        assert m_parcours is not None and m_projet is not None
        assert m_parcours.start() < m_projet.start(), (
            "La section « Parcours rapides » doit précéder les sections de domaine."
        )

    def test_has_enough_domain_sections(self, doc_text):
        """Le catalogue regroupe les commandes en au moins 10 sections H2."""
        h2_count = len(re.findall(r"^## [A-Z]", doc_text, re.MULTILINE))
        assert h2_count >= 10, (
            f"cli-commands.md doit avoir au moins 10 sections H2 (groupes de "
            f"commandes). Trouvé : {h2_count}."
        )


# ---------------------------------------------------------------------------
# Contenu — parcours rapides
# ---------------------------------------------------------------------------


class TestParcoursRapidesContent:
    """Les parcours rapides doivent enchaîner des commandes Forge dans des
    blocs ``bash``. On ne vérifie pas le texte exact des explications,
    mais la présence d'au moins quelques scénarios concrets avec commandes."""

    def _parcours_section(self, doc_text: str) -> str:
        m_start = re.search(r"^##\s+Parcours rapides", doc_text, re.MULTILINE)
        assert m_start is not None, "Section « Parcours rapides » manquante."
        m_end = re.search(r"^##\s+Projet", doc_text[m_start.end():], re.MULTILINE)
        assert m_end is not None, (
            "Une section de domaine doit suivre « Parcours rapides »."
        )
        return doc_text[m_start.end(): m_start.end() + m_end.start()]

    def test_contains_bash_blocks(self, doc_text):
        section = self._parcours_section(doc_text)
        bash_blocks = re.findall(r"```bash\n", section)
        assert len(bash_blocks) >= 3, (
            f"La section « Parcours rapides » doit contenir plusieurs blocs "
            f"`bash` d'exemple, vu : {len(bash_blocks)}."
        )

    def test_parcours_section_contains_forge_commands(self, doc_text):
        """Au moins cinq commandes Forge enchaînées dans la section parcours."""
        section = self._parcours_section(doc_text)
        forge_calls = re.findall(r"\bforge\s+[a-z]+(?::[a-z\-]+)*\b", section)
        assert len(forge_calls) >= 5, (
            f"La section « Parcours rapides » doit montrer plusieurs "
            f"commandes Forge enchaînées ; vu : {len(forge_calls)}."
        )


# ---------------------------------------------------------------------------
# Catalogue — commandes listées en tableaux
# ---------------------------------------------------------------------------


class TestCommandCatalog:
    def test_commands_listed_as_table_rows(self, doc_text):
        """Chaque commande tient sur une ligne de tableau « | `forge <cmd>` | … »."""
        rows = re.findall(r"^\|\s*`forge [a-z][a-z0-9:_-]*`", doc_text, re.MULTILINE)
        assert len(rows) >= 30, (
            f"Le catalogue doit lister les commandes en tableaux "
            f"(« | `forge <cmd>` | … »). Lignes vues : {len(rows)}."
        )

    @pytest.mark.parametrize("command", [
        "forge new",
        "forge doctor",
        "forge project:check",
        "forge routes:list",
        "forge make:entity",
        "forge make:crud",
        "forge migration:apply",
    ])
    def test_core_essentials_listed(self, doc_text, command):
        assert f"`{command}`" in doc_text, (
            f"Le catalogue doit lister la commande essentielle `{command}`."
        )
