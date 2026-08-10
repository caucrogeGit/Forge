"""Les tests d'intégration tiennent sous `-n` (TEST-DB-WORKER-ISOLATION-001).

La suite d'intégration partage **un serveur**. Lancée en parallèle, elle ne
tient que si deux garanties sont posées ensemble. Chacune seule laisse passer
la moitié des cas, et les deux ont été mesurées.

## 1. Une base par worker

`tables_temporaires` crée et jette des tables par leur **nom réel**, celui que
le code sous test emploie. Deux workers qui exercent deux paquets partageant une
table se détruisent mutuellement leurs données : `forge-mvc-settings` et le
relevé de portabilité emploient tous deux `app_settings`.

Mesuré sur la suite d'intégration MariaDB sous `-n 4`, avant correctif : **7 à
26 échecs sur 135, à chaque passage**. Ce défaut est arrivé avec
`TEST-PACKAGE-INTEGRATION-REAL-LAYER-001`, qui a remplacé la base jetable par
test par des tables dans une base commune.

## 2. Un fichier reste sur un worker

Plusieurs fichiers d'intégration sont des **scénarios** : une étape crée la
table, une autre la lit, une dernière la jette. La répartition par défaut de
pytest-xdist les éparpille, si bien que l'étape de lecture peut s'exécuter là où
la table n'a jamais été créée.

Mesuré sur les deux scénarios E2E MariaDB : **2 à 4 échecs sur 19** en
répartition par défaut, aucun en `loadfile`. Ce défaut-là **préexistait**,
vérifié en rejouant les fichiers d'avant le cycle.

## Pourquoi la CI ne voyait rien

Elle ne parallélise pas ses jobs d'intégration. Seul le développeur qui lance la
suite entière avec `-n` rencontrait ces échecs, et pouvait les prendre pour un
aléa. C'est la forme la plus coûteuse d'un défaut : celle qui apprend à ne plus
croire sa propre suite.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from forge_mvc_testing import real_db

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PYTEST_INI = PROJECT_ROOT / "pytest.ini"


def test_la_repartition_par_fichier_est_le_defaut() -> None:
    """`--dist loadfile` garde un scénario entier sur le même worker.

    Sans lui, un fichier dont les étapes se suivent est éparpillé, et la moitié
    de ses assertions cherche une table qu'un autre worker vient de jeter.
    """
    contenu = PYTEST_INI.read_text(encoding="utf-8")
    addopts = re.search(r"^addopts\s*=\s*(.+)$", contenu, re.MULTILINE)

    assert addopts is not None, "pytest.ini ne déclare plus d'addopts"
    assert "--dist loadfile" in addopts.group(1), (
        "pytest.ini a perdu `--dist loadfile` : les scénarios d'intégration "
        "redeviennent éparpillables entre workers."
    )


def test_le_greffon_du_drapeau_est_declare() -> None:
    """`--dist` vient de pytest-xdist : le déclarer, sinon la CI refuse de démarrer.

    Le drapeau a été posé dans `addopts` alors que `pytest-xdist` n'était
    installé que sur le poste de développement. La CI suit `requirements-dev.txt`,
    ne connaissait pas le greffon, et **les six jobs** ont échoué d'un coup sur
    « unrecognized arguments: --dist », avant même le premier test.

    Une validation locale ne pouvait pas le voir : le greffon y était présent.
    C'est la dérive d'environnement entre le poste et le contrat déclaré.
    """
    addopts = re.search(
        r"^addopts\s*=\s*(.+)$", PYTEST_INI.read_text(encoding="utf-8"), re.MULTILINE
    )
    assert addopts is not None

    if "--dist" not in addopts.group(1):
        return
    requirements = (PROJECT_ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
    assert "pytest-xdist" in requirements, (
        "`addopts` emploie `--dist`, drapeau de pytest-xdist, mais le greffon "
        "n'est pas déclaré dans requirements-dev.txt : la CI refusera de démarrer."
    )


def test_chaque_worker_a_sa_propre_base(monkeypatch: pytest.MonkeyPatch) -> None:
    """Le nom de base porte l'identifiant du worker, et lui seul le porte."""
    monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw3")
    assert real_db._nom_par_worker("forge_test") == "forge_test_gw3"


def test_hors_parallele_le_nom_ne_change_pas(monkeypatch: pytest.MonkeyPatch) -> None:
    """La CI ne parallélise pas : son nom de base doit rester intact.

    Un suffixe inconditionnel aurait changé la base sous les jobs
    d'intégration, qui la provisionnent par leur service.
    """
    monkeypatch.delenv("PYTEST_XDIST_WORKER", raising=False)
    assert real_db._nom_par_worker("forge_test") == "forge_test"


def test_la_creation_de_base_couvre_les_trois_moteurs() -> None:
    """`CREATE DATABASE` s'écrit différemment sur chacun, et aucun n'accepte de paramètre lié."""
    import inspect

    source = inspect.getsource(real_db._creer_base)

    assert "pg_database" in source, "PostgreSQL n'a pas de CREATE DATABASE IF NOT EXISTS"
    assert "DB_ID(" in source, "SQL Server passe par DB_ID"
    assert "IF NOT EXISTS" in source, "MariaDB accepte la forme conditionnelle"


def test_la_sonde_postgres_emploie_le_marqueur_de_forge() -> None:
    """`?` et non `%s`, car l'enveloppe Forge double tout `%` littéral.

    Écrit en `%s`, ce contrôle rendait « 0 marqueurs pour 1 paramètre » et
    faisait échouer les 98 cas PostgreSQL d'un coup. C'est le défaut même que
    `VIDEO-DML-PORTABLE-001` venait de corriger ailleurs, réintroduit dans le
    correctif de celui-ci.
    """
    import inspect

    source = inspect.getsource(real_db._creer_base)

    assert "datname = ?" in source
    assert "datname = %s" not in source


def test_aucun_test_ne_code_en_dur_le_nom_de_la_base() -> None:
    """Un littéral « forge_test » ignore la base du worker.

    `test_schema_diff_golden_001.py` interrogeait `information_schema` sur
    « forge_test » alors que ses tables vivaient dans `forge_test_gw2` : le
    diff rendait « table absente en base ».
    """
    coupables: list[str] = []
    for chemin in sorted((PROJECT_ROOT / "tests" / "db").rglob("*.py")):
        for numero, ligne in enumerate(
            chemin.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if "database=" in ligne and '"forge_test"' in ligne:
                coupables.append(f"{chemin.relative_to(PROJECT_ROOT)}:{numero}")
    assert not coupables, (
        "Ces tests visent une base codée en dur au lieu de celle du worker "
        "(`os.environ[\"DB_NAME\"]`) :\n  " + "\n  ".join(coupables)
    )
