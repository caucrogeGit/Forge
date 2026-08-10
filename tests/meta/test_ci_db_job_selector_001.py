"""Chaque job d'intégration ne sélectionne que son serveur (CI-DB-JOB-SELECTOR-001).

Le job MariaDB employait `-m db`. Or un cas PostgreSQL ou SQL Server porte
**aussi** `db`, par une convention qui reste juste : c'est elle qui dit au garde
de collecte du `conftest.py` racine qu'un tel cas n'est pas exigé de ce job, et
qui permet au job sans base d'exclure les trois serveurs d'un seul terme.

Conséquence non voulue : le job MariaDB les collectait, puis leur fixture tentait
une connexion vers un serveur absent avant de les sauter. Mesuré, fixture
`real_pg_db` avec un hôte injoignable : **quinze secondes par cas**, contre deux
et demie quand l'hôte refuse, ce qui est le cas d'un runner. Le job payait ainsi
quatre minutes pour 196 cas qu'il ne pouvait pas exécuter, soit 312 sélectionnés
pour 116 exécutables.

Le correctif porte sur la **sélection**, pas sur les marqueurs. Toucher à la
convention aurait cassé le garde de collecte, et obligé le job sans base à
énumérer chaque backend, donc à en oublier un au prochain ajout.

Aucune couverture n'est perdue : 116 + 98 + 98 = 312.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
WORKFLOW = PROJECT_ROOT / ".github" / "workflows" / "tests.yml"

#: Sélection attendue pour chaque job d'intégration.
_SELECTION_ATTENDUE = {
    "real MariaDB": '-m "db and not db_pg and not db_mssql"',
    "real PostgreSQL": "-m db_pg",
    "real SQL Server": "-m db_mssql",
}


def _commandes_pytest() -> dict[str, str]:
    """Associe le libellé de chaque étape d'intégration à sa commande pytest."""
    texte = WORKFLOW.read_text(encoding="utf-8")
    trouvees: dict[str, str] = {}
    for libelle in _SELECTION_ATTENDUE:
        debut = texte.find(f"Run DB integration tests ({libelle})")
        assert debut != -1, f"étape introuvable dans le workflow : {libelle}"
        # L'étape court jusqu'à la suivante : `- name:` est le seul délimiteur
        # fiable, l'indentation étant uniforme à l'intérieur d'un bloc `run`.
        suivante = texte.find("- name:", debut + 1)
        bloc = texte[debut : suivante if suivante != -1 else len(texte)]
        commande = re.search(r"python -m pytest [^\n]*", bloc)
        assert commande is not None, f"aucune commande pytest dans l'étape {libelle}"
        trouvees[libelle] = commande.group(0)
    return trouvees


@pytest.mark.parametrize(("libelle", "selection"), sorted(_SELECTION_ATTENDUE.items()))
def test_le_job_ne_selectionne_que_son_serveur(libelle: str, selection: str) -> None:
    """Sans cela, le job monte des cas qu'il ne peut pas exécuter, et paye leur timeout."""
    commande = _commandes_pytest()[libelle]

    assert selection in commande, (
        f"le job « {libelle} » sélectionne « {commande} », attendu « {selection} ». "
        "Un job qui collecte les cas d'un autre backend paye une tentative de "
        "connexion par cas avant de le sauter."
    )


def test_le_job_mariadb_n_utilise_plus_le_selecteur_large() -> None:
    """`-m db` seul est précisément ce que ce ticket retire."""
    commande = _commandes_pytest()["real MariaDB"]

    assert not re.search(r"-m db(\s|$)", commande), (
        "le job MariaDB est revenu à `-m db`, qui collecte aussi les cas "
        "PostgreSQL et SQL Server (CI-DB-JOB-SELECTOR-001)"
    )


def test_les_tests_d_empaquetage_tournent_apres_la_construction() -> None:
    """Ils ne prouvent rien tant que `dist/` est vide (`CI-WHEEL-TESTS-NEVER-RAN-001`).

    Le job lançait la suite **avant** de construire les distributions, si bien
    que les contrôles de contenu de wheel se sautaient. Ils ne s'exécutaient
    donc nulle part : en local non plus, où un `dist/` résiduel les faisait
    passer contre une distribution périmée.

    Deux propriétés à tenir ensemble : l'étape existe, et elle vient **après**
    la construction.
    """
    texte = WORKFLOW.read_text(encoding="utf-8")

    etape = texte.find("Test packaging")
    build = texte.find("Build package")
    assert etape != -1, "l'étape de test d'empaquetage a disparu du workflow"
    assert build != -1
    assert build < etape, (
        "les tests d'empaquetage passent avant la construction : `dist/` sera "
        "vide et ils se sauteront."
    )
    assert 'FORGE_REQUIRE_DIST: "1"' in texte, (
        "sans ce drapeau, une distribution absente ferait sauter les tests au "
        "lieu de faire échouer le job."
    )


def test_le_job_sans_base_exclut_les_trois_serveurs_d_un_seul_terme() -> None:
    """C'est ce que la combinaison des marqueurs achète, et qu'il ne faut pas perdre.

    Si `db_pg` cessait d'impliquer `db`, ce job devrait énumérer chaque backend,
    et en oublierait un au prochain ajout.
    """
    texte = WORKFLOW.read_text(encoding="utf-8")

    assert 'python -m pytest -m "not db"' in texte
