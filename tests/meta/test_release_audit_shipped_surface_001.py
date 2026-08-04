"""Bloc D du plan rc3 : bornes de dépendances et garde de release honnête.

Trois défauts distincts, corrigés ensemble parce qu'ils partagent une cause :
le garde de release ne regardait pas ce que Forge livre réellement.

`RELEASE-AUDIT-SHIPPED-SURFACE-001`
    `tools/release-validate.sh` auditait `requirements.txt`, soit les **4**
    dépendances du cœur, en ignorant `requirements-audit.txt` qui agrège la
    surface expédiée (Pillow, cryptography, psycopg, pyodbc...) — précisément
    celles qui portent des CVE. Et son verdict pytest se lisait dans le
    **texte** de sortie : une suite ne collectant aucun test affichait « no
    tests ran » et était comptée réussie, alors que pytest sort en code 5. Une
    release pouvait donc passer sans qu'un seul test ait tourné.

`DEPS-PILLOW-FLOOR-001`
    La borne `Pillow>=10.3` autorisait des versions vulnérables. Mesuré avec
    pip-audit : 10.3, 11.0, 11.3 et 12.0 portent des avis, tous corrigés en
    **12.3.0**, première version propre. L'audit ne le voyait pas puisqu'il
    résout la borne haute.

`DEPS-MARIADB-PIN-RANGE-001`
    `mariadb==1.1.14` figeait une version portant `PYSEC-2026-217`, avis sans
    correctif amont, exclu de l'audit. Une exclusion est une dette : sans
    surveillance, elle survit à la publication du correctif et masque une
    vulnérabilité réparable. D'où `tools/check_ignored_vulns.py`, seule étape
    **bloquante** de l'audit hebdomadaire.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

RELEASE_VALIDATE = PROJECT_ROOT / "tools" / "release-validate.sh"
AUDIT_WORKFLOW = PROJECT_ROOT / ".github" / "workflows" / "dependency-audit.yml"
REQUIREMENTS_AUDIT = PROJECT_ROOT / "requirements-audit.txt"
IMAGES_PYPROJECT = PROJECT_ROOT / "packages" / "forge-mvc-images" / "pyproject.toml"
MARIADB_PYPROJECT = PROJECT_ROOT / "packages" / "forge-mvc-mariadb" / "pyproject.toml"

pytestmark = pytest.mark.meta


# ── Le garde de release regarde la surface expédiée ──────────────────────────

def test_le_garde_de_release_audite_la_surface_expediee() -> None:
    script = RELEASE_VALIDATE.read_text(encoding="utf-8")
    assert "-r requirements-audit.txt" in script, (
        "release-validate.sh doit auditer requirements-audit.txt : "
        "requirements.txt ne couvre que les 4 dépendances du cœur."
    )


def test_le_garde_de_release_juge_pytest_sur_le_code_retour() -> None:
    """Le texte de sortie ne peut pas distinguer « 0 test » de « tout passe »."""
    script = RELEASE_VALIDATE.read_text(encoding="utf-8")

    assert "PYTEST_CODE" in script
    assert 'grep -qE "passed|no tests ran"' not in script, (
        "verdict par le texte : une suite ne collectant aucun test passait pour réussie"
    )


def test_le_code_5_de_pytest_est_traite_explicitement() -> None:
    """pytest sort en 5 quand rien n'est collecté : le cas doit être nommé."""
    script = RELEASE_VALIDATE.read_text(encoding="utf-8")
    assert re.search(r"\n\s*5\)\s+_fail", script), (
        "le cas « aucun test collecté » doit avoir son propre message"
    )


def test_l_exclusion_est_surveillee_par_le_garde_de_release() -> None:
    script = RELEASE_VALIDATE.read_text(encoding="utf-8")
    assert "check_ignored_vulns.py" in script


# ── L'audit hebdomadaire surveille ses exclusions ────────────────────────────

def test_l_audit_hebdomadaire_couvre_la_surface_expediee() -> None:
    workflow = AUDIT_WORKFLOW.read_text(encoding="utf-8")
    assert "requirements-audit.txt" in workflow


def test_la_surveillance_des_exclusions_est_bloquante() -> None:
    """Tout le workflow est non bloquant, sauf cette étape : c'est le point."""
    workflow = AUDIT_WORKFLOW.read_text(encoding="utf-8")

    position = workflow.index("check_ignored_vulns.py")
    step_start = workflow.rindex("- name:", 0, position)
    step = workflow[step_start:position]
    assert "continue-on-error" not in step, (
        "la surveillance des avis ignorés doit échouer pour être vue"
    )


