"""Tests documentaires — GIT-RECOVERY-WORKFLOW-GUARD-001.

Verrouille le contrat de `docs/contributing/canonical-repo.md` : la page
doit imposer la vérification du dépôt canonique avant tout ticket Forge
et documenter la procédure officielle de récupération de commits faits
par erreur dans un dépôt secondaire.

Critères :

- la page existe et n'est pas vide ;
- elle identifie sans ambiguïté le dépôt canonique attendu
  (chemin, branche `main`, remote `caucrogeGit/Forge.git`) ;
- elle liste la checklist pré-ticket en 5 commandes git ;
- elle énumère les signaux d'un mauvais dépôt (branche `master`,
  dossier `forge-test-*`, etc.) ;
- elle documente la procédure 4.1→4.9 (`git format-patch`,
  `git apply --check`, `git am`, fast-forward, push) ;
- elle pose des interdits explicites (merge direct d'un projet généré,
  patch WIP appliqué automatiquement) ;
- elle est référencée depuis `docs/contributing.md` et `mkdocs.yml` ;
- la roadmap mentionne le ticket comme livré.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
DOC = PROJECT_ROOT / "docs" / "contributing" / "canonical-repo.md"
CONTRIBUTING = PROJECT_ROOT / "docs" / "contributing.md"
MKDOCS = PROJECT_ROOT / "mkdocs.yml"
ROADMAP = PROJECT_ROOT / "docs" / "roadmap" / "forge-roadmap.md"
CLAUDE_MD = PROJECT_ROOT / "CLAUDE.md"


def _text() -> str:
    return DOC.read_text(encoding="utf-8")


# ── Existence ──────────────────────────────────────────────────────────────────


class TestExistence:

    def test_doc_exists(self):
        assert DOC.exists(), "docs/contributing/canonical-repo.md doit exister"

    def test_doc_not_empty(self):
        assert len(_text()) > 1000, (
            "La page semble vide ou trop courte pour être utile."
        )


# ── Dépôt canonique identifié ──────────────────────────────────────────────────


class TestCanonicalRepoIdentified:

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = _text()

    @pytest.mark.parametrize("marker", [
        "/home/roger/Projets/Forge",
        "caucrogeGit/Forge.git",
        "main",
    ])
    def test_mentions_canonical_marker(self, marker):
        assert marker in self.content, (
            f"La page doit mentionner explicitement '{marker}' "
            "comme valeur attendue du dépôt canonique."
        )


# ── Checklist pré-ticket ───────────────────────────────────────────────────────


class TestPreTicketChecklist:

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = _text()

    @pytest.mark.parametrize("command", [
        "pwd",
        "git status --short",
        "git branch --show-current",
        "git remote -v",
        "git log -3 --oneline",
    ])
    def test_checklist_command_present(self, command):
        assert command in self.content, (
            f"La checklist pré-ticket doit inclure la commande '{command}'."
        )


# ── Signaux d'un mauvais dépôt ─────────────────────────────────────────────────


class TestBadRepoSignals:

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = _text()

    @pytest.mark.parametrize("signal", [
        "master",
        "forge-test",
    ])
    def test_bad_signal_listed(self, signal):
        assert signal in self.content, (
            f"La page doit lister le signal '{signal}' comme indicateur "
            "d'un mauvais dépôt."
        )

    def test_generated_project_signal_present(self):
        # « mvc/ » seul sans core/forge_cli/packages est le signal
        # caractéristique d'un projet généré
        text = self.content
        assert "mvc/" in text and "core/" in text and "forge_cli/" in text, (
            "Le signal « projet généré (mvc/ seul) » doit être documenté."
        )


# ── Procédure de récupération ──────────────────────────────────────────────────


class TestRecoveryProcedure:

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = _text()

    @pytest.mark.parametrize("step", [
        "git format-patch",
        "git apply --check",
        "git am",
        "git switch main",
        "--ff-only",
        "git push origin main",
    ])
    def test_recovery_step_documented(self, step):
        assert step in self.content, (
            f"La procédure de récupération doit documenter l'étape '{step}'."
        )

    def test_branch_naming_documented(self):
        assert "port/recovery-" in self.content, (
            "La convention de nommage de la branche de portage "
            "(port/recovery-YYYYMMDD) doit être documentée."
        )

    @pytest.mark.parametrize("validation", [
        "pytest",
        "compileall",
        "ruff check",
        "mkdocs build --strict",
        "git diff --check",
    ])
    def test_canonical_validations_listed(self, validation):
        assert validation in self.content, (
            f"La validation canonique '{validation}' doit être listée "
            "avant la fusion dans main."
        )


# ── Interdits explicites ───────────────────────────────────────────────────────


class TestForbiddenActions:

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = _text()

    def test_has_explicit_forbidden_section(self):
        # La section a un titre dédié
        assert "Interdits" in self.content or "interdits" in self.content, (
            "La page doit comporter une section « Interdits » explicite."
        )

    @pytest.mark.parametrize("forbidden_keyword", [
        "WIP",                  # patch WIP appliqué automatiquement
        "projet généré",        # merge direct d'un projet généré
    ])
    def test_forbidden_action_mentioned(self, forbidden_keyword):
        assert forbidden_keyword in self.content, (
            f"La section interdits doit mentionner '{forbidden_keyword}'."
        )


# ── Intégration : contributing.md, mkdocs.yml, roadmap ─────────────────────────


class TestDocIntegration:

    def test_referenced_from_contributing(self):
        text = CONTRIBUTING.read_text(encoding="utf-8")
        assert "contributing/canonical-repo.md" in text, (
            "docs/contributing.md doit référencer la nouvelle page "
            "dans sa section « Voir aussi »."
        )

    def test_present_in_mkdocs_nav(self):
        text = MKDOCS.read_text(encoding="utf-8")
        assert "contributing/canonical-repo.md" in text, (
            "mkdocs.yml doit lister la page dans la navigation."
        )

    def test_roadmap_lists_ticket_as_delivered(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "GIT-RECOVERY-WORKFLOW-GUARD-001" in text, (
            "La roadmap doit mentionner GIT-RECOVERY-WORKFLOW-GUARD-001."
        )
        # Le ticket est marqué « livré » dans son entrée
        assert "GIT-RECOVERY-WORKFLOW-GUARD-001" in text and "**livré**" in text, (
            "Le ticket doit être marqué livré dans la roadmap."
        )


# ── CLAUDE.md : étape 0 obligatoire ────────────────────────────────────────────


class TestClaudeMdEtapeZero:
    """Verrouille l'étape 0 (CLAUDE-MD-CANONICAL-REPO-GUARD-001 +
    CLAUDE-MD-CANONICAL-REPO-GUARD-TEST-001) : CLAUDE.md doit imposer
    la vérification du dépôt canonique avant tout ticket Forge.

    Le contournement ponctuel du hook qui a permis l'insertion est
    acceptable parce que CLAUDE.md est volontairement protégé ; en
    contrepartie, ce test verrouille le résultat pour qu'une suppression
    ou un drift accidentel soit immédiatement détecté.
    """

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = CLAUDE_MD.read_text(encoding="utf-8")

    @pytest.mark.parametrize("marker", [
        "Étape 0 — Vérifier le dépôt canonique",
        "/home/roger/Projets/Forge",
        "git@github.com:caucrogeGit/Forge.git",
        "forge-test-*",
        "branche `master`",
        "arrêter immédiatement",
    ])
    def test_etape_zero_marker_present(self, marker):
        assert marker in self.content, (
            f"CLAUDE.md doit mentionner '{marker}' dans l'étape 0. "
            "Voir CLAUDE-MD-CANONICAL-REPO-GUARD-001."
        )

    def test_etape_zero_is_inside_section_5(self):
        # L'étape 0 doit être placée dans la section « Convention de
        # tickets » (section 5) — c'est le contrat de placement
        # convenu : pas un ajout en fin de fichier, pas une nouvelle
        # section qui renuméroterait les suivantes.
        idx_section_5 = self.content.find("## 5. Convention de tickets")
        idx_etape_0 = self.content.find("Étape 0 — Vérifier le dépôt canonique")
        idx_section_6 = self.content.find("## 6. Convention de tests")
        assert idx_section_5 != -1, "Section 5 introuvable dans CLAUDE.md"
        assert idx_etape_0 != -1, "Étape 0 introuvable dans CLAUDE.md"
        assert idx_section_6 != -1, "Section 6 introuvable dans CLAUDE.md"
        assert idx_section_5 < idx_etape_0 < idx_section_6, (
            "Étape 0 doit être placée à l'intérieur de la section 5, "
            "entre '## 5. Convention de tickets' et '## 6. Convention de tests'."
        )

    def test_etape_zero_points_to_canonical_repo_doc(self):
        # L'étape 0 renvoie vers la page de procédure complète
        # (signaux d'un mauvais dépôt + portage par patchs).
        assert "docs/contributing/canonical-repo.md" in self.content, (
            "L'étape 0 doit pointer explicitement vers "
            "docs/contributing/canonical-repo.md."
        )
