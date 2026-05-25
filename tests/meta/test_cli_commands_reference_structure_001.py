"""Garde-fou DOCS-CLI-COMMANDS-EXAMPLES-RESTRUCTURE-001.

Verrouille la structure pédagogique de ``docs/reference/cli-commands.md`` :

  * vue d'ensemble + tableau des commandes essentielles ;
  * parcours rapides (scénarios d'enchaînement) ;
  * référence complète par domaine — sections existantes intactes ;
  * section dédiée aux modules opt-in (avec rappel qu'ils restent optionnels) ;
  * index alphabétique en fin de page.

Les assertions visent la **présence des sections** et de **marqueurs
sémantiques** stables, jamais le texte exact d'un paragraphe — pour
permettre une réécriture éditoriale future sans casser le garde-fou.
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
    def test_has_vue_d_ensemble(self, doc_text):
        assert re.search(r"^##\s+Vue d'ensemble", doc_text, re.MULTILINE), (
            "La page doit ouvrir sur une section « Vue d'ensemble »."
        )

    def test_has_commandes_essentielles(self, doc_text):
        assert re.search(r"^##\s+Commandes essentielles", doc_text, re.MULTILINE), (
            "La page doit contenir une section « Commandes essentielles »."
        )

    def test_has_parcours_rapides(self, doc_text):
        assert re.search(r"^##\s+Parcours rapides", doc_text, re.MULTILINE), (
            "La page doit contenir une section « Parcours rapides »."
        )

    def test_has_modules_opt_in(self, doc_text):
        assert re.search(r"^##\s+Modules opt-in", doc_text, re.MULTILINE), (
            "La page doit contenir une section dédiée aux modules opt-in."
        )

    def test_has_index_alphabetique(self, doc_text):
        assert re.search(r"^##\s+Index alphab[ée]tique", doc_text, re.MULTILINE), (
            "La page doit se terminer par un index alphabétique des commandes."
        )

    def test_command_reference_uses_api_like_details(self, doc_text):
        command_cards = re.findall(
            r"<details markdown=\"1\" id=\"forge-[^\"]+\">\n"
            r"<summary><code>forge [^<]+</code> - ",
            doc_text,
        )
        assert len(command_cards) >= 40, (
            "La référence CLI doit présenter les commandes comme l'index API : "
            f"blocs <details> repliables avec summary. Vu : {len(command_cards)}."
        )

    def test_sections_appear_in_expected_order(self, doc_text):
        """Vue d'ensemble → Essentielles → Parcours → … → Index alpha en fin."""
        order_required = [
            r"^##\s+Vue d'ensemble",
            r"^##\s+Commandes essentielles",
            r"^##\s+Parcours rapides",
            r"^##\s+Modules opt-in",
            r"^##\s+Index alphab[ée]tique",
        ]
        positions = []
        for pattern in order_required:
            match = re.search(pattern, doc_text, re.MULTILINE)
            assert match is not None, f"Section manquante : {pattern}"
            positions.append(match.start())
        assert positions == sorted(positions), (
            f"Les sections ne sont pas dans l'ordre attendu : positions = {positions}"
        )


# ---------------------------------------------------------------------------
# Contenu — parcours rapides, exemples, opt-ins
# ---------------------------------------------------------------------------


class TestParcoursRapidesContent:
    """Les parcours rapides doivent enchaîner des commandes Forge dans des
    blocs ``bash``. On ne vérifie pas le texte exact des explications,
    mais la présence d'au moins quelques scénarios concrets avec commandes."""

    def test_contains_bash_blocks(self, doc_text):
        bash_blocks = re.findall(r"```bash\n", doc_text)
        assert len(bash_blocks) >= 10, (
            f"La page doit contenir plusieurs blocs `bash` d'exemple, "
            f"vu : {len(bash_blocks)}."
        )

    def test_parcours_section_contains_forge_commands(self, doc_text):
        """Au moins deux commandes Forge enchaînées dans la section parcours."""
        m_start = re.search(r"^##\s+Parcours rapides", doc_text, re.MULTILINE)
        m_end = re.search(
            r"^##\s+Commandes de projet",
            doc_text[m_start.end():],
            re.MULTILINE,
        )
        section = doc_text[m_start.end(): m_start.end() + m_end.start()]
        # Compte des commandes `forge ...` (hors imports / autres).
        forge_calls = re.findall(r"\bforge\s+[a-z]+(?::[a-z\-]+)*\b", section)
        assert len(forge_calls) >= 5, (
            f"La section « Parcours rapides » doit montrer plusieurs "
            f"commandes Forge enchaînées ; vu : {len(forge_calls)}."
        )


