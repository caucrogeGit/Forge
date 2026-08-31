"""ENV-APP-ENV-NORMALISATION-001 : la casse de `APP_ENV` ne désarme plus les gardes.

Deux gardes de sécurité comparaient `APP_ENV` à `"prod"` sans normaliser. Avec
`APP_ENV=Prod`, la comparaison était fausse et la garde ne se déclenchait pas,
si bien que l'API IoT s'enregistrait sans jeton en production et que
`fixtures:load --run` acceptait de peupler la base de production.

Les tests de ces deux gardes existaient déjà, et passaient : ils n'exerçaient
qu'une seule écriture, `"prod"` en minuscules. Ces tests-ci exercent le
comportement sur les écritures qu'un exploitant peut réellement poser.
"""
from __future__ import annotations

import pytest

from core.app.env import is_prod, normalize_app_env, read_app_env

#: Écritures de la production qu'un exploitant peut poser dans `env/prod`.
VARIANTES_PROD = ["prod", "Prod", "PROD", " prod", "prod ", "  Prod  ", "pRoD"]

#: Écritures qui ne désignent pas la production.
VARIANTES_HORS_PROD = [None, "", "   ", "dev", "Dev", "staging"]


@pytest.mark.parametrize("valeur", VARIANTES_PROD)
def test_variantes_de_casse_designent_la_production(valeur: str) -> None:
    """Toute écriture de « prod » est reconnue comme la production."""
    assert is_prod(valeur), f"{valeur!r} devrait désigner la production"
    assert normalize_app_env(valeur) == "prod"


@pytest.mark.parametrize("valeur", VARIANTES_HORS_PROD)
def test_ce_qui_n_est_pas_la_production_ne_l_est_pas(valeur: "str | None") -> None:
    """Une valeur absente ou autre ne bascule pas en production."""
    assert not is_prod(valeur)


def test_environnement_absent_vaut_developpement() -> None:
    """Sans `APP_ENV`, on est en développement, jamais en production."""
    assert read_app_env({}) == "dev"


@pytest.mark.parametrize("valeur", VARIANTES_PROD)
def test_fixtures_refuse_le_chargement_en_production(valeur: str, tmp_path) -> None:
    """`fixtures:load --run` refuse la production sans `--force`, quelle que soit la casse."""
    pytest.importorskip("forge_mvc_fixtures")
    from forge_mvc_fixtures.cli.load import load_fixtures

    dossier = tmp_path / "mvc" / "fixtures"
    dossier.mkdir(parents=True)
    (dossier / "01_villes.sql").write_text(
        "INSERT INTO villes (nom) VALUES ('Nantes');\n", encoding="utf-8"
    )

    code = load_fixtures(tmp_path, run=True, force=False, env=valeur)

    assert code == 2, (
        f"APP_ENV={valeur!r} : le chargement en production devait être refusé "
        f"(code 2), obtenu {code}"
    )


@pytest.mark.parametrize("valeur", VARIANTES_PROD)
def test_api_iot_ouverte_refusee_en_production(valeur: str, monkeypatch) -> None:
    """L'API IoT sans jeton refuse de s'enregistrer en production (SEC-IOT-TOKEN-PROD-001)."""
    pytest.importorskip("forge_mvc_iot")
    from core.http.router import Router
    from forge_mvc_iot import http
    from forge_mvc_iot.config import load_iot_config

    monkeypatch.setattr(
        http, "_forge_get", lambda key: valeur if key == "app_env" else None
    )

    with pytest.raises(RuntimeError, match="production"):
        http.register_iot_routes(Router(), config=load_iot_config(env={}))


@pytest.mark.parametrize("valeur", ["dev", "Dev", " DEV "])
def test_api_iot_ouverte_reste_permise_hors_production(valeur: str, monkeypatch) -> None:
    """Le mode ouvert reste autorisé hors production, la correction ne l'a pas fermé."""
    pytest.importorskip("forge_mvc_iot")
    from core.http.router import Router
    from forge_mvc_iot import http
    from forge_mvc_iot.config import load_iot_config

    monkeypatch.setattr(
        http, "_forge_get", lambda key: valeur if key == "app_env" else None
    )

    http.register_iot_routes(Router(), config=load_iot_config(env={}))
