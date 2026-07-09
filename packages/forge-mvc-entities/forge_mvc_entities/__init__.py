# pyright: strict
"""forge-mvc-entities — moteur d'entites, opt-in (extrait du coeur, ADR-070).

Generation et modelisation d'entites et de relations : `make:entity`,
`make:relation` (`many_to_one` et `many_to_many`), normaliseur canonique,
validation, `build:model`, generation de migrations, `make:crud`, provisioning
`db:config` / `db:init` / `db:apply`, et le service pivot enrichi + `make:pivot-crud`
(herites de `forge-mvc-pivot`, absorbe par cet opt-in).

Cet opt-in depend du contrat `Dialect` expose par le coeur (`core.database`),
jamais d'un backend concret : il reste independant du SGBD. Il consomme aussi les
schemas d'entites/relations, qui restent des *contrats du coeur* (`cli.schemas`,
ADR-058), a l'image du contrat `Dialect`.

L'API du paquet est faite de ses sous-modules (un par commande : `make_entity`,
`make_relation`, `make_crud`, `model`, `entity_validate`, `entity_doc`,
`migrations`, `db_apply`, `db_init`, `db_config`, ...) et de leurs fonctions
publiques (`validation.validate_entity_definition`,
`relations.validate_relations_definition`, ...). On importe le sous-module voulu.
"""
from __future__ import annotations

__all__: list[str] = []

__version__ = "1.0.0rc2"
