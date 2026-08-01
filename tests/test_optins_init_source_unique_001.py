"""OPTINS-INIT-SOURCE-UNIQUE-001 : `optins/__init__.py` vivait en double.

Le squelette en livrait une version, `cli/optins/enable.py` en portait une
autre dans une constante. Les deux disaient la même chose, écrite
différemment, 319 caractères contre 349, et elles avaient dérivé.

La conséquence se voyait au premier geste, sur un projet neuf :

    forge new MonProjet          # pose la version du squelette
    forge opt-in:enable audio --apply
    [WARN] optins/__init__.py existe déjà avec un contenu différent.
           Aucune modification. Vérifie le fichier manuellement.

La commande sortait en erreur, et les trois opt-ins routiers, `audio`, `video`
et `iot`, étaient donc inutilisables sur un projet neuf. Constaté en jouant
leurs chapitres « Mise en service », qui échouaient tous les trois au même
endroit.

Le refus d'écraser était **juste** : Forge ne réécrit pas un fichier
applicatif (principe 9). C'est la duplication qui était fautive, exactement
comme la primitive CSV recopiée dans chaque contrôleur généré : une règle
écrite deux fois finit écrite de deux façons.

Une source, un lecteur (principe 11).
"""
from __future__ import annotations

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LIVRE = PROJECT_ROOT / "skeleton" / "data" / "optins" / "__init__.py"


def test_la_commande_lit_le_fichier_du_squelette() -> None:
    """Le cas mesuré : deux contenus divergents pour le même chemin."""
    from cli.optins.enable import OPTINS_INIT

    assert OPTINS_INIT == LIVRE.read_text(encoding="utf-8")


def test_le_contenu_n_est_plus_recopie_dans_la_commande() -> None:
    """Test d'absence : c'est la constante littérale qui avait dérivé."""
    source = (PROJECT_ROOT / "cli" / "optins" / "enable.py").read_text(
        encoding="utf-8")

    assert "OPTINS_INIT = '''" not in source
    assert "_optins_init_du_squelette" in source


def test_le_fichier_est_embarque_dans_la_distribution() -> None:
    """Lu à l'exécution : absent du paquet, la commande ne démarrerait plus."""
    import skeleton

    racine = Path(skeleton.__file__ or "").resolve().parent

    assert (racine / "data" / "optins" / "__init__.py").is_file()


def test_le_squelette_livre_bien_ce_fichier() -> None:
    """S'il cessait de le livrer, `forge new` produirait un `optins/` sans
    `__init__.py`, et la lecture ci-dessus tomberait."""
    assert LIVRE.is_file()
    assert LIVRE.read_text(encoding="utf-8").lstrip().startswith('"""')


# ── Les trois opt-ins que le défaut bloquait ─────────────────────────────────

@pytest.mark.parametrize("optin", ["audio", "video", "iot"])
def test_les_optins_routiers_partagent_ce_fichier(optin: str) -> None:
    """Ce sont les seuls à recevoir la couche `optins/`, donc les seuls
    qu'un conflit sur ce fichier rendait inutilisables."""
    from cli.optins.enable import SUPPORTED_OPTINS

    assert optin in SUPPORTED_OPTINS


def test_le_fichier_partage_est_traite_comme_partage() -> None:
    """Il ne doit pas être rangé parmi les fichiers propres à un opt-in :
    trois opt-ins l'écriraient alors chacun de leur côté."""
    source = (PROJECT_ROOT / "cli" / "optins" / "enable.py").read_text(
        encoding="utf-8")
    partages = source[source.index("_SHARED_FILES"):source.index("REGISTRY_REL")]

    assert '"optins/__init__.py"' in partages


# ── Le code généré doit passer la porte qualité que Forge installe ───────────

@pytest.mark.parametrize("optin", ["iot", "video", "audio"])
def test_le_cablage_genere_annote_son_parametre(optin: str) -> None:
    """Le squelette livre un pyright strict : un paramètre non annoté faisait
    échouer `make typage` sur le code que Forge venait d'écrire.

    Second défaut de la même famille que `pytest.ini`, révélé en débloquant le
    premier : Forge produisait du code refusé par la porte qualité qu'il
    installe lui-même (OPTINS-GENERATED-TYPING-001).
    """
    from cli.optins import enable

    gabarit = getattr(enable, f"_{optin.upper()}_ROUTES")

    assert "def register(router: Router) -> None:" in gabarit
    assert "if TYPE_CHECKING:" in gabarit
    assert "from core.http.router import Router" in gabarit


def test_aucun_cablage_genere_ne_laisse_un_parametre_nu() -> None:
    """Un nouveau gabarit copié sur un ancien reprendrait le défaut."""
    source = (PROJECT_ROOT / "cli" / "optins" / "enable.py").read_text(
        encoding="utf-8")

    assert "def register(router) -> None:" not in source


def test_le_squelette_annote_deja_ainsi() -> None:
    """La forme retenue n'est pas inventée : c'est celle que `optins/registry.py`
    du squelette emploie déjà. Deux générateurs de la même couche doivent
    écrire la même chose."""
    registry = (PROJECT_ROOT / "skeleton" / "data" / "optins"
                / "registry.py").read_text(encoding="utf-8")

    assert "if TYPE_CHECKING:" in registry
    assert "from core.http.router import Router" in registry
