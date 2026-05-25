"""Garde-fou RELEASE-VALIDATE-PATH-ROBUSTNESS-001.

Verrouille que ``tools/release-validate.sh`` utilise un interpréteur
Python explicite configurable au lieu d'invocations nues dépendantes
du ``PATH``.

Contrat verrouillé
------------------
* Le script définit ``PYTHON_BIN="${PYTHON:-python3}"`` (ou un alias) ;
* il valide que ``PYTHON_BIN`` existe avant d'exécuter quoi que ce soit ;
* chaque appel à ``pytest``, ``compileall``, ``ruff``, ``mkdocs`` ou
  ``pip_audit`` passe par ``"$PYTHON_BIN" -m <module>`` — pas par le
  binaire du ``PATH`` ;
* le mode utilitaire ``--convert`` reste fonctionnel et ne nécessite
  pas la résolution de Python (il ne touche que du shell pur).

Les assertions sont robustes au déplacement de lignes : on parse le
contenu du script et on cherche les patterns canoniques, sans dépendre
des numéros de ligne.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "tools" / "release-validate.sh"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def script_text() -> str:
    assert _SCRIPT.is_file(), f"{_SCRIPT.relative_to(_REPO_ROOT)} doit exister."
    return _SCRIPT.read_text(encoding="utf-8")


def _non_comment_lines(text: str) -> list[str]:
    """Lignes shell non commentées (élimine les `#` en début de ligne)."""
    return [
        raw for raw in text.splitlines()
        if not raw.lstrip().startswith("#")
    ]


# ---------------------------------------------------------------------------
# 1. PYTHON_BIN est défini et configurable
# ---------------------------------------------------------------------------


class TestPythonBinDeclared:
    def test_script_declares_python_bin_variable(self, script_text):
        """Le script doit déclarer ``PYTHON_BIN=...`` (configurable via env)."""
        assert re.search(
            r'^\s*PYTHON_BIN\s*=\s*"?\$\{PYTHON:?-?[^"}]+\}',
            script_text,
            re.MULTILINE,
        ), (
            "Le script doit déclarer une variable PYTHON_BIN configurable "
            "via la variable d'environnement PYTHON, par exemple : "
            "`PYTHON_BIN=\"${PYTHON:-python3}\"`."
        )

    def test_script_validates_python_bin_exists(self, script_text):
        """Le script doit valider que `PYTHON_BIN` est résolvable avant
        d'utiliser des modules."""
        assert "command -v \"$PYTHON_BIN\"" in script_text or \
               "command -v $PYTHON_BIN" in script_text, (
            "Le script doit vérifier l'existence de PYTHON_BIN via "
            "`command -v \"$PYTHON_BIN\"` et échouer clairement si absent."
        )


# ---------------------------------------------------------------------------
# 2. Chaque appel Python passe par $PYTHON_BIN -m <module>
# ---------------------------------------------------------------------------


