# Avancé 4 : Les jetons et leur portée

Objectif : qu'un capteur ne puisse écrire que ses propres mesures.

## Un jeton par appareil, jamais un jeton pour tous

```python
from forge_mvc_iot import generate_token, hash_token

jeton = generate_token()          # à remettre à l'appareil, une seule fois
empreinte = hash_token(jeton)     # à stocker en base
```

La base ne garde que l'empreinte.
Une fuite de la table ne donne donc aucun jeton utilisable, et un jeton perdu ne se retrouve pas : il se remplace.

!!! danger "Le jeton n'est montré qu'une fois"
    C'est le prix du stockage par empreinte, et c'est le bon prix.

    Un jeton relisable en base est un jeton qu'une sauvegarde, un journal ou un écran d'administration peut divulguer.

## La portée limite ce qu'un jeton peut faire

```python
from forge_mvc_iot import IotScope, GLOBAL_SCOPE

portee = IotScope(device_id="capteur-salle-201")
```

Un jeton de portée `capteur-salle-201` ne peut pas écrire au nom d'un autre appareil.

!!! warning "La portée globale n'est pas un raccourci de développement"
    `GLOBAL_SCOPE` autorise à écrire au nom de n'importe quel appareil.

    Elle a des usages, une passerelle qui relaie plusieurs capteurs par exemple, et un seul jeton global qui fuit permet d'injecter des mesures pour tout le parc.

!!! info "La lecture se contrôle séparément"
    Écrire une mesure et lire les agrégats sont deux actions distinctes.

    Un capteur écrit et ne lit pas ; un écran lit et n'écrit pas. `is_read_allowed` porte cette seconde question, et l'application y branche sa propre règle.

## À retenir

- La base garde une empreinte, jamais le jeton.
- Une portée par appareil borne les dégâts d'une fuite.
- Lecture et écriture sont deux droits séparés.

## Étape suivante

[Bilan du niveau avancé](bilan.md)
