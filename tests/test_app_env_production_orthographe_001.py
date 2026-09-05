"""ENV-APP-ENV-PRODUCTION-SPELLING-001 : `production` désigne la production.

`ENV-APP-ENV-NORMALISATION-001` avait fermé la variation de casse : `Prod`
désarmait les gardes, il ne le fait plus. Le même défaut subsistait à une
orthographe près. `is_prod("production")` rendait **faux**, alors que ce mot
s'écrit au moins aussi naturellement que son abréviation.

Ce que cela coûtait, mesuré avant correction : `fixtures:purge --run`
supprimait les données sans exiger `--force`, `fixtures:load --run` acceptait
de peupler la base, et le squelette servait ses pages d'erreur en mode
développement, pile d'exception comprise.

Le test précédent n'a pas vu ce trou parce qu'il énumérait des écritures de
`prod`, jamais le mot entier. Celui-ci ferme la famille, et fixe surtout ce
qui reste **hors** de la production : accepter tout inconnu rendrait le refus
si fréquent qu'on le désactiverait.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from core.app.env import PROD_SPELLINGS, is_prod, normalize_app_env

#: Écritures entières de la production, casse et espaces compris.
ECRITURES_PRODUCTION = [
    "production", "Production", "PRODUCTION", "  production  ", "\tproduction\n",
]

#: Environnements distincts, que leurs exploitants ne veulent pas voir
#: traiter comme la production.
ENVIRONNEMENTS_VOISINS = ["staging", "preprod", "pre-prod", "ci", "test", "sandbox"]


@pytest.mark.parametrize("valeur", ECRITURES_PRODUCTION)
def test_production_designe_la_production(valeur: str) -> None:
    assert is_prod(valeur), f"{valeur!r} devrait désigner la production"


@pytest.mark.parametrize("valeur", ENVIRONNEMENTS_VOISINS)
def test_un_environnement_voisin_n_est_pas_la_production(valeur: str) -> None:
    """La tolérance s'arrête aux deux mots qui ne veulent dire que cela."""
    assert not is_prod(valeur), f"{valeur!r} est un environnement distinct"


def test_la_liste_des_ecritures_reste_close() -> None:
    """Deux mots, et le test le dit pour qu'un ajout soit un choix conscient."""
    assert PROD_SPELLINGS == frozenset({"prod", "production"})


def test_production_n_est_pas_reecrit_en_prod() -> None:
    """La normalisation range la casse, elle ne renomme pas l'environnement.

    Ce que l'exploitant a écrit reste ce que les messages lui montrent.
    """
    assert normalize_app_env("Production") == "production"


class TestGardeDesFixtures:
    """Le trou se mesure là où il coûtait : la suppression de données."""

    @staticmethod
    def _projet_avec_fixtures() -> Path:
        racine = Path(tempfile.mkdtemp())
        (racine / "mvc" / "fixtures").mkdir(parents=True)
        (racine / "mvc" / "fixtures" / "eleves.sql").write_text(
            "INSERT INTO eleves (nom) VALUES ('Durand');\n", encoding="utf-8")
        return racine

    @pytest.mark.parametrize("env", ["prod", "production", "PRODUCTION"])
    def test_la_purge_refuse_sans_force(self, env: str) -> None:
        from forge_mvc_fixtures.cli.purge import purge_fixtures

        code = purge_fixtures(self._projet_avec_fixtures(), run=True, force=False, env=env)

        assert code == 2, f"APP_ENV={env} doit exiger --force"
