"""CLI-HELP-SUMMARY-COHERENCE-001 : le sommaire disait alias, le détail disait surensemble.

`forge --help` annonçait `media:init` comme un « alias de upload:init ». C'est
faux, et la conséquence n'est pas cosmétique : `init_media_storage()` **appelle**
`init_upload_storage()` puis crée en plus les sous-dossiers de variantes
d'image. Un lecteur qui les croit équivalents lance `upload:init`, n'obtient pas
`storage/uploads/images/thumbnail` ni `medium`, et le découvre au premier
traitement d'image.

L'aide **détaillée** de la même commande disait pourtant juste, « surensemble de
upload:init pour le sous-système média ». Deux descriptions de la même commande,
contradictoires, dans le même fichier.

Le cas a été trouvé en étendant le balayage documentaire à `cli/*/docs`
(ADR-043), qui manquait au contrôle d'adéquation alors qu'il porte 60 blocs de
commandes qu'un lecteur tape.

Ce garde ne juge pas la prose : il vérifie qu'une description courte n'annonce
pas un **alias** que l'aide longue ne confirme pas. Une sur quatre-vingts le
faisait.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.meta


def _aides() -> "tuple[dict[str, str], dict[str, str]]":
    from cli._support.help_dispatch import HELP_DESCRIPTIONS, HELP_TEXTS_RICH

    return HELP_DESCRIPTIONS, HELP_TEXTS_RICH


def test_aucune_description_courte_n_annonce_un_alias_non_confirme() -> None:
    """Annoncer un alias qui n'en est pas fait sauter une étape au lecteur."""
    courtes, longues = _aides()

    fautives = [
        commande
        for commande, texte in courtes.items()
        if "alias" in texte.lower()
        and "alias" not in longues.get(commande, "").lower()
    ]

    assert not fautives, (
        "descriptions courtes annonçant un alias que l'aide longue ne confirme "
        f"pas : {', '.join(sorted(fautives))}"
    )


def test_media_init_est_decrit_comme_un_surensemble() -> None:
    """Le cas mesuré : `media:init` fait tout ce que fait `upload:init`, plus."""
    courtes, longues = _aides()

    assert "alias" not in courtes["media:init"].lower()
    assert "surensemble" in longues["media:init"].lower()


def test_media_init_fait_bien_davantage_que_upload_init() -> None:
    """La preuve par le code : l'une appelle l'autre puis ajoute des dossiers."""
    import inspect

    from cli.assets import uploads

    source = inspect.getsource(uploads.init_media_storage)

    assert "init_upload_storage(" in source
    assert "IMAGE_VARIANT_SUBDIRS" in source


def test_les_deux_tables_d_aide_couvrent_les_memes_commandes() -> None:
    """Une commande décrite d'un côté seulement échapperait au contrôle."""
    courtes, longues = _aides()

    assert set(courtes) == set(longues)