def test_les_exclusions_sont_declarees_au_meme_endroit() -> None:
    """Un `--ignore-vuln` ajouté ailleurs doit être connu du veilleur."""
    from tools.check_ignored_vulns import IGNORED_VULNERABILITIES

    declared = set(IGNORED_VULNERABILITIES)
    for path in (RELEASE_VALIDATE, PROJECT_ROOT / ".github" / "workflows" / "tests.yml"):
        used = set(re.findall(r"--ignore-vuln\s+(\S+)", path.read_text(encoding="utf-8")))
        assert used <= declared, (
            f"{path.name} ignore {used - declared}, absent(s) de "
            "tools/check_ignored_vulns.py : l'exclusion ne serait pas surveillée."
        )


# ── Bornes de dépendances ────────────────────────────────────────────────────

def _requirement(text: str, package: str) -> str:
    match = re.search(rf"^{package}(\S*)$", text, re.MULTILINE | re.IGNORECASE)
    assert match is not None, f"{package} absent"
    return match.group(1)


def test_pillow_exclut_les_versions_vulnerables() -> None:
    """12.3.0 est la première version sans avis connu (mesuré avec pip-audit)."""
    for path in (IMAGES_PYPROJECT, REQUIREMENTS_AUDIT):
        text = path.read_text(encoding="utf-8")
        assert "Pillow>=12.3" in text, f"{path.name} autorise un Pillow vulnérable"
        assert "Pillow>=10.3" not in text


def test_mariadb_est_une_plage_et_non_une_version_figee() -> None:
    """Une version figée n'accueille pas le correctif de PYSEC-2026-217."""
    for path in (MARIADB_PYPROJECT, REQUIREMENTS_AUDIT):
        text = path.read_text(encoding="utf-8")
        assert "mariadb>=1.1.14,<1.2" in text
        assert "mariadb==1.1.14" not in text


def test_les_bornes_hautes_restent_posees() -> None:
    """Une borne basse relevée ne doit pas faire sauter la borne haute.

    `cryptography` est écarté depuis `DEPS-CRYPTOGRAPHY-NO-CEILING-001`, et
    c'est la seule exception. Cette bibliothèque livre ses correctifs de
    sécurité dans une nouvelle majeure : un plafond les exclut au moment même de
    leur parution, et `forge-mvc-mfa` étant une bibliothèque, il casse la
    résolution des applications qui en dépendent. Motifs complets dans
    `tests/meta/test_security_cryptography_mfa_001.py`, qui exige en retour
    l'ABSENCE de plafond, si bien que les deux gardes ne peuvent plus diverger.
    """
    audit = REQUIREMENTS_AUDIT.read_text(encoding="utf-8")
    for package in ("Pillow", "mariadb", "jsonschema"):
        spec = _requirement(audit, package)
        assert "<" in spec, f"{package} n'a plus de borne haute : {package}{spec}"


# ── Le veilleur lui-même ─────────────────────────────────────────────────────

def test_le_veilleur_signale_un_avis_ignore_devenu_corrigeable() -> None:
    from tools.check_ignored_vulns import IGNORED_VULNERABILITIES, find_fixed_ignored

    identifier = next(iter(IGNORED_VULNERABILITIES))
    dependencies = [
        {
            "name": "mariadb",
            "version": "1.1.14",
            "vulns": [{"id": identifier, "fix_versions": ["1.1.15"]}],
        }
    ]

    found = find_fixed_ignored(dependencies)

    assert found == [(identifier, "mariadb", "1.1.14", ["1.1.15"])]


def test_le_veilleur_se_tait_tant_qu_aucun_correctif_n_existe() -> None:
    from tools.check_ignored_vulns import IGNORED_VULNERABILITIES, find_fixed_ignored

    identifier = next(iter(IGNORED_VULNERABILITIES))
    dependencies = [
        {
            "name": "mariadb",
            "version": "1.1.14",
            "vulns": [{"id": identifier, "fix_versions": []}],
        }
    ]

    assert find_fixed_ignored(dependencies) == []


def test_le_veilleur_ignore_les_avis_non_exclus() -> None:
    """Ce n'est pas un second audit : il ne surveille que les exclusions."""
    from tools.check_ignored_vulns import find_fixed_ignored

    dependencies = [
        {
            "name": "autre",
            "version": "1.0",
            "vulns": [{"id": "PYSEC-0000-000", "fix_versions": ["2.0"]}],
        }
    ]

    assert find_fixed_ignored(dependencies) == []
