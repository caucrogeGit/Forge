"""RELEASE-PYPI-COMPLETENESS-GUARD-001 : rien ne vérifiait qu'on publiait tout.

La rc2 a été publiée avec vingt-quatre distributions sur vingt-sept. Les trois
absentes n'ont pas échoué à se construire : elles sont nées après la
publication précédente, et aucune étape ne comparait ce que le dépôt porte à ce
que PyPI sert. Le pré-mortem du 2026-07-28 a chiffré la conséquence : le cœur
n'a plus `cli/entities` depuis l'ADR-070, la rc2 publiée l'embarque encore,
donc publier une rc3 sans `forge-mvc-entities` retirerait `make:entity`,
`make:crud`, les migrations et `db:*` à tous les projets. Une release peut être
une régression sans que rien ne le dise.

Le garde croise trois ensembles : le dépôt, la construction, PyPI. Il détecte
aujourd'hui, en interrogeant vraiment PyPI, les trois distributions jamais
publiées et deux orphelines qui restent installables sans être maintenues.

Ces tests n'appellent pas le réseau : ils éprouvent la logique et le câblage.
La vérification réelle appartient à `release-validate.sh`.
"""
from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

from tools import check_pypi_completeness as guard  # noqa: E402


# ── Ce que le garde lit du dépôt ─────────────────────────────────────────────

def test_le_depot_est_releve_entierement() -> None:
    """Le cœur et chaque opt-in, sans liste écrite en dur."""
    noms = guard.repo_distributions()
    attendus = 1 + len(list(PROJECT_ROOT.glob("packages/*/pyproject.toml")))

    assert len(noms) == attendus
    assert "forge-mvc" in noms


def test_les_noms_viennent_des_pyproject_pas_des_dossiers() -> None:
    """Un dossier peut différer du nom de distribution : c'est ce dernier qui compte."""
    noms = set(guard.repo_distributions())
    for pyproject in PROJECT_ROOT.glob("packages/*/pyproject.toml"):
        declare = tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["name"]
        assert declare in noms


def test_aucune_liste_de_paquets_ecrite_en_dur() -> None:
    """Un compte figé ne prévient de rien : il a valu 13, puis 25, puis 28."""
    source = (PROJECT_ROOT / "tools" / "check_pypi_completeness.py").read_text(
        encoding="utf-8")

    assert "packages/*/pyproject.toml" in source


# ── Les distributions absorbées ──────────────────────────────────────────────

def test_les_absorbees_ne_sont_plus_au_depot() -> None:
    """La liste ABSORBED décrit ce qui a quitté `packages/`, pas ce qui y est."""
    depot = set(guard.repo_distributions())

    for nom in guard.ABSORBED:
        assert nom not in depot, (
            f"{nom} est déclaré absorbé mais vit encore dans packages/"
        )


def test_les_absorbees_disent_par_quoi_et_selon_quel_adr() -> None:
    """Un orphelin sans raison écrite se fait rétablir au ticket suivant."""
    for nom, raison in guard.ABSORBED.items():
        assert "ADR-" in raison, f"{nom} : raison sans ADR"


def test_pivot_et_media_sont_les_absorbes_connus() -> None:
    """Les deux suppressions de paquet que le dépôt a connues (CLAUDE.md §9)."""
    assert set(guard.ABSORBED) == {"forge-mvc-pivot", "forge-mvc-media"}


# ── La lecture des artefacts construits ──────────────────────────────────────

def test_le_nom_de_distribution_est_deduit_de_l_artefact(tmp_path: Path,
                                                         monkeypatch: pytest.MonkeyPatch) -> None:
    """`forge_mvc_entities-1.0.0rc3-py3-none-any.whl` vaut `forge-mvc-entities`."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "forge_mvc_entities-1.0.0rc3-py3-none-any.whl").touch()
    (dist / "forge_mvc-1.0.0rc3.tar.gz").touch()
    (dist / "notes.txt").touch()
    monkeypatch.setattr(guard, "PROJECT_ROOT", tmp_path)

    assert guard.built_distributions() == {"forge-mvc-entities", "forge-mvc"}


# ── Le verdict ───────────────────────────────────────────────────────────────

def _sans_reseau(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(guard, "pypi_versions", lambda nom, timeout=10.0: None)


def test_un_pypi_muet_fait_echouer_par_defaut(monkeypatch: pytest.MonkeyPatch,
                                              capsys: pytest.CaptureFixture[str]) -> None:
    """Un garde qui se tait quand il ne peut pas vérifier ne garde rien."""
    _sans_reseau(monkeypatch)

    assert guard.verifier(check_build=False, offline_ok=False) == 1
    assert "injoignable" in capsys.readouterr().out


def test_un_pypi_muet_est_tolerable_si_on_le_demande(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    _sans_reseau(monkeypatch)

    assert guard.verifier(check_build=False, offline_ok=True) == 0
    assert "[WARN]" in capsys.readouterr().out


def test_une_distribution_jamais_publiee_fait_echouer(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """Le cas mesuré : trois distributions du dépôt absentes de PyPI."""
    def _versions(nom: str, timeout: float = 10.0) -> "list[str]":
        return [] if nom == "forge-mvc-entities" else ["1.0.0rc2"]

    monkeypatch.setattr(guard, "pypi_versions", _versions)

    assert guard.verifier(check_build=False, offline_ok=False) == 1
    sortie = capsys.readouterr().out
    assert "forge-mvc-entities" in sortie
    assert "JAMAIS PUBLIÉ" in sortie


def test_une_orpheline_avertit_sans_bloquer(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """L'orphelin appelle une décision de release, pas un blocage automatique."""
    monkeypatch.setattr(guard, "pypi_versions",
                        lambda nom, timeout=10.0: ["1.0.0rc2"])

    assert guard.verifier(check_build=False, offline_ok=False) == 0
    sortie = capsys.readouterr().out
    assert "ORPHELIN" in sortie
    assert "forge-mvc-pivot" in sortie


def test_tout_publie_et_aucun_orphelin_passe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """L'état visé après la rc3 : rien à signaler."""
    depot = set(guard.repo_distributions())
    monkeypatch.setattr(
        guard, "pypi_versions",
        lambda nom, timeout=10.0: ["1.0.0rc3"] if nom in depot else [])

    assert guard.verifier(check_build=False, offline_ok=False) == 0


# ── Le câblage ───────────────────────────────────────────────────────────────

def test_release_validate_appelle_le_garde() -> None:
    source = (PROJECT_ROOT / "tools" / "release-validate.sh").read_text(
        encoding="utf-8")

    assert "check_pypi_completeness.py" in source
    assert "Complétude" in source


def test_aucun_compteur_de_paquets_fige_dans_les_scripts() -> None:
    """« 13 paquets » a survécu à quinze paquets de plus, sans jamais alerter."""
    for script in (PROJECT_ROOT / "tools").glob("*.sh"):
        texte = script.read_text(encoding="utf-8")
        assert "13 paquets" not in texte, f"{script.name} : compteur figé"
        assert "13 wheels" not in texte, f"{script.name} : compteur figé"
