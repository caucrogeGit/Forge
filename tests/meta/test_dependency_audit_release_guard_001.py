"""Garde-fou DEPENDENCY-AUDIT-RELEASE-GUARD-001.

Forge utilise une politique à deux niveaux pour les audits de dépendances :

  * **Surveillance hebdomadaire** (`.github/workflows/dependency-audit.yml`) —
    informatif (`continue-on-error: true`) ; tolère les CVE transitoires
    sans bloquer le développement quotidien.
  * **Validation release** (`tools/release-validate.sh`) — bloquant ; aucune
    publication n'est validée tant que `pip-audit` (Python) et `npm audit`
    (Node) ne passent pas.

Ce meta-test verrouille :

  1. `tools/release-validate.sh` contient un audit Python (`pip-audit`) ;
  2. il contient un audit Node (`npm audit`) ;
  3. ces commandes ne sont jamais neutralisées par `|| true` ;
  4. la documentation `docs/release/release-policy.md` énonce la politique ;
  5. le workflow `dependency-audit.yml` reste explicitement annoté comme
     informatif (la présence de `continue-on-error: true` doit s'accompagner
     d'un commentaire indiquant que ce workflow n'est PAS le garde release.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

_ROOT = Path(__file__).resolve().parents[2]
_RELEASE_SCRIPT = _ROOT / "tools" / "release-validate.sh"
_RELEASE_POLICY = _ROOT / "docs" / "release" / "release-policy.md"
_AUDIT_WORKFLOW = _ROOT / ".github" / "workflows" / "dependency-audit.yml"


# ---------------------------------------------------------------------------
# Helpers — analyse ligne à ligne en ignorant les commentaires shell.
# ---------------------------------------------------------------------------


def _shell_lines(text: str) -> list[str]:
    """Lignes shell non commentées (commentaires `# ...` retirés en début).

    On garde la ligne entière même si elle finit par un commentaire — on
    veut surtout la commande effective. Une ligne dont le premier caractère
    non-blanc est `#` est filtrée.
    """
    out = []
    for raw in text.splitlines():
        stripped = raw.lstrip()
        if stripped.startswith("#"):
            continue
        out.append(raw)
    return out


# ---------------------------------------------------------------------------
# Tests — script release.
# ---------------------------------------------------------------------------


class TestReleaseScriptBlocksOnVulnerabilities:
    """`tools/release-validate.sh` doit poser les audits sans les masquer."""

    def test_release_script_exists(self):
        assert _RELEASE_SCRIPT.is_file(), (
            "tools/release-validate.sh doit exister."
        )

    def test_release_script_runs_pip_audit(self):
        text = _RELEASE_SCRIPT.read_text(encoding="utf-8")
        non_comment = "\n".join(_shell_lines(text))
        assert "pip-audit" in non_comment, (
            "tools/release-validate.sh doit appeler `pip-audit` (audit "
            "dépendances Python — DEPENDENCY-AUDIT-RELEASE-GUARD-001)."
        )

    def test_release_script_runs_npm_audit(self):
        text = _RELEASE_SCRIPT.read_text(encoding="utf-8")
        non_comment = "\n".join(_shell_lines(text))
        # Tolère `npm audit` et `npm audit --omit=dev`.
        assert re.search(r"\bnpm\s+audit\b", non_comment), (
            "tools/release-validate.sh doit appeler `npm audit` (audit "
            "dépendances Node — DEPENDENCY-AUDIT-RELEASE-GUARD-001)."
        )

    def test_pip_audit_is_not_masked_by_or_true(self):
        """Aucune occurrence `pip-audit ... || true` qui neutraliserait l'échec.

        On tolère `|| true` sur d'autres commandes du script (par ex. pour
        des captures de sortie comme `RUFF_OUT=$(ruff check ... || true)`),
        mais une ligne exécutant `pip-audit` ne doit jamais finir par cette
        neutralisation.
        """
        for line in _shell_lines(_RELEASE_SCRIPT.read_text(encoding="utf-8")):
            if "pip-audit" not in line:
                continue
            # On regarde la commande EFFECTIVE — pas une capture `$(... || true)`
            # qui sert à récupérer la sortie pour analyse explicite ensuite.
            # Ici, le pattern interdit est `pip-audit ... || true` en queue.
            if "$(" in line and "|| true" in line:
                # Le test continue de checker s'il y a un `_fail` en aval
                # qui rétablit le caractère bloquant. C'est le pattern actuel
                # du script. On l'autorise.
                continue
            assert "|| true" not in line, (
                f"`pip-audit` masqué par `|| true` dans : {line.strip()!r}. "
                "Le garde release doit faire échouer la validation sur CVE."
            )

    def test_npm_audit_is_not_masked_by_or_true(self):
        for line in _shell_lines(_RELEASE_SCRIPT.read_text(encoding="utf-8")):
            if not re.search(r"\bnpm\s+audit\b", line):
                continue
            if "$(" in line and "|| true" in line:
                continue
            assert "|| true" not in line, (
                f"`npm audit` masqué par `|| true` dans : {line.strip()!r}. "
                "Le garde release doit faire échouer la validation sur CVE."
            )

    def test_release_script_calls_fail_on_pip_audit_failure(self):
        """Le pattern attendu : capture de sortie + check d'exit code + `_fail`.

        On vérifie que la section pip-audit contient un appel à `_fail` —
        sinon la capture `$( ... || true)` masquerait l'erreur sans rien
        signaler.
        """
        text = _RELEASE_SCRIPT.read_text(encoding="utf-8")
        # Sectionne par les en-têtes `# ── N. ... ──`.
        sections = re.split(r"#\s*──\s*\d+\.\s*", text)
        pip_audit_sections = [s for s in sections if "pip-audit" in s]
        assert pip_audit_sections, "Pas de section dédiée à pip-audit."
        for section in pip_audit_sections:
            assert "_fail" in section, (
                "La section pip-audit ne contient pas d'appel `_fail` — "
                "un échec ne serait pas comptabilisé comme erreur release."
            )

    def test_release_script_calls_fail_on_npm_audit_failure(self):
        text = _RELEASE_SCRIPT.read_text(encoding="utf-8")
        sections = re.split(r"#\s*──\s*\d+\.\s*", text)
        npm_audit_sections = [s for s in sections if re.search(r"\bnpm\s+audit\b", s)]
        assert npm_audit_sections, "Pas de section dédiée à npm audit."
        for section in npm_audit_sections:
            assert "_fail" in section, (
                "La section npm audit ne contient pas d'appel `_fail`."
            )


# ---------------------------------------------------------------------------
# Tests — workflow informatif documenté.
# ---------------------------------------------------------------------------


class TestPeriodicAuditWorkflowIsAnnotated:
    """Si `dependency-audit.yml` reste informatif (`continue-on-error: true`),
    son rôle doit être documenté dans le fichier lui-même — sinon un futur
    lecteur pourrait croire que c'est le garde release."""

    def test_workflow_exists(self):
        assert _AUDIT_WORKFLOW.is_file()

    def test_continue_on_error_is_paired_with_a_role_comment(self):
        text = _AUDIT_WORKFLOW.read_text(encoding="utf-8")
        if "continue-on-error: true" not in text:
            pytest.skip("Le workflow n'utilise plus `continue-on-error: true`.")
        # On accepte plusieurs formulations équivalentes ; l'important est
        # qu'un commentaire YAML mentionne le rôle informatif / non-bloquant.
        markers = (
            "informatif",
            "non bloquant",
            "non-bloquant",
            "NON BLOQUANT",
            "non blocking",
            "informational",
        )
        assert any(m in text for m in markers), (
            "Le workflow `dependency-audit.yml` utilise `continue-on-error: "
            "true` sans préciser son rôle. Ajouter un commentaire YAML "
            "indiquant qu'il s'agit d'un workflow informatif / non bloquant "
            "et que le garde release vit dans `tools/release-validate.sh`."
        )

    def test_workflow_mentions_release_validate_pointer(self):
        """Le workflow doit pointer vers le garde release pour éviter qu'on
        confonde les rôles dans le futur."""
        text = _AUDIT_WORKFLOW.read_text(encoding="utf-8")
        assert "release-validate.sh" in text or "release-validate" in text, (
            "Le workflow informatif doit explicitement renvoyer vers "
            "`tools/release-validate.sh` (qui est le garde release)."
        )


# ---------------------------------------------------------------------------
# Tests — documentation release.
# ---------------------------------------------------------------------------


class TestReleasePolicyDocumentsTheRule:
    def test_release_policy_exists(self):
        assert _RELEASE_POLICY.is_file()

    def test_release_policy_mentions_pip_audit(self):
        text = _RELEASE_POLICY.read_text(encoding="utf-8")
        assert "pip-audit" in text, (
            "docs/release/release-policy.md doit mentionner `pip-audit` dans la "
            "section audits dépendances."
        )

    def test_release_policy_mentions_npm_audit(self):
        text = _RELEASE_POLICY.read_text(encoding="utf-8")
        assert "npm audit" in text, (
            "docs/release/release-policy.md doit mentionner `npm audit`."
        )

    def test_release_policy_states_blocking_in_release(self):
        """La politique doit dire explicitement que l'audit est bloquant
        en release (et seulement à ce moment-là)."""
        text = _RELEASE_POLICY.read_text(encoding="utf-8").lower()
        assert "bloquant" in text, (
            "docs/release/release-policy.md doit qualifier explicitement les audits "
            "release de « bloquants »."
        )
