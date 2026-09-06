# Avancé 4 : Les métadonnées et le découpage

Objectif : lire le titre d'un fichier audio, et n'en garder qu'un extrait.

## Les tags, lus et nettoyés

```python
from forge_mvc_audio import parse_tags, clean_tag_value

tags = parse_tags(sortie_de_ffprobe)
```

`AudioTags` porte les champs usuels : titre, artiste, album, durée.

!!! danger "Un tag est une donnée d'utilisateur"
    Il vient du fichier déposé, et rien n'oblige qui l'a fabriqué à y mettre du texte raisonnable.

    `clean_tag_value` retire ce qui n'a rien à faire dans une page : caractères de contrôle, longueurs déraisonnables. Afficher un tag brut revient à afficher ce qu'un inconnu a écrit.

## Le découpage

```python
from forge_mvc_audio import build_trim_command, parse_timecode

commande = build_trim_command(
    "ffmpeg", entree, sortie,
    start=parse_timecode("00:01:30"),
    end=parse_timecode("00:02:00"),
)
```

`parse_timecode` accepte `SS`, `MM:SS` et `HH:MM:SS`, avec décimales.

!!! danger "La commande est une liste, jamais une chaîne"
    `build_trim_command` rend une liste d'arguments, passée telle quelle au processus.

    Un nom de fichier contenant `; rm -rf /` n'est donc qu'un nom de fichier : il n'y a pas de shell pour l'interpréter. Construire la commande par concaténation de texte serait l'inverse exact.

!!! warning "Un instant illisible ou négatif est refusé"
    `parse_timecode` lève plutôt que de retomber sur zéro.

    Retomber donnerait un extrait qui commence au début, et l'utilisateur croirait sa saisie prise en compte.

!!! info "Le découpage par défaut ne réencode pas"
    Il copie le flux, ce qui est quasi instantané et sans perte, mais découpe sur les images clés.

    `reencode=True` donne un découpage exact, au prix du temps de calcul.

## À retenir

- Un tag vient du fichier déposé : nettoyez-le avant de l'afficher.
- La commande est une liste d'arguments, sans shell pour l'interpréter.
- La copie de flux est rapide et approximative ; le réencodage est exact et lent.

## Étape suivante

[Bilan du niveau avancé](bilan.md)
