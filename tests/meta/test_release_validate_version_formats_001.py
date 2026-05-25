"""Meta tests pour `tools/release-validate.sh` — conversion SemVer ↔ PEP 440.

Ticket : RELEASE-VALIDATE-PEP440-SEMVERSION-001.

Forge utilise deux formats équivalents pour la même release :
  - SemVer public : 1.0.0-beta.9 (CHANGELOG, tags git, package.json, docs)
  - PEP 440       : 1.0.0b9      (pyproject.toml, core/__init__.py, forge.py)

Le script de validation doit normaliser dans les deux sens pour comparer le
bon format à chaque source. Ces tests verrouillent les fonctions de
conversion et de validation exposées via le mode `--convert`.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

_SCRIPT = Path(__file__).resolve().parents[2] / "tools" / "release-validate.sh"


def _convert(direction: str, version: str) -> tuple[int, str]:
    proc = subprocess.run(
        ["bash", str(_SCRIPT), "--convert", direction, version],
        capture_output=True, text=True, check=False,
    )
    return proc.returncode, proc.stdout.strip()


class TestSemverToPep440:
    @pytest.mark.parametrize("semver,pep440", [
        ("1.0.0-beta.9", "1.0.0b9"),
        ("1.0.0-beta.10", "1.0.0b10"),
        ("1.0.0-beta.11", "1.0.0b11"),
        ("1.0.0-alpha.1", "1.0.0a1"),
        ("1.0.0-rc.1", "1.0.0rc1"),
        ("1.0.0", "1.0.0"),       # stable identique entre SemVer et PEP 440
        ("3.0.2", "3.0.2"),       # rétro-compat versions historiques
        ("2.0.10-beta.3", "2.0.10b3"),  # minor/patch à deux chiffres
    ])
    def test_conversion(self, semver, pep440):
        code, out = _convert("pep440", semver)
        assert code == 0
        assert out == pep440


class TestPep440ToSemver:
    @pytest.mark.parametrize("pep440,semver", [
        ("1.0.0b9", "1.0.0-beta.9"),
        ("1.0.0b10", "1.0.0-beta.10"),
        ("1.0.0b11", "1.0.0-beta.11"),
        ("1.0.0a1", "1.0.0-alpha.1"),
        ("1.0.0rc1", "1.0.0-rc.1"),
        ("1.0.0", "1.0.0"),
        ("3.0.2", "3.0.2"),
        ("2.0.10b3", "2.0.10-beta.3"),
    ])
    def test_conversion(self, pep440, semver):
        code, out = _convert("semver", pep440)
        assert code == 0
        assert out == semver


class TestRoundTrip:
    """Les conversions sont involutives pour les formats canoniques Forge."""

    @pytest.mark.parametrize("version", [
        "1.0.0-beta.9",
        "1.0.0-beta.10",
        "1.0.0-alpha.3",
        "1.0.0-rc.2",
        "1.0.0",
        "3.0.2",
    ])
    def test_semver_then_pep440_then_semver(self, version):
        _, pep = _convert("pep440", version)
        _, back = _convert("semver", pep)
        assert back == version, f"round-trip cassé : {version!r} -> {pep!r} -> {back!r}"

    @pytest.mark.parametrize("version", [
        "1.0.0b9",
        "1.0.0b10",
        "1.0.0a3",
        "1.0.0rc2",
        "1.0.0",
        "3.0.2",
    ])
    def test_pep440_then_semver_then_pep440(self, version):
        _, sem = _convert("semver", version)
        _, back = _convert("pep440", sem)
        assert back == version, f"round-trip cassé : {version!r} -> {sem!r} -> {back!r}"

    @pytest.mark.parametrize("version", [
        "1.0.0b9", "1.0.0a3", "1.0.0rc2", "1.0.0", "3.0.2",
        "1.0.0-beta.9", "1.0.0-alpha.3", "1.0.0-rc.2",
    ])
    def test_idempotence(self, version):
        """Convertir vers son propre format ne change rien."""
        if "-" in version:
            _, out = _convert("semver", version)
        else:
            _, out = _convert("pep440", version)
        assert out == version


class TestValidation:
    @pytest.mark.parametrize("version", [
        "1.0.0",
        "1.0.0-beta.9",
        "1.0.0b9",
        "1.0.0-beta.10",
        "1.0.0b10",
        "1.0.0-alpha.1",
        "1.0.0a1",
        "1.0.0-rc.1",
        "1.0.0rc1",
        "3.0.2",
        "2.0.10-beta.3",
        "2.0.10b3",
    ])
    def test_versions_acceptees(self, version):
        code, _ = _convert("validate", version)
        assert code == 0, f"version valide {version!r} rejetée à tort"

    @pytest.mark.parametrize("version", [
        "1.0.0beta9",   # pas de séparateur SemVer ni préfixe PEP 440 valide
        "1.0.0-beta",   # numéro de pre-release manquant
        "1.0.0-b9",     # ni SemVer (`beta`) ni PEP 440 (pas de tiret)
        "beta.9",       # pas de version
        "1.0",          # patch manquant
        "",             # vide
        "v1.0.0",       # préfixe `v` est pour les tags, pas la version
        "1.0.0-",       # tiret orphelin
        "1.0.0-BETA.9", # majuscules non acceptées
    ])
    def test_versions_invalides(self, version):
        code, _ = _convert("validate", version)
        assert code != 0, f"version invalide {version!r} acceptée à tort"


class TestNonLiteralComparison:
    """Garde-fou — le script ne compare pas littéralement SemVer et PEP 440.

    L'équivalence sémantique 1.0.0-beta.9 ≡ 1.0.0b9 doit passer par la
    normalisation, pas par une comparaison de chaînes brute.
    """

    def test_semver_et_pep440_sont_distincts_litteralement(self):
        # Sanity : sans conversion, ce sont deux chaînes différentes.
        assert "1.0.0-beta.9" != "1.0.0b9"

    def test_conversion_etablit_l_equivalence(self):
        _, pep = _convert("pep440", "1.0.0-beta.9")
        _, sem = _convert("semver", "1.0.0b9")
        assert pep == "1.0.0b9"
        assert sem == "1.0.0-beta.9"

    def test_stable_meme_format_dans_les_deux_sens(self):
        """Une version stable est identique dans les deux conventions."""
        _, pep = _convert("pep440", "1.0.0")
        _, sem = _convert("semver", "1.0.0")
        assert pep == sem == "1.0.0"
