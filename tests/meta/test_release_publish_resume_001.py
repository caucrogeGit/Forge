"""RELEASE-PUBLISH-RESUME-GENERALIZE-001 : la reprise de publication sert toute release.

Le script de reprise portait `rc2` dans son nom, son journal, ses messages et
sa ligne d'auto-retrait. Écrit pour un incident précis, il aurait été recopié
et réédité à chaque release, ou oublié au moment où le 429 frappe, c'est-à-dire
au plus mauvais moment pour écrire un script.

La version ne doit donc figurer nulle part : elle se lit dans `pyproject.toml`,
seule source de vérité.

Généraliser a révélé un trou dans le garde de complétude. Celui-ci demandait
« cette distribution a-t-elle été publiée un jour », alors que le script de
reprise devait savoir « la version qu'on publie est-elle servie partout ». Une
distribution restée en rc2 pendant que les vingt-sept autres passent en rc3
satisfaisait donc le garde, alors que la release est partielle. Le script
posait la bonne question dans son coin, avec sa propre lecture de PyPI,
forcément divergente : elle comptait une version retirée comme publiée, et
déduisait les noms de distribution des noms de dossier.

La question rejoint le garde sous `--version`, et le script l'appelle
(principe 11, une seule façon officielle de faire chaque chose).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = PROJECT_ROOT / "tools" / "publish-resume.sh"

from tools import check_pypi_completeness as guard  # noqa: E402


@pytest.fixture(scope="module")
def source() -> str:
    return SCRIPT.read_text(encoding="utf-8")


# ── Le script généralisé ─────────────────────────────────────────────────────

def test_le_script_generalise_existe() -> None:
    assert SCRIPT.is_file()


def test_l_ancien_script_nomme_rc2_a_disparu() -> None:
    """Test d'absence : un script daté ressort à la release suivante."""
    assert not (PROJECT_ROOT / "tools" / "publish-rc2-resume.sh").exists()


def test_aucune_version_ecrite_en_dur(source: str) -> None:
    """« rc2 » vivait dans le nom, le journal, deux messages et l'auto-retrait.

    Les commentaires sont exemptés : la règle porte sur ce que le script
    **fait**, et raconter d'où il vient est précisément ce qui empêche de le
    redater au prochain incident. Ce test a d'abord refusé sa propre note
    d'historique, ce qui aurait poussé à effacer la mémoire du ticket.
    """
    code = "\n".join(ligne for ligne in source.splitlines()
                     if not ligne.lstrip().startswith("#"))

    for marqueur in ("rc2", "rc.2", "rc3", "rc.3", "1.0.0"):
        assert marqueur not in code, (
            f"le script nomme une version précise ({marqueur}) : il ne servira "
            "pas la release suivante"
        )


def test_la_version_est_lue_du_pyproject(source: str) -> None:
    assert "pyproject.toml" in source
    assert 'VERSION="' in source


def test_le_script_s_auto_retire_sous_son_nom_courant(source: str) -> None:
    """Une ligne de cron qui survit relance des publications pour toujours."""
    assert "grep -v 'publish-resume.sh'" in source


def test_le_script_active_le_venv_du_projet(source: str) -> None:
    """cron a un PATH minimal : sans le venv, ni twine ni Forge ne sont là."""
    assert ".venv/bin/activate" in source
    assert ".venv/bin/python" in source


def test_le_script_est_executable() -> None:
    assert SCRIPT.stat().st_mode & 0o111, "le script n'est pas exécutable"


# ── Il délègue au garde au lieu de relire PyPI ───────────────────────────────

def test_le_verdict_vient_du_garde_de_completude(source: str) -> None:
    assert "check_pypi_completeness.py --version" in source


def test_le_script_ne_relit_pas_pypi_lui_meme(source: str) -> None:
    """Sa lecture recopiée comptait une version retirée comme publiée."""
    assert "urllib" not in source
    assert "pypi.org/pypi" not in source


# ── La question ajoutée au garde ─────────────────────────────────────────────

def test_sans_version_le_garde_se_contente_de_publie_un_jour(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Le comportement d'origine, préservé : c'est la question de la release."""
    depot = set(guard.repo_distributions())
    monkeypatch.setattr(
        guard, "pypi_versions",
        lambda nom, timeout=10.0: ["1.0.0rc2"] if nom in depot else [])

    assert guard.verifier(check_build=False, offline_ok=False) == 0


def test_avec_version_une_distribution_restee_en_arriere_fait_echouer(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """Le trou mesuré : publié un jour, mais pas dans la version qu'on publie."""
    depot = set(guard.repo_distributions())

    def _versions(nom: str, timeout: float = 10.0) -> "list[str]":
        if nom not in depot:
            return []
        return ["1.0.0rc2"] if nom == "forge-mvc-fixtures" else ["1.0.0rc2", "1.0.0rc3"]

    monkeypatch.setattr(guard, "pypi_versions", _versions)

    assert guard.verifier(check_build=False, offline_ok=False, version="1.0.0rc3") == 1
    sortie = capsys.readouterr().out
    assert "forge-mvc-fixtures" in sortie
    assert "partielle" in sortie


def test_avec_version_tout_publie_passe(monkeypatch: pytest.MonkeyPatch) -> None:
    depot = set(guard.repo_distributions())
    monkeypatch.setattr(
        guard, "pypi_versions",
        lambda nom, timeout=10.0: ["1.0.0rc2", "1.0.0rc3"] if nom in depot else [])

    assert guard.verifier(check_build=False, offline_ok=False, version="1.0.0rc3") == 0


def test_jamais_publie_prime_sur_mauvaise_version(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """Le message doit dire le vrai problème : la distribution n'existe pas."""
    monkeypatch.setattr(guard, "pypi_versions", lambda nom, timeout=10.0: [])

    assert guard.verifier(check_build=False, offline_ok=False, version="1.0.0rc3") == 1
    sortie = capsys.readouterr().out
    assert "JAMAIS PUBLIÉ" in sortie
    assert "partielle" not in sortie


# ── Les deux écritures d'une même version ────────────────────────────────────

@pytest.mark.parametrize(("semver", "pep440"), [
    ("1.0.0-rc.3", "1.0.0rc3"),
    ("1.0.0-beta.14", "1.0.0b14"),
    ("1.0.0", "1.0.0"),
])
def test_semver_et_pep440_designent_la_meme_version(semver: str, pep440: str) -> None:
    """Forge tague en SemVer et publie en PEP 440 : le garde ne doit pas s'y perdre."""
    assert guard.meme_version(semver, pep440)


def test_deux_versions_differentes_ne_se_confondent_pas() -> None:
    assert not guard.meme_version("1.0.0rc2", "1.0.0rc3")


# ── Le câblage dans la publication ───────────────────────────────────────────

def test_publish_verifie_pypi_apres_avoir_publie() -> None:
    """« twine n'a pas protesté » n'est pas « PyPI sert la version »."""
    source = (PROJECT_ROOT / "tools" / "publish.sh").read_text(encoding="utf-8")

    assert "check_pypi_completeness.py" in source
    assert "--version" in source


def test_publish_tolere_le_delai_d_indexation() -> None:
    """Conclure au premier refus ferait crier le garde sur un envoi réussi."""
    source = (PROJECT_ROOT / "tools" / "publish.sh").read_text(encoding="utf-8")

    assert "nouvel essai" in source


def test_publish_oriente_vers_la_reprise_automatique() -> None:
    """Un refus sans remède fait perdre le temps qu'il prétend économiser."""
    source = (PROJECT_ROOT / "tools" / "publish.sh").read_text(encoding="utf-8")

    assert "publish-resume.sh" in source
