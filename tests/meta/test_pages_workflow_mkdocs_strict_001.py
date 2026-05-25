"""Garde-fou CI-PAGES-MKDOCS-STRICT-001.

Verrouille l'alignement entre :

  * la validation locale documentaire (``mkdocs build --strict``) ;
  * le workflow GitHub Actions de tests (``.github/workflows/tests.yml``
    → ``mkdocs build --strict``) ;
  * le workflow GitHub Pages (``.github/workflows/pages.yml``).

Sans ce garde-fou, le workflow Pages pourrait revenir silencieusement à
un ``mkdocs build`` permissif et publier une documentation contenant des
liens cassés ou des références invalides que la validation locale aurait
refusés.

Le test parse le YAML du workflow et inspecte chaque étape pour s'assurer
qu'au moins une étape de build appelle ``mkdocs build`` avec ``--strict``.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

_PAGES_WORKFLOW = (
    Path(__file__).resolve().parents[2] / ".github" / "workflows" / "pages.yml"
)


def _workflow_steps() -> list[dict]:
    """Charge le workflow Pages et retourne la liste des steps du job `build`.

    On évite une dépendance dure à PyYAML : on parse à la main les `run:`
    de chaque step via une lecture ligne à ligne. C'est suffisant pour ce
    garde-fou qui n'a besoin que des commandes shell exécutées.
    """
    text = _PAGES_WORKFLOW.read_text(encoding="utf-8")
    steps: list[dict] = []
    current: dict | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        # Détection grossière d'un nouveau step : `- name:` ou `- uses:`
        # en début de ligne (indentation YAML usuelle de GitHub Actions).
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if indent == 6 and stripped.startswith("- "):
            if current is not None:
                steps.append(current)
            current = {"raw": [stripped]}
            continue
        if current is not None:
            current["raw"].append(stripped)
    if current is not None:
        steps.append(current)

    # Extrait `name:` et `run:` (multi-ligne `|` ou inline) pour chaque step.
    for step in steps:
        joined = " ".join(step["raw"])
        # `run:` peut être inline (`run: mkdocs build`) ou bloc YAML (`run: |`).
        if "run:" in joined:
            after = joined.split("run:", 1)[1].strip()
            step["run"] = after
        if "name:" in joined:
            after = joined.split("name:", 1)[1].split(" run:")[0].strip()
            step["name"] = after
    return steps


class TestPagesWorkflow:
    def test_pages_workflow_exists(self):
        assert _PAGES_WORKFLOW.is_file(), (
            f"{_PAGES_WORKFLOW.relative_to(_PAGES_WORKFLOW.parents[2])} doit exister."
        )

    def test_has_mkdocs_build_step(self):
        steps = _workflow_steps()
        runs = " ".join(s.get("run", "") for s in steps)
        assert "mkdocs build" in runs, (
            "Le workflow Pages doit contenir une étape `mkdocs build`."
        )

    def test_mkdocs_build_uses_strict(self):
        """Chaque invocation de ``mkdocs build`` dans pages.yml doit porter
        ``--strict``. On parcourt tous les ``run:`` du workflow ; toute
        commande ``mkdocs build`` sans ``--strict`` fait échouer le test."""
        steps = _workflow_steps()
        violations: list[str] = []
        for step in steps:
            run = step.get("run", "")
            if "mkdocs build" not in run:
                continue
            # Ignore les commandes commentées (ex. `# mkdocs build`).
            for fragment in run.split("&&"):
                fragment = fragment.strip()
                if not fragment.startswith("mkdocs build"):
                    continue
                if "--strict" not in fragment:
                    violations.append(
                        f"step {step.get('name', '<sans nom>')!r}: {fragment!r}"
                    )
        assert not violations, (
            "Le workflow Pages contient une commande `mkdocs build` non "
            f"stricte : {violations}. Ajouter `--strict` pour aligner sur la "
            "validation locale et `.github/workflows/tests.yml`."
        )

    def test_no_lenient_mkdocs_build_anywhere(self):
        """Garde-fou textuel additionnel : ``mkdocs build`` (sans ``--strict``)
        ne doit pas apparaître comme commande exécutable dans le fichier.

        On accepte que la chaîne brute soit présente dans un commentaire
        ou une heredoc explicative, mais pas comme commande effective.
        """
        text = _PAGES_WORKFLOW.read_text(encoding="utf-8")
        for line in text.splitlines():
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            # Cherche une commande shell `run: mkdocs build` exactement (pas suivie de --strict).
            if "mkdocs build" in stripped:
                # Tolère les variantes strictes : `--strict` n'importe où dans la ligne.
                if "--strict" not in stripped:
                    pytest.fail(
                        f"Ligne `{stripped}` exécute `mkdocs build` sans `--strict` : "
                        "cela publierait une documentation que la validation locale "
                        "refuserait. Aligner sur `mkdocs build --strict`."
                    )
