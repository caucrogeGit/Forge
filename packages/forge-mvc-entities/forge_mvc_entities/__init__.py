# pyright: strict
"""forge-mvc-entities — moteur d'entites, opt-in (extrait du coeur, ADR-070).

Generation et modelisation d'entites et de relations : `make:entity`,
`make:relation` (`many_to_one` et `many_to_many`), normaliseur canonique,
validation, `build:model`, generation de migrations, `make:crud`, provisioning
`db:config` / `db:init` / `db:apply`, et le service pivot enrichi + `make:pivot-crud`
(herites de `forge-mvc-pivot`, absorbe par cet opt-in).

Cet opt-in depend du contrat `Dialect` expose par le coeur (`core.database`),
jamais d'un backend concret : il reste independant du SGBD.

Le scaffold (ADR-070, phase 1) n'expose pas encore d'API : les modules du moteur
d'entites y sont deplaces dans les phases suivantes.
"""
from __future__ import annotations

__all__: list[str] = []

__version__ = "1.0.0rc2"