class TestToolInvocationsUsePythonBin:
    """Tous les appels aux outils Python du script doivent passer par
    `"$PYTHON_BIN" -m <module>`. On vérifie présence du pattern correct
    + absence du pattern nu (sans `PYTHON_BIN`)."""

    @pytest.mark.parametrize("module,naked_patterns", [
        # Pour chaque outil, on cherche le pattern d'INVOCATION nue —
        # c'est-à-dire le binaire en tête de commande, soit après `$(` (capture
        # de sortie), soit en début de ligne après indentation. La forme
        # correcte `"$PYTHON_BIN" -m <module>` ne déclenche AUCUN de ces
        # patterns car le binaire concerné n'apparaît jamais en tête de mot.
        ("pytest", [
            r"\$\(\s*python\s+-m\s+pytest\b",
            r"\$\(\s*pytest\b",
            r"^\s*pytest\s+-",   # ligne shell commençant directement par pytest
        ]),
        ("compileall", [
            r"\$\(\s*python\s+-m\s+compileall\b",
            r"\$\(\s*python3\s+-m\s+compileall\b",
        ]),
        ("ruff", [
            r"\$\(\s*ruff\s",
            r"^\s*ruff\s+check\b",
        ]),
        ("mkdocs", [
            r"\$\(\s*mkdocs\s",
            r"^\s*mkdocs\s+build\b",
        ]),
        ("pip_audit", [
            r"\$\(\s*pip-audit\b",
            r"^\s*pip-audit\s+-r",
        ]),
    ])
    def test_no_naked_call_to(self, script_text, module, naked_patterns):
        non_comment = "\n".join(_non_comment_lines(script_text))
        # Chaque pattern nu doit être ABSENT du code non commenté.
        for pat in naked_patterns:
            assert not re.search(pat, non_comment, re.MULTILINE), (
                f"Le script contient encore un appel nu vers `{module}` "
                f"(pattern : {pat!r}). Remplacer par `\"$PYTHON_BIN\" -m {module}`."
            )

    @pytest.mark.parametrize("module", [
        "pytest",
        "compileall",
        "ruff",
        "mkdocs",
        "pip_audit",
    ])
    def test_calls_module_via_python_bin(self, script_text, module):
        """Forme attendue : `"$PYTHON_BIN" -m <module>`."""
        pattern = rf'"\$PYTHON_BIN"\s+-m\s+{re.escape(module)}\b'
        assert re.search(pattern, script_text), (
            f"Le script doit invoquer `{module}` via "
            f"`\"$PYTHON_BIN\" -m {module}`. Aucune occurrence trouvée."
        )


# ---------------------------------------------------------------------------
# 3. Le mode --convert reste fonctionnel (sans dépendre de Python)
# ---------------------------------------------------------------------------


class TestConvertModeStillWorks:
    """Le mode utilitaire `--convert` est utilisé par d'autres tests méta
    (cf RELEASE-VALIDATE-PEP440-SEMVERSION-001). Il doit rester
    fonctionnel après le durcissement PATH."""

    def _convert(self, *args) -> tuple[int, str]:
        proc = subprocess.run(
            ["bash", str(_SCRIPT), "--convert", *args],
            capture_output=True, text=True, check=False,
        )
        return proc.returncode, proc.stdout.strip()

    def test_convert_pep440_works(self):
        code, out = self._convert("pep440", "1.0.0-beta.10")
        assert code == 0
        assert out == "1.0.0b10"

    def test_convert_semver_works(self):
        code, out = self._convert("semver", "1.0.0b10")
        assert code == 0
        assert out == "1.0.0-beta.10"

    def test_convert_validate_accepts_valid_version(self):
        code, _ = self._convert("validate", "1.0.0-beta.10")
        assert code == 0

    def test_convert_validate_rejects_invalid_version(self):
        code, _ = self._convert("validate", "1.0.0beta10")
        assert code != 0


# ---------------------------------------------------------------------------
# 4. Le script échoue clairement si PYTHON_BIN est introuvable
# ---------------------------------------------------------------------------


class TestExitsCleanlyOnMissingPython:
    def test_exits_nonzero_with_clear_message(self):
        """Un PYTHON pointant nulle part doit produire un message explicite
        et `exit 1` avant d'attaquer la validation."""
        proc = subprocess.run(
            ["bash", str(_SCRIPT), "1.0.0-beta.9"],
            env={
                "PYTHON": "/nonexistent/python-binary-for-test",
                "PATH": "/usr/bin:/bin",  # supprime venv shims
            },
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        assert proc.returncode == 1, (
            f"Exit code attendu : 1 (Python introuvable). "
            f"Reçu : {proc.returncode}. stdout={proc.stdout!r} "
            f"stderr={proc.stderr!r}"
        )
        combined = proc.stdout + proc.stderr
        assert "Python introuvable" in combined, (
            "Le message d'erreur doit contenir « Python introuvable »."
        )
        assert "/nonexistent/python-binary-for-test" in combined, (
            "Le message doit echoer la valeur de PYTHON pour aider au diagnostic."
        )