class TestOptInSection:
    def test_opt_in_section_lists_packages(self, doc_text):
        m = re.search(r"^##\s+Modules opt-in", doc_text, re.MULTILINE)
        assert m is not None
        # Coupe la section opt-in jusqu'à la section suivante (## ...).
        rest = doc_text[m.end():]
        next_h2 = re.search(r"^##\s+", rest, re.MULTILINE)
        section = rest[: next_h2.start()] if next_h2 else rest

        # Les cinq opt-ins officiels doivent être mentionnés au moins par leur paquet.
        for pkg in ("forge-mvc-rbac", "forge-mvc-workflow", "forge-mvc-stats",
                    "forge-mvc-mfa", "forge-mvc-media"):
            assert pkg in section, (
                f"La section Modules opt-in doit mentionner `{pkg}`."
            )

    def test_opt_in_section_states_optional_nature(self, doc_text):
        """Le rappel « les opt-ins restent optionnels / le core n'en dépend pas »
        est obligatoire — éviter qu'un lecteur croie qu'un opt-in est requis."""
        m = re.search(r"^##\s+Modules opt-in", doc_text, re.MULTILINE)
        rest = doc_text[m.end():]
        next_h2 = re.search(r"^##\s+", rest, re.MULTILINE)
        section = rest[: next_h2.start()] if next_h2 else rest
        markers = ("optionnel", "opt-in", "ne dépend")
        assert any(m in section.lower() for m in markers), (
            "La section Modules opt-in doit rappeler explicitement leur "
            "nature optionnelle (le core ne dépend d'aucun opt-in)."
        )


# ---------------------------------------------------------------------------
# Index alphabétique — exhaustivité minimale
# ---------------------------------------------------------------------------


class TestAlphabeticalIndex:
    def _index_section(self, doc_text: str) -> str:
        m = re.search(r"^##\s+Index alphab[ée]tique", doc_text, re.MULTILINE)
        assert m is not None, "Section Index alphabétique manquante."
        return doc_text[m.end():]

    def test_index_lists_core_essentials(self, doc_text):
        section = self._index_section(doc_text)
        essentials = [
            "forge new",
            "forge doctor",
            "forge project:check",
            "forge routes:list",
            "forge make:entity",
            "forge make:crud",
            "forge migration:apply",
        ]
        for cmd in essentials:
            assert f"`{cmd}`" in section, (
                f"L'index alphabétique doit lister `{cmd}`."
            )

    def test_index_marks_opt_in_status(self, doc_text):
        """Au moins une commande RBAC doit apparaître avec statut opt-in."""
        section = self._index_section(doc_text)
        line_rbac = next(
            (line for line in section.splitlines()
             if "rbac:validate" in line or "rbac:audit" in line),
            None,
        )
        assert line_rbac is not None, "RBAC absent de l'index."
        assert "Opt-in" in line_rbac or "opt-in" in line_rbac, (
            "Les commandes RBAC doivent être marquées « Opt-in » dans l'index."
        )


# ---------------------------------------------------------------------------
# Fiches de commandes principales — annotations attendues
# ---------------------------------------------------------------------------


class TestPrincipalCommandsHaveStatusAndConfusionNotes:
    """Les commandes principales doivent annoncer leur statut et lister
    leurs faux-jumeaux pour éviter les confusions documentées."""

    def _command_block(self, doc_text: str, anchor_command: str) -> str:
        title_pattern = (
            r"<details markdown=\"1\" id=\"[^\"]+\">\n"
            + re.escape(f"<summary><code>{anchor_command}</code>")
            + r".*?</summary>\n(?P<body>.*?)\n</details>"
        )
        match = re.search(title_pattern, doc_text, re.DOTALL)
        assert match is not None, f"Commande `{anchor_command}` absente."
        return match.group("body")

    @pytest.mark.parametrize("anchor_command", [
        "forge make:crud",
        "forge doctor",
        "forge project:check",
    ])
    def test_command_card_states_status_core(self, doc_text, anchor_command):
        block = self._command_block(doc_text, anchor_command)
        assert "Statut" in block and "core" in block.lower(), (
            f"La fiche `{anchor_command}` doit mentionner « **Statut :** core »."
        )

    @pytest.mark.parametrize("anchor_command", [
        "forge make:crud",
        "forge doctor",
    ])
    def test_command_card_lists_confusions(self, doc_text, anchor_command):
        block = self._command_block(doc_text, anchor_command)
        assert "confondre" in block.lower(), (
            f"La fiche `{anchor_command}` doit lister les commandes proches "
            "via une note « À ne pas confondre avec »."
        )
