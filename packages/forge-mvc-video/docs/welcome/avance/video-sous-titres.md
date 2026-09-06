# Avancé 4 : Les sous-titres

Objectif : joindre une piste de sous-titres à une vidéo, sans ouvrir une porte.

## Une piste, une langue, un fichier WebVTT

```python
from forge_mvc_video import SubtitleTrack, normalize_lang, validate_vtt

validate_vtt(contenu)
piste = SubtitleTrack(lang=normalize_lang("fr-FR"), path=chemin)
```

Le lecteur HTML les rend par un élément `<track>`, et le navigateur fait le reste.

!!! danger "L'étiquette de langue devient un nom de fichier"
    C'est pourquoi elle est normalisée et validée : `../../etc` est refusé, et non transformé.

    Une langue non contrôlée serait le vecteur exact d'une traversée de chemin, sur une valeur qui a l'air inoffensive.

!!! warning "Le fichier est vérifié, pas seulement son extension"
    `validate_vtt` refuse ce qui ne commence pas par la signature `WEBVTT`.

    Un `.vtt` qui n'en est pas serait servi tel quel au navigateur, et un fichier arbitraire servi depuis votre domaine n'est jamais une bonne idée.

!!! info "La casse et le tiret sont normalisés"
    `fr-FR`, `FR` et `fr` désignent la même piste.

    Sans cela, deux pistes de la même langue coexisteraient, et le navigateur en choisirait une au hasard.

## À retenir

- La langue est validée parce qu'elle devient un chemin.
- Le contenu est vérifié par sa signature, pas par son extension.
- Les variantes de casse d'une même langue se rejoignent.

## Étape suivante

[Suivant : les quotas vidéo](video-quotas.md)
